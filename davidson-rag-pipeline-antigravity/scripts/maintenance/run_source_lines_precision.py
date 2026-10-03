"""Real invocation of the source_lines precision checker against a
chapter's chunks.md + REPAIRED_S2.md. Checks EVERY L1+L2 chunk directly
(not just ones Stage 4.5d happened to flag via a content-pattern mismatch)
-- this is a more complete check than Stage 4.5d's candidate-driven
discovery, since a chunk with wrong source_lines but no numeric/unit/etc.
content in the mismapped region would never trigger a Stage 4.5d candidate
at all, yet still has bad provenance metadata.

Usage:
    python run_source_lines_precision.py <OUTPUT_DIR> <PREFIX>

Writes {PREFIX}_SourceLinesPrecision.md and .json. Advisory only -- does
not touch the checkpoint or gate anything. Never calls apply_corrections()
itself; that's a separate, explicit step after reviewing the report.

v2.6.3 SAFETY GUARDRAIL: CLASSIFICATION = generates new outputs (advisory
report; never touches chunks.md, RAG_Optimised.md, or the checkpoint).
Lower risk than the chapter-specific repair scripts, but still requires
--write to land in the real chapter directory -- without it, results are
computed and written to a report-only *.DRYRUN.report file instead. Does
NOT require --in-place/--backup even for a protected chapter, since this
script never modifies a certified output file, only ever its own advisory
report (which itself is never fed into a downstream gate -- see the
module-level docstring above and Stage 4.5d gate output's `source_mapping`
disclosure, requirement 7 of the v2.6.3 spec, for where this precision
data is now surfaced without being made blocking).
"""
import argparse
import sys
from pipeline.stages.chunk_blocks import split_chunk_blocks
import io
import os
import re
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pipeline.stages.source_lines_precision import check_chunk_precision
from pipeline.checkpoint_utils import PIPELINE_VERSION
from pipeline.stages.mutation_guard import guarded_write_file


def run(out_dir, prefix, args=None):
    rep_path = os.path.join(out_dir, f"{prefix}_REPAIRED_S2.md")
    chunk_path = os.path.join(out_dir, f"{prefix}_chunks.md")
    repaired = open(rep_path, encoding='utf-8').read()
    chunks_text = open(chunk_path, encoding='utf-8').read()

    blocks = split_chunk_blocks(chunks_text)
    results = [check_chunk_precision(b, repaired) for b in blocks]

    by_verdict = {}
    for r in results:
        by_verdict.setdefault(r["verdict"], []).append(r)

    md_lines = [f"# Source-Lines Precision Report — {prefix}",
                f"pipeline_version: {PIPELINE_VERSION}",
                f"Chunks checked: {len(results)}", ""]
    for verdict in ["PRECISE", "UNDER_INCLUSIVE", "OVER_INCLUSIVE",
                     "UNDER_AND_OVER_INCLUSIVE", "UNRESOLVED"]:
        items = by_verdict.get(verdict, [])
        md_lines.append(f"## {verdict} ({len(items)})")
        if verdict != "PRECISE":
            for r in items:
                declared = r.get("declared_segments")
                suggested = r.get("suggested_segments")
                md_lines.append(f"  - {r['chunk_id']}: match_rate={r.get('match_rate')} "
                                 f"declared={declared} suggested={suggested}")
        md_lines.append("")

    md_path = os.path.join(out_dir, f"{prefix}_SourceLinesPrecision.md")
    json_path = os.path.join(out_dir, f"{prefix}_SourceLinesPrecision.json")
    s8_prov_md = (
        "<!--\n"
        "PROVENANCE METADATA:\n"
        '  skill_name: "davidson-rag-pipeline-hyperagent"\n'
        f'  skill_version: "{PIPELINE_VERSION}"\n'
        f'  source_path: "{prefix}"\n'
        '  stage: "8"\n'
        "-->\n\n"
    )
    md_content = s8_prov_md + '\n'.join(md_lines)
    json_payload = {
        "_provenance": {
            "skill_name": "davidson-rag-pipeline-hyperagent",
            "skill_version": PIPELINE_VERSION,
            "source_path": prefix,
            "stage": "8",
        },
        "prefix": prefix,
        "pipeline_version": PIPELINE_VERSION,
        "results": results,
    }
    json_content = json.dumps(json_payload, indent=2)

    cli_args = args or argparse.Namespace(write=False, in_place=False, backup=False, dry_run=False)
    # v2.6.4 fix: is_new_file must reflect whether THIS PATH already exists,
    # not be hardcoded True -- a chapter that already has a
    # SourceLinesPrecision.md/.json from an earlier run (e.g. Chapter 05's
    # pre-v2.6.4 report) needs the existing-file + protected-chapter
    # authorization path, not the always-new-file path, or a protected
    # chapter's re-run crashes (out_dir/prefix were also previously never
    # threaded through, needed for the protection-marker check).
    guarded_write_file(md_path, md_content, args=cli_args, is_new_file=not os.path.exists(md_path),
                        out_dir=out_dir, prefix=prefix,
                        target_description=f"{prefix}'s SourceLinesPrecision.md")
    guarded_write_file(json_path, json_content, args=cli_args, is_new_file=not os.path.exists(json_path),
                        out_dir=out_dir, prefix=prefix,
                        target_description=f"{prefix}'s SourceLinesPrecision.json")

    print(f"Source-lines precision -> {md_path}" if cli_args.write else
          f"Source-lines precision (dry run) -> {md_path}.DRYRUN.report")
    for verdict in ["PRECISE", "UNDER_INCLUSIVE", "OVER_INCLUSIVE",
                     "UNDER_AND_OVER_INCLUSIVE", "UNRESOLVED"]:
        print(f"  {verdict}: {len(by_verdict.get(verdict, []))}")
    return results


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out_dir")
    parser.add_argument("prefix")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--in-place", action="store_true")
    parser.add_argument("--backup", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    cli = parser.parse_args()
    run(cli.out_dir, cli.prefix, args=cli)
