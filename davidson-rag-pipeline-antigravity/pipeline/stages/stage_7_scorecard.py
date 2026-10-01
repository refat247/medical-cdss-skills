"""Stage 7 — Quality Scorecard Module (v2.13.0, Advisory).

Aggregates multi-dimensional quality scores from stage logs and computes end-to-end
dosing and threshold preservation ratios against the final RAG_Optimised.md.
"""
import io
import json
import os
import re
import sys
from typing import Dict, Optional, Tuple

from pipeline.checkpoint_utils import (
    attach_json_provenance,
    format_markdown_provenance_header,
    load_checkpoint,
    mark_stage_complete,
    should_run_stage,
)


DOSING_PATTERNS = [
    r"\b\d+\s*(?:mg|mcg|g|mL|units?|IU)\b",
    r"\b(?:once|twice|three times)\s+(?:daily|weekly)",
    r"\b(?:loading|maintenance)\s+dose\b",
    r"\b\d+(?:\.\d+)?\s*(?:mg/kg)\b",
]

THRESHOLD_PATTERNS = [
    r"\b\d+(?:\.\d+)?%\b",
    r"\b(?:eGFR|CrCl)\s*[<>]\s*\d+",
    r"\bnumber needed to treat\b",
    r"\bNNT\b",
    r"\b(?:sensitivity|specificity)\s*(?:of\s*)?\d+",
]


def run_stage_7(rep_path: str, rag_path: str, out_dir: str, prefix: str) -> dict:
    """Computes composite quality scorecard across all dimensions."""
    checkpoint, checkpoint_path = load_checkpoint(out_dir, prefix)
    if not should_run_stage(checkpoint, "7"):
        return {"status": "skipped", "reason": "already complete"}

    def read_or_blank(path):
        return open(path, encoding="utf-8").read() if os.path.exists(path) else ""

    repaired = open(rep_path, encoding="utf-8").read()
    final = open(rag_path, encoding="utf-8").read()

    # Value-aware: a token only counts as retained if the SAME normalised value survives (multiset
    # intersection). The old min(hits_final/hits_source, 1.0) scored a 10x dose error as 1.000.
    from pipeline.stages.stage_4_5b_pharma import DOSING_PATTERNS as _D, THRESHOLD_PATTERNS as _T, _tokens

    def retained(patterns, src, dst):
        s, _ = _tokens(src, patterns)
        d, _ = _tokens(dst, patterns)
        return sum((s & d).values()), sum(s.values())

    dc, ds = retained(_D, repaired, final)
    tc, ts = retained(_T, repaired, final)

    scores = {}

    if ds > 0:
        scores["dosing_preservation"] = (min(dc / ds, 1.0), f"{dc}/{ds} source hits retained")
    else:
        scores["dosing_preservation"] = (None, "N/A — no dosing content in source")

    if ts > 0:
        scores["threshold_preservation"] = (min(tc / ts, 1.0), f"{tc}/{ts} source hits retained")
    else:
        scores["threshold_preservation"] = (None, "N/A — no threshold content in source")

    spot = read_or_blank(os.path.join(out_dir, f"{prefix}_SpotCheck.md"))
    m = re.search(r"Passed:\s*(\d+)\s*\|\s*Failed:\s*(\d+)", spot)
    if m:
        p, f = int(m.group(1)), int(m.group(2))
        scores["verbatim_accuracy"] = (p / (p + f) if (p + f) else None, f"{p}/{p+f} L2 chunks passed Stage 4.5")
    else:
        scores["verbatim_accuracy"] = (None, "N/A — SpotCheck.md not found or unparsed")

    gaps = read_or_blank(os.path.join(out_dir, f"{prefix}_L1L2_CoverageGaps.md"))
    m = re.search(r"L1 chunks checked:\s*(\d+)", gaps)
    n_gap_rows = len(re.findall(r"^\|\s*L1-", gaps, re.MULTILINE))
    if m:
        checked = int(m.group(1))
        scores["coverage_completeness"] = (
            1 - (n_gap_rows / checked) if checked else None,
            f"{n_gap_rows}/{checked} L1 sections had a coverage gap (Stage 4.5c)",
        )
    else:
        scores["coverage_completeness"] = (None, "N/A — L1L2_CoverageGaps.md not found (Stage 4.5c did not run)")

    valid_vals = [val for val, _ in scores.values() if val is not None]
    overall_score = round(sum(valid_vals) / len(valid_vals), 3) if valid_vals else None

    prov_hdr = format_markdown_provenance_header(rag_path, stage_name="7")
    md_lines = [
        prov_hdr.rstrip(),
        "",
        f"# Quality Scorecard — {prefix}\n",
        f"**Overall Quality Score**: `{overall_score if overall_score is not None else 'N/A'}`\n",
        "| Dimension | Score | Detail |",
        "|---|---|---|",
    ]
    for dim, (val, detail) in scores.items():
        score_str = f"{val:.3f}" if val is not None else "N/A"
        md_lines.append(f"| {dim} | `{score_str}` | {detail} |")

    md_path = os.path.join(out_dir, f"{prefix}_QualityScorecard.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    json_path = os.path.join(out_dir, f"{prefix}_QualityScorecard.json")
    json_data = {
        "chapter": prefix,
        "overall_score": overall_score,
        "dimensions": {dim: {"score": val, "detail": detail} for dim, (val, detail) in scores.items()},
    }
    attach_json_provenance(json_data, rag_path, stage_name="7")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)


    mark_stage_complete(
        checkpoint,
        checkpoint_path,
        "7",
        output_file=os.path.basename(md_path),
        overall_score=overall_score,
    )
    return json_data