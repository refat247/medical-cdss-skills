"""Applies manually-verified source_lines corrections to Chapter 05's
chunks.md for the 6 highest-confidence findings from
{PREFIX}_SourceLinesPrecision.md (4 UNDER_INCLUSIVE + the two confirmed
OVER_INCLUSIVE cases, L2-118/L2-126).

IMPORTANT: these are NOT the tool's raw `suggested_segments` applied
verbatim. The checker's anchor matching never uses a chunk's own heading
line as an anchor (see source_lines_precision.py's _anchor_units), so its
suggestions systematically start 1-2 lines late, dropping the heading from
the declared range. Each value below was re-verified by hand against
REPAIRED_S2.md before use:

- L2-080 (declared "882-891"): body's own last line is a stray
  running-header residue ("Disorders of altered energy balance") that
  Stage 2's repair didn't fully strip and Stage 4B verbatim-captured as
  part of this chunk -- confirmed present at REPAIRED_S2.md line 893,
  immediately after the declared range. Widened end 891 -> 893, start
  unchanged (882 correctly includes the box heading).
- L2-086 (declared "942-969"): same pattern, trailing
  "NUTRITIONAL FACTORS IN DISEASE" residue confirmed at line 971. Widened
  end 969 -> 971, start unchanged.
- L1-056 / L2-097 (declared "1045-1058"): body includes a full vitamin
  reference-intake table that starts at line 1059 (declared end excluded
  it entirely) and the same trailing "NUTRITIONAL FACTORS IN DISEASE"
  residue at line 1084. Widened end 1058 -> 1084, start unchanged (1045
  correctly includes the "## Vitamins" heading).
- L2-118 (declared "1301-1305, 1307-1334"): declared range swept in an
  entire unrelated box (Box 5.36, scurvy causes/clinical features, lines
  1309-1332) that is separately and correctly chunked elsewhere. Corrected
  to "1301-1307, 1334-1334" -- keeps the chunk's own prose before the box
  (including the trailing header residue at 1307, confirmed part of this
  chunk's body) and the single line that resumes after the box (1334).
- L2-126 (declared "1376-1386"): a single stray interleaved caption line
  ("Diseases associated with deficiency and excess of vitamins and
  minerals") at line 1380 is not part of this chunk's real Iron content.
  Corrected to "1376-1379, 1381-1386" -- excludes only that one line.

Regenerating RAG_Optimised.md from the corrected chunks.md, and re-running
Stage 4.5d/Stage 6, are separate, explicit follow-up steps
(regenerate_rag_optimised_ch05.py, run_stage_4_5d.py, rerun_stage6_ch05.py)
-- not performed automatically by this script.

v2.6.3 SAFETY GUARDRAIL: CLASSIFICATION = chapter-specific repair, mutates
an existing certified output (chunks.md). Default invocation is READ-ONLY
-- computes and reports the corrected text without overwriting the real
file. Requires --write --in-place --backup (backup mandatory once
CORPUS_OUTPUT_PROTECTED.json exists for this chapter) to actually mutate.
"""
import argparse
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from pipeline.stages.source_lines_precision import apply_corrections
from pipeline.stages.mutation_guard import guarded_write_file

OUT_DIR = r"D:\davidson_25_full_pipeline\05"
PREFIX = "Davidson_25_Ch05_Nutritional_factors_in_disease"

CORRECTIONS = {
    "L2-080": [(882, 893)],
    "L2-086": [(942, 971)],
    "L1-056": [(1045, 1084)],
    "L2-097": [(1045, 1084)],
    "L2-118": [(1301, 1307), (1334, 1334)],
    "L2-126": [(1376, 1379), (1381, 1386)],
}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--in-place", action="store_true")
    parser.add_argument("--backup", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    chunk_path = os.path.join(OUT_DIR, f"{PREFIX}_chunks.md")
    chunks_text = open(chunk_path, encoding="utf-8").read()
    new_text, changed, unmatched = apply_corrections(chunks_text, CORRECTIONS)
    print(f"Computed {changed} corrections, {len(unmatched)} unmatched: {unmatched}")
    assert changed == len(CORRECTIONS), "expected all 6 corrections to apply"
    assert not unmatched

    for cid, segs in CORRECTIONS.items():
        m = re.search(rf'chunk_id:\s*{re.escape(cid)}\b.*?source_lines:\s*"([^"]+)"', new_text, re.DOTALL)
        print(f"  {cid} -> source_lines: \"{m.group(1) if m else '???'}\"")

    result = guarded_write_file(
        chunk_path, new_text, args=args, is_new_file=False,
        out_dir=OUT_DIR, prefix=PREFIX, target_description="chunks.md",
    )
    if result["written"]:
        print(f"Wrote corrected {chunk_path}")
    return result


if __name__ == "__main__":
    main()
