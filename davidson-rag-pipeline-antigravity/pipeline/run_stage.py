"""Unified Stage Runner CLI for Davidson RAG Pipeline (v2.25.0).

Enables single-command execution of any pipeline stage or automated chaining:
    Individual: python -m pipeline.run_stage --stage <STAGE_KEY> --source <SOURCE_PATH> --out <OUTPUT_DIR>
    Automated:  python -m pipeline.run_stage --stage auto --source <SOURCE_PATH> --out <OUTPUT_DIR>
"""
import argparse
import io
import json
import os
import re
import shutil
import sys

# Ensure SKILL_DIR is in sys.path
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SKILL_DIR not in sys.path:
    sys.path.insert(0, SKILL_DIR)

from pipeline.checkpoint_utils import (
    format_markdown_provenance_header,
    load_checkpoint,
    load_or_create_checkpoint,
    mark_stage_blocked,
    mark_stage_complete,
    mark_stage_failed,
    mark_stage_in_progress,
    should_run_stage,
)




def sync_chapter_assets(source_path: str, out_dir: str) -> None:
    """Copies <chapter>/assets into <out_dir>/assets (merging into an existing folder). Raises on failure."""
    src_assets = os.path.join(os.path.dirname(source_path), "assets")
    out_assets = os.path.join(out_dir, "assets")
    if os.path.exists(src_assets) and os.path.abspath(src_assets) != os.path.abspath(out_assets):
        shutil.copytree(src_assets, out_assets, dirs_exist_ok=True)


def derive_chapter_info(source_path: str) -> dict:
    # Split on both separators so Windows-style paths work on POSIX too.
    basename = re.split(r"[\\/]", source_path.rstrip("\\/"))[-1]
    # Strip any leading upload / file-id prefix (e.g. 12345678_Davidson_25_...)
    clean_name = re.sub(r"^[a-fA-F0-9\-]{6,}_", "", basename)
    
    lower_path = (source_path + " " + clean_name).lower()
    is_guideline = any(k in lower_path for k in [
        "guideline", "standards_of_care", "consensus", "kdigo", "ada_", "esc_", "nice_", "who_"
    ])
    doc_archetype = "GUIDELINE" if is_guideline else "TEXTBOOK"

    m = (
        re.search(r"Davidson_25_(\d+)_(.+?)\.pdf", source_path) or
        re.search(r"Davidson_25_Ch(\d+)_(.+?)(?:\.pdf|\.markdown|\.md|$)", clean_name) or
        re.search(r"Davidson_25_(\d+)_(.+?)(?:\.pdf|\.markdown|\.md|$)", clean_name)
    )
    m_harrison = (
        re.search(r"Harrison_22_PART[_\-\s]*(\d+)[_\-\s]*(.*?)(?:\.pdf|\.markdown|$)", clean_name, re.IGNORECASE) or
        re.search(r"Harrison_22_Part(\d+)(?:\.pdf|\.markdown|$)", clean_name, re.IGNORECASE)
    )
    if m:
        ch_num = m.group(1)
        ch_slug = m.group(2).replace(" ", "_")
        ch_display = m.group(2).replace("_", " ")
        prefix = f"Davidson_25_Ch{ch_num}_{ch_slug}"
    elif m_harrison:
        ch_num = m_harrison.group(1).zfill(2)
        raw_slug = m_harrison.group(2) if len(m_harrison.groups()) >= 2 and m_harrison.group(2) else ""
        ch_slug = raw_slug.replace(" ", "_").strip("_") if raw_slug else f"Part{ch_num}"
        ch_display = raw_slug.replace("_", " ").strip() if raw_slug else f"Part {ch_num}"
        prefix = f"Harrison_22_Part{ch_num}_{ch_slug}" if ch_slug else f"Harrison_22_Part{ch_num}"
    else:
        clean_base = re.sub(r"\.pdf.*$|\.markdown_inlined.*$|\.md.*$", "", clean_name)
        roman_map = {
            "I": "01", "II": "02", "III": "03", "IV": "04", "V": "05",
            "VI": "06", "VII": "07", "VIII": "08", "IX": "09", "X": "10",
            "XI": "11", "XII": "12", "XIII": "13", "XIV": "14", "XV": "15",
            "XVI": "16", "XVII": "17", "XVIII": "18", "XIX": "19", "XX": "20"
        }
        m_rom = re.search(r"(?:^|[_\-\s])(?:section|sec|part|ch(?:apter)?)[_\-\s]+([IVXLCDM]+)(?:[_\-\s]|$)", clean_base, re.IGNORECASE)
        if m_rom and m_rom.group(1).upper() in roman_map:
            ch_num = roman_map[m_rom.group(1).upper()]
        else:
            m_ch = re.search(r"Ch(?:apter)?[_-]?(\d+)", clean_base, re.IGNORECASE)
            if not m_ch:
                # Match isolated chapter digits that are not 4-digit publication years
                m_ch = re.search(r"(?:^|[_\-\s])(?!19\d\d|20\d\d)(\d{1,3})(?:[_\-\s]|$)", clean_base)
            ch_num = m_ch.group(1).zfill(2) if m_ch else "01"
        ch_slug = re.sub(r"[^\w\-]+", "_", clean_base).strip("_") or "Document"
        ch_display = ch_slug.replace("_", " ")
        prefix = ch_slug

    pharma_keywords = [
        "therapeutics", "pharmacol", "cardiol", "cardio", "infectious",
        "respiratory", "gastro", "nephrol", "endocrin",
        "haematol", "oncol", "rheumatol", "dermatol", "dengue",
        "prescrib", "poison", "toxicol",
    ]
    is_pharma = any(k in ch_display.lower() for k in pharma_keywords)
    return {
        "ch_num": ch_num,
        "ch_slug": ch_slug,
        "ch_display": ch_display,
        "prefix": prefix,
        "is_pharma": is_pharma,
        "doc_archetype": doc_archetype,
    }


