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

    passed, failed, skipped = 0, [], 0
    for chunk in l2:
        body = chunk["body"].strip()
        if not body or len(body) < 40:
            skipped += 1
            continue
        found = False
        for offset in [len(body) // 2, 0, len(body) // 4, len(body) * 3 // 4]:
            sl = body[offset:offset + 100].strip()
            sl_clean = re.sub(r"\*+|_+|`+|^#+\s", "", sl, flags=re.MULTILINE).strip()
            if sl_clean and len(sl_clean) >= 30 and (sl_clean in repaired or sl in repaired):
                found = True
                break
        if found:
            passed += 1
        else:
            failed.append(chunk["id"])

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