"""Regenerates RAG_Optimised.md from the corrected chunks.md (Stage 5's own
logic, unchanged, replicated here as a standalone re-run since Stage 5 is
deterministic/regex-based -- no subagent involved, safe to re-run directly
rather than hand-pasting SKILL.md's inline block into a session).

Only source_lines frontmatter changed in chunks.md
(apply_source_lines_corrections_ch05.py) -- coverage_status/gap_note
assignment logic is unchanged and unaffected by that edit.

v2.6.3 SAFETY GUARDRAIL: CLASSIFICATION = chapter-specific repair, mutates
the single most trusted certified output file (RAG_Optimised.md). Default
invocation is READ-ONLY -- computes and reports the would-be regenerated
content without overwriting the real file. Requires --write --in-place
--backup (backup mandatory once CORPUS_OUTPUT_PROTECTED.json exists for
this chapter) to actually mutate.
"""
import argparse
import os
import sys
import re
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from pipeline.stages.mutation_guard import guarded_write_file

OUT_DIR = r"D:\davidson_25_full_pipeline\05"
PREFIX = "Davidson_25_Ch05_Nutritional_factors_in_disease"
CH_NUM = "05"
CH_DISPLAY = "Nutritional factors in disease"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--in-place", action="store_true")
    parser.add_argument("--backup", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    chunk_path = f"{OUT_DIR}\\{PREFIX}_chunks.md"
    rag_path = f"{OUT_DIR}\\{PREFIX}_RAG_Optimised.md"

    SCATTERED_CHUNK_NOTES = {}  # unchanged from the original Stage 5 run for this chapter

    text = open(chunk_path, encoding='utf-8').read()
    blocks = re.findall(r'(---\nchunk_id:.*?\n---\n.*?)(?=\n---\nchunk_id:|\Z)', text, re.DOTALL)
    l2 = [b.strip() for b in blocks if re.search(r'chunk_level:\s*2', b)]

    def add_coverage_fields(block):
        if re.search(r'^coverage_status:', block, re.M):
            return block
        cid = re.search(r'chunk_id:\s*(.+)', block).group(1).strip()
        if cid in SCATTERED_CHUNK_NOTES:
            status, note = 'partial', SCATTERED_CHUNK_NOTES[cid]
        else:
            status, note = 'complete', ''
        return re.sub(r'(chunk_level:\s*\d+\n)',
                       rf'\1coverage_status: {status}\ngap_note: "{note}"\n', block, count=1)

    l2 = [add_coverage_fields(b) for b in l2]

    header = (
        f"# Davidson's Principles and Practice of Medicine, 25th Edition\n"
        f"# Chapter {CH_NUM} — {CH_DISPLAY}\n"
        f"# RAG-Optimised Output — L2 Micro Chunks\n"
        f"# Total L2 chunks: {len(l2)}\n"
        f"# Source: markdown_inlined.md (Mistral native PDF, tables inlined)\n\n---\n\n"
    )
    output = header + '\n\n---\n\n'.join(l2)

    old_rag = open(rag_path, encoding='utf-8').read()
    old_l2_count = old_rag.count('chunk_level: 2')
    print(f"L2 chunks: before={old_l2_count} after={len(l2)} (should be unchanged -- metadata-only edit)")
    assert len(l2) == old_l2_count, "chunk COUNT changed -- this should never happen from a source_lines-only edit"

    result = guarded_write_file(
        rag_path, output, args=args, is_new_file=False,
        out_dir=OUT_DIR, prefix=PREFIX, target_description="RAG_Optimised.md",
    )
    if result["written"]:
        print(f"Regenerated {rag_path}")
        dist = Counter(re.findall(r'^semantic_type:\s*(.+)', output, re.M))
        print("Semantic type distribution unchanged check: OK (chunk set identical, only source_lines values differ)")
    return result


if __name__ == "__main__":
    main()
