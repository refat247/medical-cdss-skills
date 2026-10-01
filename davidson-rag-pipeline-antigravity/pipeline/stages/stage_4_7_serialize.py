"""Stage 4.7 JSON output serialization (CP-04 + correction G), extracted so
the envelope shape (schema_version/pipeline_version/chapter/generated_at)
and atomic-write behavior are testable independent of the full completeness-
checklist clustering logic (which stays in SKILL.md's Stage 4.7 block
unchanged — this module only serializes the SCATTERED/SUSPECTED_GAP/
COMPLETE_DISEASES dicts that block already computes in memory).

Fixes a self-consistency bug found while writing IMPLEMENTATION_MAP.md,
independent of the evaluation guide's own CP-04 request: SKILL.md's Stage
5.2 code block already assumes "{PREFIX}_SCATTERED.json" exists
(`scattered = json.load(open(...))`), but the Stage 4.7 block as originally
written never produced it. This module is what closes that gap.
"""
import json
import os
from pipeline.stages.chunk_blocks import split_chunk_blocks
from datetime import datetime, timezone

SCHEMA_VERSION = "1.0"


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _envelope(data, pipeline_version, chapter, source_path=""):
    return {
        "_provenance": {
            "skill_name": "davidson-rag-pipeline-hyperagent",
            "skill_version": pipeline_version,
            "generated_at": _now(),
            "source_path": source_path or chapter,
            "stage": "4.7",
        },
        "schema_version": SCHEMA_VERSION,
        "pipeline_version": pipeline_version,
        "chapter": chapter,
        "generated_at": _now(),
        "data": data,
    }


def write_json_atomic(path, payload):
    """Same atomic pattern as checkpoint_utils.save_checkpoint: write to a
    sibling .tmp file, then os.replace() onto the real path, so a crash
    mid-write can never leave a half-written, unparseable JSON file behind."""
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp_path, path)


def build_stage_4_7_outputs(scattered, suspected_gap, complete_diseases, pipeline_version, chapter):
    """scattered / suspected_gap: the dicts Stage 4.7's clustering logic
    already builds in memory (unchanged). complete_diseases: list of disease
    keys with zero missing categories (new — Stage 4.7's original block
    never tracked this at all; SKILL.md's block gains one line to compute
    it: `[d for d in multi if d not in SCATTERED and d not in SUSPECTED_GAP]`).

    Returns {filename: envelope_dict} for the three JSON files CP-04
    requires — the caller writes each with write_json_atomic(); this
    function does no I/O itself so it stays trivially testable."""
    return {
        f"{{PREFIX}}_SCATTERED.json": _envelope(scattered, pipeline_version, chapter),
        f"{{PREFIX}}_SUSPECTED_GAP.json": _envelope(suspected_gap, pipeline_version, chapter),
        f"{{PREFIX}}_COMPLETE_DISEASES.json": _envelope(complete_diseases, pipeline_version, chapter),
    }