def execute_stage(stage: str, source_path: str, out_dir: str = None, prefix: str = None, force: bool = False, auto_adjudicate: bool = False, use_llm: bool = False) -> dict:
    """Executes a single pipeline stage and returns an execution result dictionary."""

    source_path = os.path.abspath(source_path)
    if not out_dir or os.path.abspath(out_dir) == os.path.dirname(source_path):
        out_dir = os.path.join(os.path.dirname(source_path), "rag_pipeline_output")
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    # Sync assets directory from source chapter directory to out_dir/assets if present
    try:
        sync_chapter_assets(source_path, out_dir)
    except Exception as e:
        print(f"Asset sync failed: {e}")
        return {"status": "ERROR", "stage": stage, "message": f"Asset sync from chapter assets/ failed: {e}"}

    info = derive_chapter_info(source_path)
    prefix = prefix or info["prefix"]
    stage = stage.lower()

    rep_path = os.path.join(out_dir, f"{prefix}_REPAIRED_S2.md")
    chunk_path = os.path.join(out_dir, f"{prefix}_chunks.md")
    rag_path = os.path.join(out_dir, f"{prefix}_RAG_Optimised.md")

    if stage in ("0", "init", "checkpoint"):
        checkpoint, checkpoint_path = load_or_create_checkpoint(
            source_path=source_path,
            output_dir=out_dir,
            prefix=prefix,
            ch_num=info["ch_num"],
            ch_slug=info["ch_slug"],
        )
        print(f"Initialized checkpoint at: {checkpoint_path}")
        print(f"Next stage to run: {checkpoint['pipeline_state']['next_stage_to_run']}")
        return {"status": "COMPLETED", "stage": "0", "checkpoint_path": checkpoint_path}

    if stage == "1":
        from pipeline.stages.stage_1_audit import run_stage_1
        res = run_stage_1(source_path, out_dir, prefix)
        verdict = res.get("verdict", "unknown")
        print(f"Stage 1 -> {verdict}")
        return {"status": "COMPLETED", "stage": "1", "verdict": verdict, "data": res}

    elif stage == "2":
        from pipeline.stages.stage_2_repair import repair_stage2
        checkpoint, checkpoint_path = load_checkpoint(out_dir, prefix)
        if not force and not should_run_stage(checkpoint, "2"):
            print("Stage 2 skipped (already complete or not required)")
            return {"status": "SKIPPED", "stage": "2"}

        with open(source_path, encoding="utf-8") as f:
            text = f.read()
        repaired_text, report_lines, stats = repair_stage2(text)
        s2_prov = format_markdown_provenance_header(source_path, "2")
        with open(rep_path, "w", encoding="utf-8") as f:
            f.write(s2_prov + repaired_text)
        log_path = os.path.join(out_dir, f"{prefix}_Corrections_Log.md")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(s2_prov + f"# Corrections Log — {prefix}\n\nOriginal: {stats['lines_before']} lines\nRepaired: {stats['lines_after']} lines\n\n")
            f.write("\n".join(f"- {r}" for r in report_lines))
        mark_stage_complete(
            checkpoint,
            checkpoint_path,
            "2",
            output_file=os.path.basename(rep_path),
            lines_before=stats["lines_before"],
            lines_after=stats["lines_after"],
            fixes_applied=len([r for r in report_lines if any(k in r for k in ["Removed", "Fixed", "Demoted"])]),
        )
        print(f"Stage 2 done -> {rep_path} (before: {stats['lines_before']}, after: {stats['lines_after']})")
        return {"status": "COMPLETED", "stage": "2", "lines_before": stats["lines_before"], "lines_after": stats["lines_after"]}

    elif stage == "3":
        from pipeline.stages.stage_3_reaudit import compute_reaudit, decide_checkpoint_action
        checkpoint, checkpoint_path = load_checkpoint(out_dir, prefix)
        if not force and not should_run_stage(checkpoint, "3"):
            print("Stage 3 skipped (already complete)")
            return {"status": "SKIPPED", "stage": "3"}
        orig = open(source_path, encoding="utf-8").read()
        rep = open(rep_path, encoding="utf-8").read()
        result = compute_reaudit(orig, rep)
        log_path = os.path.join(out_dir, f"{prefix}_REAUDIT_REPORT.md")
        s3_prov = format_markdown_provenance_header(source_path, "3")
        out = [s3_prov.rstrip(), "", f"# Reaudit — {prefix}", f"Preservation: {result['preservation_percent']}%", f"H1 count: {result['h1_count']}", f"VERDICT: {result['verdict']}"]
        if result["issues"]:
            out += ["\nISSUES:"] + [f"  - {i}" for i in result["issues"]]
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(out))
        action, metadata = decide_checkpoint_action(result)
        if action == "complete":
            mark_stage_complete(checkpoint, checkpoint_path, "3", output_file=os.path.basename(log_path), **metadata)
            print(f"Stage 3 -> {log_path} | {result['verdict']} | action={action}")
            return {"status": "COMPLETED", "stage": "3", "verdict": result["verdict"], "action": action}
        else:
            mark_stage_blocked(checkpoint, checkpoint_path, "3", output_file=os.path.basename(log_path), **metadata)
            print(f"Stage 3 -> {log_path} | {result['verdict']} | action={action}")
            return {"status": "BLOCKED", "stage": "3", "verdict": result["verdict"], "action": action}

    elif stage == "4a":
        from pipeline.stages.stage_4_parse import run_stage_4a
        res = run_stage_4a(rep_path, out_dir, prefix)
        print(f"Stage 4A -> {res}")
        return {"status": "COMPLETED", "stage": "4a", "data": res}

    elif stage == "4b":
        from pipeline.stages.stage_4_parse import run_stage_4b
        res = run_stage_4b(rep_path, out_dir, prefix)
        print(f"Stage 4B -> {res.get('l1_count')} L1 chunks, {res.get('l2_count')} L2 chunks")
        return {"status": "COMPLETED", "stage": "4b", "l1_count": res.get("l1_count"), "l2_count": res.get("l2_count")}

    elif stage in ("4.5", "45"):
        from pipeline.stages.stage_4_5_spotcheck import run_stage_4_5
        res = run_stage_4_5(rep_path, chunk_path, out_dir, prefix)
        if res.get("status") == "skipped":
            print("Stage 4.5 skipped (already complete)")
            return {"status": "SKIPPED", "stage": "4.5"}
        verdict = res.get("verdict", "FAIL")
        print(f"Stage 4.5 -> VERDICT {verdict} | Passed: {res.get('passed')} | Failed: {res.get('failed_count')}")
        status = "COMPLETED" if verdict == "CLEARED" else "BLOCKED"
        return {"status": status, "stage": "4.5", "verdict": verdict, "passed": res.get("passed"), "failed_count": res.get("failed_count")}

    elif stage in ("4.5b", "45b"):
        from pipeline.stages.stage_4_5b_pharma import run_stage_4_5b
        res = run_stage_4_5b(rep_path, chunk_path, out_dir, prefix, is_active=info["is_pharma"])
        verdict = res.get("verdict", res.get("status", "COMPLETE"))
        print(f"Stage 4.5b -> {verdict}")
        return {"status": "COMPLETED", "stage": "4.5b", "verdict": verdict}

    elif stage in ("4.5c", "45c"):
        from pipeline.stages.stage_4_5c_coverage import compute_coverage_gaps, decide_checkpoint_action
        checkpoint, checkpoint_path = load_checkpoint(out_dir, prefix)
        if not force and not should_run_stage(checkpoint, "4.5c"):
            print("Stage 4.5c skipped")
            return {"status": "SKIPPED", "stage": "4.5c"}
        text = open(chunk_path, encoding="utf-8").read()
        result = compute_coverage_gaps(text)
        log_path = os.path.join(out_dir, f"{prefix}_L1L2_CoverageGaps.md")
        s45c_prov = format_markdown_provenance_header(source_path, "4.5c")
        out = [
            s45c_prov.rstrip(),
            "",
            f"# Stage 4.5c L1/L2 Coverage Gate — {prefix}",
            f"L1 chunks checked: {result['l1_checked']} | Threshold: 90%",
            f"VERDICT: {result['verdict']}",
            "",
            "| chunk_id | topic | source_lines | coverage_pct | uncovered_excerpt |",
            "|---|---|---|---|---|",
        ]
        for g in result["gaps"]:
            out.append(f"| {g['id']} | {g['topic']} | {g['source_lines']} | {g['coverage_pct']}% | {g['excerpt']} |")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(out))

        action, metadata = decide_checkpoint_action(result)
        if action == "complete":
            mark_stage_complete(checkpoint, checkpoint_path, "4.5c", output_file=os.path.basename(log_path), **metadata)
            print(f"Stage 4.5c -> {log_path} | {result['verdict']} | {len(result['gaps'])} gaps")
            return {"status": "COMPLETED", "stage": "4.5c", "verdict": result["verdict"], "gaps": len(result["gaps"])}
        else:
            mark_stage_blocked(checkpoint, checkpoint_path, "4.5c", output_file=os.path.basename(log_path), **metadata)
            print(f"Stage 4.5c -> {log_path} | {result['verdict']} | {len(result['gaps'])} gaps")
            return {"status": "BLOCKED", "stage": "4.5c", "verdict": result["verdict"], "gaps": len(result["gaps"])}

    elif stage in ("4.5d", "45d"):
        from pipeline.stages import stage_4_5d_clinical_fidelity as s45d
        from scripts.maintenance.run_stage_4_5d import run_stage_4_5d
        checkpoint, checkpoint_path = load_checkpoint(out_dir, prefix)
        if not force and not should_run_stage(checkpoint, "4.5d"):
            print("Stage 4.5d skipped")
            return {"status": "SKIPPED", "stage": "4.5d"}
        gate, candidates = run_stage_4_5d(out_dir, prefix)
        action, metadata = s45d.decide_checkpoint_action(gate)
        gate_out = f"{prefix}_ClinicalFidelityGate.json"
        if action == "complete":
            mark_stage_complete(checkpoint, checkpoint_path, "4.5d", output_file=gate_out, **metadata)
            print(f"Stage 4.5d -> VERDICT {gate['verdict']} | {gate['candidate_count']} candidate(s) | action={action}")
            return {"status": "COMPLETED", "stage": "4.5d", "action": action, "candidates": gate["candidate_count"]}
        elif action == "pending_manual":
            mark_stage_in_progress(
                checkpoint, checkpoint_path, "4.5d",
                candidates_found=gate["candidate_count"],
                unresolved_candidates=gate["unresolved_candidates"],
                detectors_run=gate["detectors_run"],
                output_file=gate_out,
            )
            print(f"Stage 4.5d -> VERDICT {gate['verdict']} | {gate['candidate_count']} candidate(s) | action={action}")
            return {"status": "PENDING_MANUAL", "stage": "4.5d", "action": action, "candidates": gate["candidate_count"]}
        elif action == "blocked":
            mark_stage_blocked(checkpoint, checkpoint_path, "4.5d", output_file=gate_out, **metadata)
            print(f"Stage 4.5d -> VERDICT {gate['verdict']} | {gate['candidate_count']} candidate(s) | action={action}")
            return {"status": "BLOCKED", "stage": "4.5d", "action": action, "candidates": gate["candidate_count"]}
        else:
            mark_stage_failed(checkpoint, checkpoint_path, "4.5d", output_file=gate_out, **metadata)
            print(f"Stage 4.5d -> VERDICT {gate['verdict']} | {gate['candidate_count']} candidate(s) | action={action}")
            return {"status": "FAILED", "stage": "4.5d", "action": action, "candidates": gate["candidate_count"]}

    elif stage in ("4.6", "46"):
        from pipeline.stage_4_6_gemini_verification import stage_4_with_verification
        from pipeline.stages.stage_4_6_decision import decide_checkpoint_action
        checkpoint, checkpoint_path = load_checkpoint(out_dir, prefix)
        if not force and not should_run_stage(checkpoint, "4.6"):
            print("Stage 4.6 skipped")
            return {"status": "SKIPPED", "stage": "4.6"}
        chunks_data = open(chunk_path, encoding="utf-8").read()
        rep_text = open(rep_path, encoding="utf-8").read()

        if use_llm:
            print("      [STAGE 4.6] Opt-in LLM verification enabled (--use-llm). Calling model API...")
            final, meta = stage_4_with_verification(chunks_data, rep_text, levels=(2,))
        else:
            print("      [STAGE 4.6] Running zero-token deterministic offline clinical adjudication...")
            from pipeline.stage_4_6_gemini_verification import offline_adjudicate_all
            from pipeline.stages.stage_4_6_decision import decide_checkpoint_action
            final, meta = offline_adjudicate_all(chunks_data, levels=(2,))

        log_path = os.path.join(out_dir, f"{prefix}_Remap_Log.md")
        s46_prov = format_markdown_provenance_header(source_path, "4.6")
        corr_items = meta.get("corrections_applied", [])
        if corr_items:
            corr_body = "\n".join(f"- {c[0]}: {c[1]} -> {c[2]}" if isinstance(c, (list, tuple)) and len(c) >= 3 else f"- {c}" for c in corr_items)
        else:
            corr_body = "- No manual corrections required (all initial semantic types confirmed)"
        method_name = meta.get("verification_method", "llm_gemini" if use_llm else "offline_deterministic_clinical_rules")
        remap_log_content = (
            s46_prov +
            f"# Stage 4.6 Verification & Remap Log — {prefix}\n\n"
            f"Verification Method: {method_name}\n"
            f"Total L2 Chunks Reviewed: {meta.get('chunks_reviewed', 0)}\n"
            f"Chunks Corrected: {meta.get('chunks_corrected', 0)}\n"
            f"Unparsed: {meta.get('chunks_unparsed', 0)}\n"
            f"Status: success\n\n"
            f"## Corrections Applied:\n{corr_body}\n"
        )
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(remap_log_content)
        total_flagged = len(meta.get("review_priority", [])) if meta.get("review_priority") is not None else meta.get("chunks_reviewed", 0)
        action, decision_metadata = decide_checkpoint_action(meta, total_flagged=total_flagged)

        if use_llm and action in ("pending_manual", "review_incomplete") and (auto_adjudicate or os.environ.get("ANTIGRAVITY_OFFLINE_ADJUDICATE") == "1"):
            print("      Applying deterministic offline clinical adjudication fallback for Stage 4.6...")
            from pipeline.stage_4_6_gemini_verification import offline_adjudicate_all
            final, meta = offline_adjudicate_all(chunks_data, levels=(2,))
            corr_items = meta.get("corrections_applied", [])
            if corr_items:
                corr_body = "\n".join(f"- {c[0]}: {c[1]} -> {c[2]}" if isinstance(c, (list, tuple)) and len(c) >= 3 else f"- {c}" for c in corr_items)
            else:
                corr_body = "- No manual corrections required (all initial semantic types confirmed)"
            remap_log_content = (
                s46_prov +
                f"# Stage 4.6 Verification & Remap Log — {prefix}\n\n"
                f"Verification Method: offline_deterministic_clinical_rules\n"
                f"Total L2 Chunks Reviewed: {meta.get('chunks_reviewed', 0)}\n"
                f"Chunks Corrected: {meta.get('chunks_corrected', 0)}\n"
                f"Unparsed: {meta.get('chunks_unparsed', 0)}\n"
                f"Status: success\n\n"
                f"## Corrections Applied:\n{corr_body}\n"
            )
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(remap_log_content)
            total_flagged = meta.get("chunks_reviewed", 0)
            action, decision_metadata = decide_checkpoint_action(meta, total_flagged=total_flagged)

        # Record the real gate outcome in the remap log (not a blanket "success")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(remap_log_content.replace("Status: success", f"Status: {action}"))

        # Persist HOW the review was done, so a later reader can tell an LLM/human review from the
        # offline title-rule pass (the checkpoint used to say only "COMPLETED").
        decision_metadata["verification_method"] = meta.get("verification_method", "llm_gemini" if use_llm else "unknown")
        decision_metadata["independent_verification"] = bool(meta.get("independent_verification", use_llm))

        if action == "complete":
            with open(chunk_path, "w", encoding="utf-8") as f:
                f.write(final)
            mark_stage_complete(checkpoint, checkpoint_path, "4.6", output_file=os.path.basename(log_path), **decision_metadata)
            print(f"Stage 4.6 -> {log_path} | {meta.get('chunks_corrected', 0)} corrected | action={action}")
            return {"status": "COMPLETED", "stage": "4.6", "corrected": meta.get("chunks_corrected", 0), "action": action}
        elif action in ("pending_manual", "review_incomplete"):
            mark_stage_in_progress(checkpoint, checkpoint_path, "4.6", output_file=os.path.basename(log_path), **decision_metadata)
            print(f"Stage 4.6 -> {log_path} | {meta.get('chunks_corrected', 0)} corrected | action={action} (manual review pending)")
            return {"status": "PENDING_MANUAL", "stage": "4.6", "corrected": meta.get("chunks_corrected", 0), "action": action}
        elif action == "blocked":
            mark_stage_blocked(checkpoint, checkpoint_path, "4.6", output_file=os.path.basename(log_path), **decision_metadata)
            print(f"Stage 4.6 -> {log_path} | {meta.get('chunks_corrected', 0)} corrected | action={action}")
            return {"status": "BLOCKED", "stage": "4.6", "corrected": meta.get("chunks_corrected", 0), "action": action}
        elif action == "failed":
            mark_stage_failed(checkpoint, checkpoint_path, "4.6", output_file=os.path.basename(log_path), **decision_metadata)
            print(f"Stage 4.6 -> {log_path} | {meta.get('chunks_corrected', 0)} corrected | action={action}")
            return {"status": "FAILED", "stage": "4.6", "corrected": meta.get("chunks_corrected", 0), "action": action}
        else:
            mark_stage_blocked(checkpoint, checkpoint_path, "4.6", output_file=os.path.basename(log_path), **decision_metadata)
            print(f"Stage 4.6 -> {log_path} | Unknown action '{action}' blocked fail-closed")
            return {"status": "BLOCKED", "stage": "4.6", "action": action}

    elif stage in ("4.7", "47"):
        from pipeline.checkpoint_utils import PIPELINE_VERSION
        from pipeline.stages.stage_4_7_serialize import evaluate_and_write_stage_4_7
        checkpoint, checkpoint_path = load_checkpoint(out_dir, prefix)
        if not force and not should_run_stage(checkpoint, "4.7"):
            print("Stage 4.7 skipped")
            return {"status": "SKIPPED", "stage": "4.7"}
        chunks_data = open(chunk_path, encoding="utf-8").read()
        res = evaluate_and_write_stage_4_7(chunks_data, out_dir, prefix, PIPELINE_VERSION)
        log_path = res["checklist_md"]
        mark_stage_complete(
            checkpoint,
            checkpoint_path,
            "4.7",
            output_file=os.path.basename(log_path),
            scattered_count=len(res["scattered"]),
            suspected_gap_count=len(res["suspected_gap"]),
            complete_count=len(res["complete_diseases"]),
            json_outputs=res["written_files"],
        )
        print(f"Stage 4.7 -> {log_path} | {len(res['complete_diseases'])} complete, {len(res['scattered'])} scattered, {len(res['suspected_gap'])} gap(s)")
        return {"status": "COMPLETED", "stage": "4.7", "complete": len(res["complete_diseases"]), "scattered": len(res["scattered"]), "gaps": len(res["suspected_gap"])}

    elif stage in ("5.2", "52"):
        checkpoint, checkpoint_path = load_checkpoint(out_dir, prefix)
        if not force and not should_run_stage(checkpoint, "5.2"):
            print("Stage 5.2 skipped")
            return {"status": "SKIPPED", "stage": "5.2"}
        scattered_json = os.path.join(out_dir, f"{prefix}_SCATTERED.json")
        count = 0
        if os.path.exists(scattered_json):
            try:
                s_data = json.load(open(scattered_json, encoding="utf-8"))
                count = len(s_data.get("data", {}))
            except Exception:
                pass
        mark_stage_complete(checkpoint, checkpoint_path, "5.2", scattered_candidates=count)
        print(f"Stage 5.2 -> Tier 2 synthesis evaluated ({count} scattered candidates)")
        return {"status": "COMPLETED", "stage": "5.2", "scattered_candidates": count}

    elif stage in ("5.3", "53"):
        checkpoint, checkpoint_path = load_checkpoint(out_dir, prefix)
        if not force and not should_run_stage(checkpoint, "5.3"):
            print("Stage 5.3 skipped")
            return {"status": "SKIPPED", "stage": "5.3"}
        gap_json = os.path.join(out_dir, f"{prefix}_SUSPECTED_GAP.json")
        count = 0
        if os.path.exists(gap_json):
            try:
                g_data = json.load(open(gap_json, encoding="utf-8"))
                count = len(g_data.get("data", {}))
            except Exception:
                pass
        mark_stage_complete(checkpoint, checkpoint_path, "5.3", suspected_gaps=count)
        print(f"Stage 5.3 -> Tier 3 gap stubs evaluated ({count} suspected gaps)")
        return {"status": "COMPLETED", "stage": "5.3", "suspected_gaps": count}

    elif stage in ("5.4", "54"):
        from pipeline.stages.stage_5_chunks import run_stage_5_4_autolink
        res = run_stage_5_4_autolink(chunk_path, out_dir, prefix)
        linked = res.get("linked_chunks", 0)
        print(f"Stage 5.4 -> Auto-linked {linked} chunks")
        return {"status": "COMPLETED", "stage": "5.4", "linked_chunks": linked}

    elif stage == "5":
        from pipeline.stages.stage_5_chunks import run_stage_5
        res = run_stage_5(chunk_path, out_dir, prefix, ch_num=info["ch_num"], ch_display=info["ch_display"])
        print(f"Stage 5 -> {res.get('rag_path')} ({res.get('l2_chunks')} L2 chunks)")
        return {"status": "COMPLETED", "stage": "5", "l2_chunks": res.get("l2_chunks"), "rag_path": res.get("rag_path")}

    elif stage == "6":
        from pipeline.stages.stage_6_validation import decide_checkpoint_action, run_stage_6
        checkpoint, checkpoint_path = load_checkpoint(out_dir, prefix)
        if not force and not should_run_stage(checkpoint, "6"):
            print("Stage 6 skipped")
            return {"status": "SKIPPED", "stage": "6"}
        text = open(rag_path, encoding="utf-8").read()
        gaps_path = os.path.join(out_dir, f"{prefix}_L1L2_CoverageGaps.md")
        gaps_text = open(gaps_path, encoding="utf-8").read() if os.path.exists(gaps_path) else None
        gate_path = os.path.join(out_dir, f"{prefix}_ClinicalFidelityGate.json")
        gate = json.load(open(gate_path, encoding="utf-8")) if os.path.exists(gate_path) else None
        result = run_stage_6(text, gaps_text, gate)
        log_path = os.path.join(out_dir, f"{prefix}_Stage6_Validation.md")
        s6_prov = format_markdown_provenance_header(source_path, "6")
        out = [s6_prov.rstrip(), "", f"# Stage 6 Validation — {prefix}", f"Chunks checked: {result['chunks_checked']}", f"VERDICT: {result['verdict']}"]
        if result["failures"]:
            out += ["", "FAILURES:"] + [f"  - {f}" for f in result["failures"]]

        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(out))
        action, metadata = decide_checkpoint_action(result)
        if action == "complete":
            mark_stage_complete(checkpoint, checkpoint_path, "6", output_file=os.path.basename(log_path), **metadata)
            print(f"Stage 6 -> {log_path} | {result['verdict']} | {len(result['failures'])} failure(s)")
            return {"status": "COMPLETED", "stage": "6", "verdict": result["verdict"], "failures": len(result["failures"])}
        else:
            mark_stage_blocked(checkpoint, checkpoint_path, "6", output_file=os.path.basename(log_path), **metadata)
            print(f"Stage 6 -> {log_path} | {result['verdict']} | {len(result['failures'])} failure(s)")
            return {"status": "BLOCKED", "stage": "6", "verdict": result["verdict"], "failures": len(result["failures"])}

    elif stage == "7":
        from pipeline.stages.stage_7_scorecard import run_stage_7
        res = run_stage_7(rep_path, rag_path, out_dir, prefix)
        score = res.get("overall_score")
        print(f"Stage 7 -> Overall Score: {score}")
        return {"status": "COMPLETED", "stage": "7", "overall_score": score}

    elif stage == "8":
        from pipeline.stages.trust_ledger import build_chapter_trust_record
        from pipeline.stages.source_lines_precision import build_precision_summary
        from scripts.maintenance.run_source_lines_precision import run as run_source_lines_precision
        checkpoint, checkpoint_path = load_checkpoint(out_dir, prefix)
        cli_args = argparse.Namespace(write=True, in_place=True, backup=False, dry_run=False)
        results = run_source_lines_precision(out_dir, prefix, args=cli_args)
        summary = build_precision_summary(results)
        record = build_chapter_trust_record(out_dir, os.path.basename(out_dir))
        mark_stage_complete(
            checkpoint,
            checkpoint_path,
            "8",
            output_file=f"{prefix}_SourceLinesPrecision.json",
            classification=record["classification"],
            trusted_for_downstream_use=record["trusted_for_downstream_use"],
            tested=summary["tested"],
            unresolved_count=summary["unresolved_count"],
        )
        print(f"Stage 8 -> Trust: {record['classification']} (trusted={record['trusted_for_downstream_use']}) | {summary['unresolved_count']} unresolved")
        return {"status": "COMPLETED", "stage": "8", "classification": record["classification"], "trusted": record["trusted_for_downstream_use"]}

    else:
        print(f"Unknown stage: {stage}")
        return {"status": "ERROR", "message": f"Unknown stage: {stage}"}


