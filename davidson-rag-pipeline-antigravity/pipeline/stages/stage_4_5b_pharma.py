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

    ds = sum(len(re.findall(p, repaired, re.I)) for p in DOSING_PATTERNS)
    dc = sum(len(re.findall(p, chunks, re.I)) for p in DOSING_PATTERNS)
    ts = sum(len(re.findall(p, repaired, re.I)) for p in THRESHOLD_PATTERNS)
    tc = sum(len(re.findall(p, chunks, re.I)) for p in THRESHOLD_PATTERNS)
    drug_n = len(re.findall(r"semantic_type:\s*drug_info", chunks))
    total_l2 = max(len(re.findall(r"chunk_level:\s*2", chunks)), 1)

    verdict = "CLEARED"
    if ds > 0 and dc < ds * 0.9:
        verdict = "WARN - dosing dropped"
    if ts > 0 and tc < ts * 0.9:
        verdict += (" | " if "WARN" in verdict else "") + "WARN - thresholds dropped"

    log_path = os.path.join(out_dir, f"{prefix}_FlagCoverage.md")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"# Stage 4.5b Flag Coverage — {prefix}\n")
        f.write(f"Dosing    source:{ds} chunks:{dc} {'OK' if dc >= ds * 0.9 else 'LOW'}\n")
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
        "threshold_source": ts,
        "threshold_chunks": tc,
        "drug_info_chunks": drug_n,
        "total_l2": total_l2,
        "verdict": verdict,
    }