def evaluate_clinical_completeness(chunk_text: str):
    """Deterministically evaluates clinical coverage across core categories per disease focus."""
    import re
    from collections import defaultdict

    blocks = split_chunk_blocks(chunk_text)
    disease_chunks = defaultdict(list)

    categories = {
        "pathophysiology": ["pathophysiology", "aetiology", "cause", "mechanism", "pathogenesis", "genetics"],
        "clinical_features": ["clinical_feature", "symptom", "sign", "presentation", "examination", "history"],
        "investigations": ["laboratory_investigation", "diagnostic_criteria", "investigation", "biomarker", "ecg", "imaging"],
        "management": ["management_step", "drug_info", "treatment", "therapy", "surgery", "dosing"],
        "safety_prognosis": ["complication", "prognosis", "safety", "monitoring", "adverse", "risk"],
    }

    for b in blocks:
        if not re.search(r"chunk_level:\s*2", b):
            continue
        cid_m = re.search(r"chunk_id:\s*(.+)", b)
        cid = cid_m.group(1).strip() if cid_m else "?"
        df_m = re.search(r"disease_focus:\s*(.*)", b)
        df = df_m.group(1).strip() if df_m else "general"
        st_m = re.search(r"semantic_type:\s*(.*)", b)
        st = st_m.group(1).strip() if st_m else "clinical_feature"
        topic_m = re.search(r"topic:\s*(.*)", b)
        topic = topic_m.group(1).strip() if topic_m else ""
        body_m = re.search(r"---\n\n?(.*)", b, re.DOTALL)
        body = body_m.group(1).strip() if body_m else b

        disease_chunks[df].append({
            "chunk_id": cid,
            "semantic_type": st,
            "topic": topic,
            "body": body,
        })

    scattered = {}
    suspected_gap = {}
    complete_diseases = []
    category_coverage = {}

    for df, chunks in disease_chunks.items():
        if df in ("general", "self_assessment", "overview") or len(df) < 3:
            continue

        covered_cats = set()
        for ch in chunks:
            text_combo = (ch["semantic_type"] + " " + ch["topic"] + " " + ch["body"][:200]).lower()
            for cat, kws in categories.items():
                if any(kw in text_combo for kw in kws):
                    covered_cats.add(cat)

        category_coverage[df] = sorted(list(covered_cats))

        if len(chunks) >= 3:
            missing = set(categories.keys()) - covered_cats
            if "management" in missing and "investigations" in missing:
                suspected_gap[df] = f"Missing core management and diagnostic investigation coverage (covered: {sorted(list(covered_cats))})"
            elif len(covered_cats) >= 3:
                complete_diseases.append(df)
            else:
                scattered[df] = f"Partially covered across {len(covered_cats)}/5 categories: {sorted(list(covered_cats))}"
        else:
            complete_diseases.append(df)

    return {
        "scattered": scattered,
        "suspected_gap": suspected_gap,
        "complete_diseases": sorted(list(set(complete_diseases))),
        "category_coverage": category_coverage,
    }


def write_stage_4_7_outputs(out_dir, prefix, scattered, suspected_gap, complete_diseases,
                             pipeline_version, chapter):
    """Convenience wrapper used by Stage 4.7: builds the three envelopes and writes them atomically."""
    outputs = build_stage_4_7_outputs(scattered, suspected_gap, complete_diseases,
                                       pipeline_version, chapter)
    written = []
    for template, payload in outputs.items():
        filename = template.replace("{PREFIX}", prefix)
        path = os.path.join(out_dir, filename)
        write_json_atomic(path, payload)
        written.append(filename)
    return written


def evaluate_and_write_stage_4_7(chunk_text: str, out_dir: str, prefix: str, pipeline_version: str) -> dict:
    """Evaluates chunk text, writes JSON outputs and creates CompletenessChecklist.md."""
    res = evaluate_clinical_completeness(chunk_text)
    written = write_stage_4_7_outputs(
        out_dir, prefix, res["scattered"], res["suspected_gap"], res["complete_diseases"],
        pipeline_version=pipeline_version, chapter=prefix
    )

    log_path = os.path.join(out_dir, f"{prefix}_CompletenessChecklist.md")
    s47_prov = (
        "<!--\n"
        "PROVENANCE METADATA:\n"
        '  skill_name: "davidson-rag-pipeline-hyperagent"\n'
        f'  skill_version: "{pipeline_version}"\n'
        f'  generated_at: "{_now()}"\n'
        f'  source_path: "{prefix}"\n'
        '  stage: "4.7"\n'
        "-->\n\n"
    )
    report_lines = [
        f"# Stage 4.7 Completeness Checklist — {prefix}",
        f"Pipeline Version: {pipeline_version}",
        f"Generated: {_now()}",
        "",
        f"### Summary",
        f"- Complete Disease Clusters: {len(res['complete_diseases'])}",
        f"- Scattered Disease Clusters: {len(res['scattered'])}",
        f"- Suspected Gaps: {len(res['suspected_gap'])}",
        "",
        "### Cluster Coverage Matrix",
        "| Disease Focus | Categories Covered | Status |",
        "|---|---|---|",
    ]
    for df, cats in res["category_coverage"].items():
        status = "COMPLETE" if df in res["complete_diseases"] else ("GAP" if df in res["suspected_gap"] else "SCATTERED")
        report_lines.append(f"| {df} | {', '.join(cats) if cats else 'general'} | {status} |")

    with open(log_path, "w", encoding="utf-8") as f:
        f.write(s47_prov + "\n".join(report_lines) + "\n")

    return {
        "scattered": res["scattered"],
        "suspected_gap": res["suspected_gap"],
        "complete_diseases": res["complete_diseases"],
        "written_files": written,
        "checklist_md": log_path,
    }