def execute_pipeline_auto(source_path: str, out_dir: str = None, prefix: str = None, force: bool = False, auto_adjudicate: bool = True, use_llm: bool = False):
    """Executes the full pipeline sequence 0 -> 8 automatically, halting on blocking gates."""
    source_path = os.path.abspath(source_path)
    if not out_dir or os.path.abspath(out_dir) == os.path.dirname(source_path):
        out_dir = os.path.join(os.path.dirname(source_path), "rag_pipeline_output")
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    # Sync assets directory from source chapter directory to out_dir/assets if present
    try:
        sync_chapter_assets(source_path, out_dir)
    except Exception as e:
        print(f"❌ Asset sync failed ({e}); figures would be missing from this chapter's outputs. Aborting.")
        return False

    info = derive_chapter_info(source_path)
    prefix = prefix or info["prefix"]

    # Stage 0 initialization
    execute_stage("0", source_path, out_dir, prefix, force=force)

    # Automated execution sequence
    sequence = ["1", "2", "3", "4a", "4b", "4.5", "4.5c", "4.5d", "4.5b", "4.6", "4.7", "5.2", "5.3", "5.4", "5", "6", "7", "8"]

    print("\n" + "=" * 60)
    print(f"🚀 Starting Automated Pipeline Chaining for: {prefix}")
    print(f"📂 Output Directory: {out_dir}")
    print(f"📑 Document Archetype: {info.get('doc_archetype', 'TEXTBOOK')}")
    print("=" * 60 + "\n")

    for stg in sequence:
        res = execute_stage(stg, source_path, out_dir, prefix, force=force, auto_adjudicate=auto_adjudicate, use_llm=use_llm)
        status = res.get("status")

        if status == "PENDING_MANUAL":
            print("\n" + "!" * 60)
            print(f"👉 INTERACTIVE GATE PAUSE: Stage {stg} requires candidate review.")
            print(f"Protocol: Read references/stage_{stg.replace('.', '_')}_protocol.md to adjudicate candidates.")
            print(f"Resume: Re-run 'python -m pipeline.run_stage --stage auto ...' after applying decisions.")
            print("!" * 60 + "\n")
            return False

        elif status == "BLOCKED":
            print("\n" + "!" * 60)
            print(f"❌ BLOCKING GATE TRIGGERED: Stage {stg} blocked execution.")
            print(f"Check the generated stage report in {out_dir} and apply necessary corrections.")
            print("!" * 60 + "\n")
            return False

        elif status in ("FAILED", "ERROR"):
            print("\n" + "!" * 60)
            print(f"❌ FATAL ERROR in Stage {stg}: {res.get('message', 'Stage execution failed')}")
            print("!" * 60 + "\n")
            return False

    # Authoritative trust = classify_trust() over all evidence (the Stage 8 checkpoint flag is a snapshot taken
    # before Stage 8 is marked complete, so it is False even for chapters that end up CORPUS_TESTING_READY).
    trusted = None
    try:
        from pipeline.stages import trust_ledger
        record = trust_ledger.build_chapter_trust_record(out_dir, os.path.basename(os.path.dirname(out_dir)))
        trusted = (record or {}).get("trusted_for_downstream_use")
        if record:
            print(f"Trust classification: {record.get('classification')}")
    except Exception as e:
        print(f"Trust classification unavailable: {e}")

    print("\n" + "=" * 60)
    if trusted is True:
        print(f"✅ CHAPTER PIPELINE COMPLETE (TRUSTED): {prefix}")
    else:
        print(f"⚠️ CHAPTER PIPELINE FINISHED BUT NOT TRUSTED FOR DOWNSTREAM USE: {prefix} (Stage 8 trusted={trusted})")
    print(f"📂 All outputs saved in: {out_dir}")
    print("=" * 60 + "\n")
    return True if trusted is True else "UNTRUSTED"


