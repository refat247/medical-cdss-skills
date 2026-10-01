"""Stage 4.5b — Clinical Flag Coverage Module (v2.13.0).

Scans pharmacology-heavy chapters for dosing and threshold retention.
"""
import io
import os
import re
import sys

from pipeline.checkpoint_utils import (
    load_checkpoint,
    mark_stage_complete,
    should_run_stage,
)

# Same unit grammar and token normalisation as Stage 4.5d, so 4.5b and 4.5d cannot disagree on what a
# "dose" is (the old patterns missed ug/mcg ranges, mg/kg/day, '1-2 g', and counted L1+L2 copies twice).
from collections import Counter

from pipeline.stages.stage_4_5d_clinical_fidelity import DOSE_PATTERNS, UNIT_PATTERNS, _norm_token

DOSING_PATTERNS = DOSE_PATTERNS + UNIT_PATTERNS
THRESHOLD_PATTERNS = [
    r"\b(?:eGFR|CrCl|GFR|creatinine clearance)\s*(?:[<>\u2264\u2265]=?|below|above|less than|greater than)\s*\d+",
    r"\bnumber needed to treat\b",
    r"\bNNT\b",
    r"\b(?:sensitivity|specificity)\s*(?:of\s*)?\d+",
]


def _l2_bodies(chunks_text):
    """Concatenate only level-2 chunk text: the chunks file also holds L1 section copies of the same text,
    which used to double-count every dose and hide a 50% loss."""
    parts = re.split(r"(?m)^---\nchunk_id:", chunks_text)
    out = []
    for part in parts[1:]:
        block = "---\nchunk_id:" + part
        if re.search(r"(?m)^chunk_level:\s*2\b", block):
            out.append(block)
    return "\n".join(out)


def _tokens(text, patterns):
    c, shown = Counter(), {}
    for p in patterns:
        for m in re.finditer(p, text, re.I):
            k = _norm_token(m.group(0))
            c[k] += 1
            shown.setdefault(k, m.group(0).strip())
    return c, shown


def run_stage_4_5b(rep_path: str, chunk_path: str, out_dir: str, prefix: str, is_active: bool = True) -> dict:
    """Runs pharma dosing & threshold scan or skips if not active."""
    checkpoint, checkpoint_path = load_checkpoint(out_dir, prefix)
    if not should_run_stage(checkpoint, "4.5b"):
        return {"status": "skipped", "reason": "already complete"}

    if not is_active:
        mark_stage_complete(
            checkpoint,
            checkpoint_path,
            "4.5b",
            output_file=None,
            status_note="SKIPPED - STAGE_45B_ACTIVE was False",
        )
        return {"status": "skipped", "reason": "STAGE_45B_ACTIVE was False"}

    repaired = open(rep_path, encoding="utf-8").read()
    chunks = open(chunk_path, encoding="utf-8").read()

    l2 = _l2_bodies(chunks) or chunks   # fall back to the whole file only if no level markers exist
    src_d, src_d_shown = _tokens(repaired, DOSING_PATTERNS)
    chk_d, chk_d_shown = _tokens(l2, DOSING_PATTERNS)
    src_t, _ = _tokens(repaired, THRESHOLD_PATTERNS)
    chk_t, _ = _tokens(l2, THRESHOLD_PATTERNS)
    ds, ts = sum(src_d.values()), sum(src_t.values())
    # matched = multiset intersection, i.e. the SAME value survived (not merely "some number of hits")
    dc, tc = sum((src_d & chk_d).values()), sum((src_t & chk_t).values())
    dose_changed = sorted(chk_d_shown[k] for k in chk_d if k not in src_d)   # present in chunks, absent in source
    dose_lost = sorted(src_d_shown[k] for k in src_d if chk_d.get(k, 0) < src_d[k])
    drug_n = len(re.findall(r"semantic_type:\s*drug_info", chunks))
    total_l2 = max(len(re.findall(r"chunk_level:\s*2", chunks)), 1)

    warns = []
    if ds > 0 and dc < ds * 0.9:
        warns.append("WARN - dosing dropped")
    if dose_changed:
        warns.append(f"WARN - dose values changed or added ({len(dose_changed)}: {', '.join(dose_changed[:5])})")
    if ts > 0 and tc < ts * 0.9:
        warns.append("WARN - thresholds dropped")
    verdict = " | ".join(warns) if warns else "CLEARED"

    log_path = os.path.join(out_dir, f"{prefix}_FlagCoverage.md")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"# Stage 4.5b Flag Coverage — {prefix}\n")
        f.write(f"Dosing    source:{ds} matched-in-L2:{dc} {'OK' if dc >= ds * 0.9 else 'LOW'}\n")
        if dose_lost:
            f.write(f"  lost from L2: {', '.join(dose_lost[:20])}\n")
        if dose_changed:
            f.write(f"  not in source (changed/added): {', '.join(dose_changed[:20])}\n")
        f.write(f"Threshold source:{ts} chunks:{tc} {'OK' if tc >= ts * 0.9 else 'LOW'}\n")
        f.write(f"drug_info chunks: {drug_n}/{total_l2} ({drug_n / total_l2 * 100:.0f}%)\n")
        f.write(f"VERDICT: {verdict}\n")

    mark_stage_complete(
        checkpoint,
        checkpoint_path,
        "4.5b",
        output_file=os.path.basename(log_path),
        verdict=verdict,
    )
    return {
        "dosing_source": ds,
        "dosing_chunks": dc,
        "dose_values_changed": dose_changed,
        "threshold_source": ts,
        "threshold_chunks": tc,
        "drug_info_chunks": drug_n,
        "total_l2": total_l2,
        "verdict": verdict,
    }