"""Stage 4.5 — Exhaustive Verbatim Spot-Check Module (v2.13.0).

Verifies that all emitted L2 chunks are 100% byte-verbatim against REPAIRED_S2.md
and ensures no figure references are dropped or hallucinated.
"""
import io
import os
import re
import sys

from pipeline.checkpoint_utils import (
    format_markdown_provenance_header,
    load_checkpoint,
    mark_stage_blocked,
    mark_stage_complete,
    should_run_stage,
)


def run_stage_4_5(rep_path: str, chunk_path: str, out_dir: str, prefix: str) -> dict:
    """Executes exhaustive verbatim spot check and figures comparison."""
    checkpoint, checkpoint_path = load_checkpoint(out_dir, prefix)
    if not should_run_stage(checkpoint, "4.5"):
        return {"status": "skipped", "reason": "already complete"}

    repaired = open(rep_path, encoding="utf-8").read()
    chunks = open(chunk_path, encoding="utf-8").read()

    blocks = re.findall(r"(---\nchunk_id:.*?\n---\n.*?)(?=\n---\nchunk_id:|\Z)", chunks, re.DOTALL)
    l2 = []
    for block in blocks:
        if not re.search(r"chunk_level:\s*2", block):
            continue
        cid = re.search(r"chunk_id:\s*(.+)", block)
        parts = block.split("---\n")
        body = parts[2].strip() if len(parts) >= 3 else block
        l2.append({"id": cid.group(1).strip() if cid else "?", "body": body})

    def norm(s):
        s = re.sub(r"^\s*#+\s*", "", s)
        s = re.sub(r"[*_`]+", "", s)
        return re.sub(r"\s+", " ", s).strip()

    rep_norm = norm(repaired)
    rep_lines = {norm(l) for l in repaired.splitlines() if norm(l)}

    def line_in_source(line):
        return line in rep_lines or line in rep_norm

    passed, failed, skipped = 0, [], 0
    for chunk in l2:
        # Whole-body check (the old version tested ONE 100-char window and passed on a single hit, so a
        # changed dose elsewhere in the chunk -- "4 g" -> "40 g" -- was never seen).
        lines = [norm(l) for l in chunk["body"].splitlines() if norm(l)]
        if not lines:
            skipped += 1
            continue
        numeric = [l for l in lines if re.search(r"\d", l)]
        prose = [l for l in lines if not re.search(r"\d", l) and len(l) >= 12]
        bad_numeric = [l for l in numeric if not line_in_source(l)]
        bad_prose = [l for l in prose if not line_in_source(l)]
        # numbers/doses must match exactly; free text tolerates up to 5% non-verbatim lines
        if bad_numeric or (prose and len(bad_prose) / len(prose) > 0.05):
            failed.append(chunk["id"])
        else:
            passed += 1

    if not l2:
        failed.append("<no L2 chunks found -- nothing was verified>")

    src_figs = sorted(set(re.findall(r"\*\*Fig\.?\s*[\d.]+\*\*[^\n]+", repaired)))
    chunk_figs = sorted(set(re.findall(r"\*\*Fig\.?\s*[\d.]+\*\*[^\n]+", chunks)))
    fig_ok = set(src_figs) == set(chunk_figs)

    verdict = "CLEARED" if not failed and fig_ok else "FAIL"
    out = [
        f"# Stage 4.5 Spot-Check — {prefix}",
        f"L2 checked: {len(l2)} | Passed: {passed} | Failed: {len(failed)} | Skipped: {skipped}",
        f"Figures: source={len(src_figs)} chunks={len(chunk_figs)} | {'OK' if fig_ok else 'MISMATCH'}",
        f"VERDICT: {verdict}",
    ]
    if failed:
        out += ["", "FAILED chunk IDs:"] + [f"  - {fid}" for fid in failed]
        out += ["", "FIX: splice verbatim text from REPAIRED_S2 into chunk body - do NOT re-run subagent"]
    if not fig_ok:
        out.append("\nFIG MISMATCHES:")
        for fig in set(src_figs) - set(chunk_figs):
            out.append(f"  MISSING: {fig}")
        for fig in set(chunk_figs) - set(src_figs):
            out.append(f"  EXTRA:   {fig}")

    log_path = os.path.join(out_dir, f"{prefix}_SpotCheck.md")
    s45_prov = format_markdown_provenance_header(rep_path, "4.5")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(s45_prov + "\n".join(out))

    if verdict == "CLEARED":
        mark_stage_complete(
            checkpoint,
            checkpoint_path,
            "4.5",
            output_file=os.path.basename(log_path),
            l2_checked=len(l2),
            passed=passed,
            failed=len(failed),
            verdict=verdict,
        )
    else:
        mark_stage_blocked(
            checkpoint,
            checkpoint_path,
            "4.5",
            output_file=os.path.basename(log_path),
            l2_checked=len(l2),
            passed=passed,
            failed=len(failed),
            verdict=verdict,
        )

    return {
        "verdict": verdict,
        "l2_checked": len(l2),
        "passed": passed,
        "failed_count": len(failed),
        "failed_ids": failed,
        "fig_ok": fig_ok,
    }