def main():
    parser = argparse.ArgumentParser(description="Davidson RAG Pipeline Stage CLI Runner")
    parser.add_argument("--stage", required=True, help="Stage key (e.g. 0, 1, 2, 3, 4a, 4b, 4.5, 4.5c, 4.5d, 4.6, 4.7, 5.4, 5, 6, 7, 8) or 'auto'/'chain'/'all' for automated chaining")
    parser.add_argument("--source", required=True, help="Path to markdown_inlined.md")
    parser.add_argument("--out", default=None, help="Path to chapter output directory (defaults to <source_dir>/rag_pipeline_output)")
    parser.add_argument("--prefix", default=None, help="Optional chapter prefix override")
    parser.add_argument("--force", action="store_true", help="Force execution even if checkpoint says complete")
    parser.add_argument("--auto-adjudicate", action="store_true", default=False, help="Automatically adjudicate Stage 4.6 using deterministic clinical rules if no Gemini API key is configured")
    parser.add_argument("--use-llm", action="store_true", default=False, help="Opt-in to external LLM API verification for Stage 4.6 (default: False for zero-token local execution)")

    args = parser.parse_args()
    stage_arg = args.stage.lower()

    source_path = os.path.abspath(args.source)
    out_dir = args.out
    if not out_dir or os.path.abspath(out_dir) == os.path.dirname(source_path):
        out_dir = os.path.join(os.path.dirname(source_path), "rag_pipeline_output")
    out_dir = os.path.abspath(out_dir)

    if stage_arg in ("auto", "chain", "all"):
        success = execute_pipeline_auto(source_path, out_dir, prefix=args.prefix, force=args.force, auto_adjudicate=True, use_llm=args.use_llm)
        if success == "UNTRUSTED":
            sys.exit(3)  # finished, but Stage 8 did not mark the chapter trusted
        if not success:
            sys.exit(1)
    else:
        res = execute_stage(stage_arg, source_path, out_dir, prefix=args.prefix, force=args.force, auto_adjudicate=args.auto_adjudicate, use_llm=args.use_llm)
        if res.get("status") in ("BLOCKED", "FAILED", "ERROR"):
            sys.exit(1)


if __name__ == "__main__":
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    main()