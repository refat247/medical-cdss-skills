"""Stage 5 — RAG_Optimised Output & Auto-Link Module (v2.13.0).

Encapsulates:
- Stage 5.4: `related_chunks` bidirectional auto-link by disease focus
- Stage 5: Final `RAG_Optimised.md` serialization, coverage field attachment, and semantic distribution logging
"""
import io
import os
from pipeline.stages.chunk_blocks import split_chunk_blocks
import re
import sys
from collections import Counter
from typing import Dict, List, Optional

from pipeline.checkpoint_utils import (
    format_markdown_provenance_header,
    load_checkpoint,
    mark_stage_complete,
    should_run_stage,
)



def run_stage_5_4_autolink(chunk_path: str, out_dir: str, prefix: str) -> dict:
    """Auto-links L2 chunks with the same disease focus."""
    checkpoint, checkpoint_path = load_checkpoint(out_dir, prefix)
    if not should_run_stage(checkpoint, "5.4"):
        return {"status": "skipped", "reason": "already complete"}

    text = open(chunk_path, encoding="utf-8").read()
    blocks = split_chunk_blocks(text)

    id_to_disease = {}
    for b in blocks:
        if not re.search(r"chunk_level:\s*2", b):
            continue
        cid_m = re.search(r"chunk_id:\s*(.+)", b)
        cid = cid_m.group(1).strip() if cid_m else ""
        df_m = re.search(r"disease_focus:\s*(.*)", b)
        df = df_m.group(1).strip() if df_m else ""
        if cid:
            id_to_disease[cid] = df

    disease_to_ids = {}
    for cid, df in id_to_disease.items():
        if df:
            disease_to_ids.setdefault(df, []).append(cid)

    def get_related(cid, df):
        if not df or df in ("general", "self_assessment", "overview"):
            return []
        related = []
        # 1. Exact match
        for other_cid in disease_to_ids.get(df, []):
            if other_cid != cid and other_cid not in related:
                related.append(other_cid)
        # 2. Stem/substring match (e.g., asthma <-> acute_severe_asthma)
        for other_df, other_ids in disease_to_ids.items():
            if other_df == df or other_df in ("general", "self_assessment", "overview"):
                continue
            if (len(df) >= 4 and df in other_df) or (len(other_df) >= 4 and other_df in df):
                for other_cid in other_ids:
                    if other_cid != cid and other_cid not in related:
                        related.append(other_cid)
        return related[:10]

    def add_related(block):
        if not re.search(r"chunk_level:\s*2", block):
            return block
        block = re.sub(r"^related_chunks:.*\n", "", block, flags=re.M)
        cid_m = re.search(r"chunk_id:\s*(.+)", block)
        if not cid_m:
            return block
        cid = cid_m.group(1).strip()
        df = id_to_disease.get(cid, "")
        related = get_related(cid, df)
        return re.sub(
            r"(disease_focus:\s*.*\n)",
            rf"\1related_chunks: [{', '.join(related)}]\n",
            block,
            count=1,
        )

    reassembled = text
    for old in blocks:
        new = add_related(old)
        if old != new:
            reassembled = reassembled.replace(old, new, 1)

    with open(chunk_path, "w", encoding="utf-8") as f:
        f.write(reassembled)

    mark_stage_complete(
        checkpoint,
        checkpoint_path,
        "5.4",
        output_file=os.path.basename(chunk_path),
        linked_chunks=len(id_to_disease),
    )
    return {"linked_chunks": len(id_to_disease)}


def run_stage_5(
    chunk_path: str,
    out_dir: str,
    prefix: str,
    ch_num: str = "??",
    ch_display: str = "Unknown",
    scattered_notes: Optional[Dict[str, str]] = None,
) -> dict:
    """Generates the final RAG_Optimised.md file from L2 chunks."""
    checkpoint, checkpoint_path = load_checkpoint(out_dir, prefix)
    if not should_run_stage(checkpoint, "5"):
        return {"status": "skipped", "reason": "already complete"}

    if scattered_notes is None:
        scattered_notes = {}

    text = open(chunk_path, encoding="utf-8").read()
    blocks = split_chunk_blocks(text)
    l2 = [b.strip() for b in blocks if re.search(r"chunk_level:\s*2", b)]

    def add_coverage_fields(block):
        if re.search(r"^coverage_status:", block, re.M):
            return block
        cid_m = re.search(r"chunk_id:\s*(.+)", block)
        cid = cid_m.group(1).strip() if cid_m else ""
        if cid in scattered_notes:
            status, note = "partial", scattered_notes[cid]
        else:
            status, note = "complete", ""
        return re.sub(
            r"(chunk_level:\s*\d+\n)",
            rf'\1coverage_status: {status}\ngap_note: "{note}"\n',
            block,
            count=1,
        )

    l2 = [add_coverage_fields(b) for b in l2]

    prov_hdr = format_markdown_provenance_header(chunk_path, stage_name="5")
    header = (
        prov_hdr +
        f"# Davidson's Principles and Practice of Medicine, 25th Edition\n"
        f"# Chapter {ch_num} — {ch_display}\n"
        f"# RAG-Optimised Output — L2 Micro Chunks\n"
        f"# Total L2 chunks: {len(l2)}\n"
        f"# Source: markdown_inlined.md (Mistral native PDF, tables inlined)\n\n---\n\n"
    )
    rag_path = os.path.join(out_dir, f"{prefix}_RAG_Optimised.md")
    output = header + "\n\n---\n\n".join(l2)
    with open(rag_path, "w", encoding="utf-8") as f:
        f.write(output)


    dist = Counter(re.findall(r"^semantic_type:\s*(.+)", output, re.M))
    remap_log_path = os.path.join(out_dir, f"{prefix}_Remap_Log.md")
    with open(remap_log_path, "a", encoding="utf-8") as f:
        f.write(f"\n\n## Stage 5 Final — {len(l2)} L2 chunks\n")
        for t, c in dist.most_common():
            f.write(f"  {t}: {c}\n")

    mark_stage_complete(
        checkpoint,
        checkpoint_path,
        "5",
        output_file=os.path.basename(rag_path),
        l2_chunks=len(l2),
    )
    return {
        "rag_path": rag_path,
        "l2_chunks": len(l2),
        "semantic_distribution": dict(dist),
    }