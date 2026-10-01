#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLINICAL PRECEPTOR CDSS ORCHESTRATOR (v1.1.0)
Universal Multi-Folder Autonomous Manufacturing Pipeline & 13-Modality Clinical Runtime Engine

Supports any physician-authored case series, clinical teaching archive, or medical preceptor corpus.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

__version__ = "1.1.0"
VERSION = "1.1.0"

DEFAULT_WORKSPACE = Path(r"D:\HABIJABI_FULL")

# ==============================================================================
# 0. WORKSPACE SCAFFOLDING & INITIALIZATION
# ==============================================================================
def init_workspace(workspace_dir: Path, clinician_name: str = "Clinician", series_name: str = "Clinical Cases"):
    print("=" * 80)
    print("🏗️  CLINICAL PRECEPTOR CDSS — WORKSPACE PRE-SCAFFOLDING (v1.1.0)")
    print(f"    Target Directory : {workspace_dir}")
    print(f"    Clinician / Series: {clinician_name} | {series_name}")
    print("=" * 80)

    directories = [
        workspace_dir / "00_CONTROL",
        workspace_dir / "01_RAW_SINGLEFILE",
        workspace_dir / "02_RAW_MEDIA",
        workspace_dir / "03_NORMALIZED_CORPUS" / "POSTS",
        workspace_dir / "03_NORMALIZED_CORPUS" / "COMMENTS",
        workspace_dir / "03_NORMALIZED_CORPUS" / "REPLIES",
        workspace_dir / "03_NORMALIZED_CORPUS" / "MEDIA_METADATA",
        workspace_dir / "03_NORMALIZED_CORPUS" / "THREADS",
        workspace_dir / "03_NORMALIZED_CORPUS" / "MARKDOWN",
        workspace_dir / "03_NORMALIZED_CORPUS" / "JSON",
        workspace_dir / "03_NORMALIZED_CORPUS" / "TABLES",
        workspace_dir / "03_NORMALIZED_CORPUS" / "CLINICAL_COMMENTS",
        workspace_dir / "03_NORMALIZED_CORPUS" / "ENGLISH_SYNTHESIS",
        workspace_dir / "04_PERSONA" / "ANALOGIES",
        workspace_dir / "04_PERSONA" / "CASE_FRAMING",
        workspace_dir / "04_PERSONA" / "CORRECTIONS",
        workspace_dir / "04_PERSONA" / "HEURISTICS",
        workspace_dir / "04_PERSONA" / "LANGUAGE_PATTERNS",
        workspace_dir / "04_PERSONA" / "OBSERVATIONS",
        workspace_dir / "04_PERSONA" / "PERSONA_EVIDENCE",
        workspace_dir / "04_PERSONA" / "PERSONA_SUMMARIES",
        workspace_dir / "04_PERSONA" / "REASONING_PATTERNS",
        workspace_dir / "04_PERSONA" / "RESPONSE_PATTERNS",
        workspace_dir / "04_PERSONA" / "TEACHING_PATTERNS",
        workspace_dir / "04_PERSONA" / "UNCERTAINTY_LANGUAGE",
        workspace_dir / "05_TEXTBOOK_BRIDGE" / "AGREEMENT",
        workspace_dir / "05_TEXTBOOK_BRIDGE" / "BRIDGE_TABLES",
        workspace_dir / "05_TEXTBOOK_BRIDGE" / "CONFLICT",
        workspace_dir / "05_TEXTBOOK_BRIDGE" / "TEXTBOOK_TO_CASES",
        workspace_dir / "05_TEXTBOOK_BRIDGE" / "CASES_TO_TEXTBOOK",
        workspace_dir / "05_TEXTBOOK_BRIDGE" / "UNMAPPED",
        workspace_dir / "05_TEXTBOOK_BRIDGE" / "UPDATE_REQUIRED",
        workspace_dir / "06_DIAGNOSTICS" / "MANUAL_REVIEW",
        workspace_dir / "07_AUDIT",
        workspace_dir / "08_EXPORTS" / "RAG",
        workspace_dir / "08_EXPORTS" / "CLAIMS",
        workspace_dir / "08_EXPORTS" / "PERSONA",
        workspace_dir / "08_EXPORTS" / "TABLES",
        workspace_dir / "08_EXPORTS" / "ENGLISH_CORPUS",
        workspace_dir / "08_EXPORTS" / "OSCE",
        workspace_dir / "08_EXPORTS" / "CURRICULUM",
        workspace_dir / "08_EXPORTS" / "GRAPH",
        workspace_dir / "08_EXPORTS" / "SBAR_HANDOVERS",
        workspace_dir / "08_EXPORTS" / "PATIENT_LEAFLETS",
        workspace_dir / "08_EXPORTS" / "ANKI",
        workspace_dir / "08_EXPORTS" / "PHARMACOVIGILANCE",
        workspace_dir / "99_BACKUP",
        workspace_dir / "raw html",
        workspace_dir / "tools",
    ]

    for d in directories:
        d.mkdir(parents=True, exist_ok=True)
    print(f"✅ Created {len(directories)} standardized directory partitions.")

    ctrl = workspace_dir / "00_CONTROL"
    claim_schema = ctrl / "claim_schema.md"
    if not claim_schema.exists():
        claim_schema.write_text(
            "# Clinical Claim Schema\n\n"
            "claim_id, record_id, source_segment_id, source_role, source_author, author_role, claim_text, "
            "claim_type, clinical_domain, disease, diagnostic_claim, treatment_claim, dose_claim, mechanism_claim, "
            "prognostic_claim, contraindication_claim, monitoring_claim, educational_claim, historical_context, "
            "source_timestamp, current_validity_status, authoritative_verification_status, evidence_class, textbook_bridge_id.\n\n"
            "Default validity statuses during extraction: current_validity_status=NOT_ASSESSED, authoritative_verification_status=NOT_VERIFIED.\n",
            encoding="utf-8"
        )

    norm_schema = ctrl / "normalized_schema.md"
    if not norm_schema.exists():
        norm_schema.write_text(
            "# Normalized Corpus Schema\n\n"
            "POST: record_id, post_id, series_number, variant, topic, author, source_url, alternate_urls, publication_timestamp, capture_timestamp, raw_text, normalized_text, reaction_count, comment_count_displayed, share_count_displayed, media_ids, raw_html_sha256, extraction_version.\n"
            "COMMENT: comment_id, record_id, parent_post_id, author, timestamp, raw_text, normalized_text, reaction_count, media_ids, reply_count_loaded, reply_count_displayed, thread_order, source_role=COMMENT.\n"
            "REPLY: reply_id, record_id, parent_post_id, parent_comment_id, author, timestamp, raw_text, normalized_text, reaction_count, media_ids, thread_order, source_role=REPLY.\n"
            "MEDIA: media_id, record_id, source_role, source_author, parent_post_id, media_type, original_filename, stored_filename, sha256, caption_text, surrounding_context, embedded_in_singlefile, separate_original_saved, ocr_status, visual_interpretation_status.\n",
            encoding="utf-8"
        )

    prov_ledger = ctrl / "provenance_ledger.csv"
    if not prov_ledger.exists():
        with prov_ledger.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["record_id", "primary_url", "singlefile_capture_path", "raw_html_sha256", "capture_timestamp", "extraction_status", "notes"])

    cap_tracker = ctrl / "capture_tracker.csv"
    if not cap_tracker.exists():
        with cap_tracker.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["record_id", "published_number", "topic", "capture_status", "inbound_filename", "verified_date"])

    manifest = ctrl / "manifest_template.csv"
    if not manifest.exists():
        with manifest.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["record_id", "published_number", "variant", "topic", "primary_url", "author", "raw_html_expected_filename"])

    print(f"✅ Generated baseline control registries and schemas in {ctrl}")
    print(f"\n📂 Workspace is 100% pre-scaffolded and ready!")
    print(f"👉 Drop raw SingleFile HTML captures into: {workspace_dir / 'raw html'}")
    print("=" * 80)

# ==============================================================================
# PIPELINE ENGINES
# ==============================================================================
def resolve_workspace(p: Optional[str]) -> Path:
    if p:
        return Path(p)
    if "CDSS_WORKSPACE" in os.environ:
        return Path(os.environ["CDSS_WORKSPACE"])
    return DEFAULT_WORKSPACE

def run_pipeline_stage(workspace: Path, stage: str):
    print("=" * 80)
    print(f"🚀 EXECUTING PIPELINE STAGE: [{stage.upper()}] on {workspace}")
    print("=" * 80)

    if not (workspace / "00_CONTROL").exists():
        print("Workspace not scaffolded. Running automatic initialization...")
        init_workspace(workspace)

    if stage in ["auto", "prune-comments"]:
        prune_script = workspace / "tools" / "prune_non_clinical_comments.py"
        if prune_script.exists():
            import runpy
            runpy.run_path(str(prune_script), run_name="__main__")

    if stage in ["auto", "english-synthesis"]:
        eng_script = workspace / "tools" / "generate_english_synthesis.py"
        if eng_script.exists():
            import runpy
            runpy.run_path(str(eng_script), run_name="__main__")

    if stage in ["auto", "claims"]:
        claims_script = workspace / "tools" / "expand_clinical_claims.py"
        if claims_script.exists():
            import runpy
            runpy.run_path(str(claims_script), run_name="__main__")

    if stage in ["auto", "bridge"]:
        bridge_script = workspace / "tools" / "build_davidson_bridge.py"
        if bridge_script.exists():
            import runpy
            runpy.run_path(str(bridge_script), run_name="__main__")

    if stage in ["auto", "extended-modalities"]:
        ext_script = workspace / "tools" / "generate_extended_modalities.py"
        skill_ext = Path(__file__).parent / "generate_extended_modalities.py"
        target_script = ext_script if ext_script.exists() else skill_ext
        if target_script.exists():
            import subprocess
            subprocess.run([sys.executable, str(target_script), "--workspace", str(workspace)])

    if stage in ["auto", "audits"]:
        audit_script = workspace / "tools" / "run_full_corpus_audits.py"
        if audit_script.exists():
            import runpy
            runpy.run_path(str(audit_script), run_name="__main__")

    print(f"\n✅ Pipeline Stage [{stage.upper()}] completed successfully.")
    print("=" * 80)

# ==============================================================================
# EXTENDED RUNTIME MODALITY HANDLERS (7 MODALITIES)
# ==============================================================================
def run_visual_spotter(workspace: Path, query: Optional[str]):
    spotter_file = workspace / "08_EXPORTS" / "OSCE" / "visual_spotters.jsonl"
    if not spotter_file.exists():
        print(f"Error: Visual spotter file not found at {spotter_file}. Run pipeline stage 'extended-modalities' first.")
        return

    stations = []
    with spotter_file.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                stations.append(json.loads(line))

    matched = None
    if query and query.lower() != "random":
        q = query.lower()
        for s in stations:
            if q in s["station_id"].lower() or q in s["record_id"].lower() or q in s["condition"].lower() or q in s["domain"].lower():
                matched = s
                break
    
    if not matched and stations:
        matched = random.choice(stations)

    if not matched:
        print("No OSCE visual spotters found.")
        return

    print("=" * 80)
    print(f"📸 CLINICAL OSCE VISUAL SPOTTER STATION: {matched['station_id']}")
    print("=" * 80)
    print(f"📁 Domain       : {matched['domain']}")
    print(f"🩺 Condition    : {matched['condition']}")
    print(f"🔬 Visual Type  : {matched['modality']}")
    print(f"🖼️  Image Path   : file:///{workspace}/{matched['image_uri']}\n")
    print("--- OSCE QUESTION ---")
    print(matched["question"])
    print("\n" + "-" * 40)
    print("🔑 MODEL ANSWER & DIAGNOSTIC KEY:")
    print("-" * 40)
    print(matched["answer_key"])
    if matched.get("pearls"):
        print(f"\n💡 Clinical Pearl: {matched['pearls']}")
    print("=" * 80)

def run_curriculum(workspace: Path, tier_filter: Optional[str]):
    tiers_csv = workspace / "03_NORMALIZED_CORPUS" / "TABLES" / "residency_curriculum_tiers.csv"
    if not tiers_csv.exists():
        print(f"Error: Curriculum file not found at {tiers_csv}. Run pipeline stage 'extended-modalities' first.")
        return

    with tiers_csv.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    tf = (tier_filter or "all").lower()
    target_tier = None
    if "1" in tf or "intern" in tf:
        target_tier = "Tier 1"
    elif "2" in tf or "mo" in tf or "gp" in tf:
        target_tier = "Tier 2"
    elif "3" in tf or "fcps" in tf or "mrcp" in tf or "md" in tf:
        target_tier = "Tier 3"

    filtered = [r for r in rows if r["curriculum_tier"] == target_tier] if target_tier else rows

    print("=" * 80)
    print(f"🎓 RESIDENCY PROGRESSION CURRICULUM: {target_tier if target_tier else 'ALL TIERS'} ({len(filtered)} cases)")
    print("=" * 80)

    t1_count = sum(1 for r in rows if r["curriculum_tier"] == "Tier 1")
    t2_count = sum(1 for r in rows if r["curriculum_tier"] == "Tier 2")
    t3_count = sum(1 for r in rows if r["curriculum_tier"] == "Tier 3")
    print(f"📊 Summary Breakdown: Tier 1 (Intern): {t1_count} | Tier 2 (MO/GP): {t2_count} | Tier 3 (FCPS/MRCP): {t3_count}\n")

    for r in filtered[:10]:
        print(f"• [{r['curriculum_tier']}] {r['record_id']}: {r['title']}")
        print(f"   Target   : {r['target_cadre']}")
        print(f"   Focus    : {r['core_competencies']}")
        print(f"   Davidson : {r['davidson_textbook_bridge']}\n")

    if len(filtered) > 10:
        print(f"... and {len(filtered) - 10} more cases in {tiers_csv}")
    print("=" * 80)

def run_causal_graph(workspace: Path, query: Optional[str]):
    graph_file = workspace / "08_EXPORTS" / "GRAPH" / "causal_knowledge_graph.jsonl"
    if not graph_file.exists():
        print(f"Error: Causal graph not found at {graph_file}. Run pipeline stage 'extended-modalities' first.")
        return

    triplets = []
    with graph_file.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                triplets.append(json.loads(line))

    q = (query or "").lower()
    matched = [t for t in triplets if q in t["subject_entity"].lower() or q in t["predicate"].lower() or q in t["object_entity"].lower() or q in t["clinical_domain"].lower()] if q else triplets

    print("=" * 80)
    print(f"🕸️  PATHO-PHYSIOLOGICAL CAUSAL KNOWLEDGE GRAPH: Query \"{query or 'ALL'}\" ({len(matched)} triplets)")
    print("=" * 80)

    for t in matched[:12]:
        print(f"• ({t['subject_entity']})")
        print(f"    ===[ {t['predicate']} ]===>")
        print(f"  ({t['object_entity']})")
        print(f"  [Domain: {t['clinical_domain']} | Record: {t['record_id']} | Type: {t['relation_type']}]\n")

    if len(matched) > 12:
        print(f"... and {len(matched) - 12} more triplets in {graph_file}")
    print("=" * 80)

def run_sbar(workspace: Path, query: Optional[str]):
    sbar_file = workspace / "08_EXPORTS" / "SBAR_HANDOVERS" / "ward_sbar_handover_cards.jsonl"
    if not sbar_file.exists():
        print(f"Error: SBAR file not found at {sbar_file}. Run pipeline stage 'extended-modalities' first.")
        return

    cards = []
    with sbar_file.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cards.append(json.loads(line))

    matched = None
    if query:
        q = query.lower()
        for c in cards:
            if q in c["condition"].lower() or q in c["record_id"].lower() or q in c["situation"].lower():
                matched = c
                break

    if not matched and cards:
        matched = cards[0]

    print("=" * 80)
    print(f"🚨 ACUTE ON-CALL SBAR WARD HANDOVER: {matched['condition']} ({matched['record_id']})")
    print("=" * 80)
    print(f"S — SITUATION:\n{matched['situation']}\n")
    print(f"B — BACKGROUND:\n{matched['background']}\n")
    print(f"A — ASSESSMENT:\n{matched['assessment']}\n")
    print(f"R — RECOMMENDATION:\n{matched['recommendation']}")
    print("=" * 80)

def run_patient_leaflet(workspace: Path, query: Optional[str]):
    leaflets_md = workspace / "08_EXPORTS" / "PATIENT_LEAFLETS" / "patient_counseling_leaflets_bengali.md"
    if not leaflets_md.exists():
        print(f"Error: Patient leaflets not found at {leaflets_md}. Run pipeline stage 'extended-modalities' first.")
        return

    content = leaflets_md.read_text(encoding="utf-8")
    sections = content.split("\n## ")

    matched = None
    if query:
        q = query.lower()
        for s in sections[1:]:
            if q in s.lower():
                matched = s
                break

    print("=" * 80)
    print("🗣️  রোগীবান্ধব স্বাস্থ্য সচেতনতা ও পরামর্শ পত্র (HABIJABI PATIENT LEAFLET)")
    print("=" * 80)
    if matched:
        print("## " + matched.strip())
    else:
        # Print first leaflet
        print("## " + sections[1].strip() if len(sections) > 1 else content)
    print("=" * 80)

def run_anki_deck(workspace: Path, query: Optional[str]):
    deck_tsv = workspace / "08_EXPORTS" / "ANKI" / "habijabi_high_yield_anki_deck.tsv"
    if not deck_tsv.exists():
        print(f"Error: Anki deck not found at {deck_tsv}. Run pipeline stage 'extended-modalities' first.")
        return

    cards = []
    with deck_tsv.open("r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)
        for r in reader:
            if r and len(r) >= 3:
                cards.append(r)

    q = (query or "").lower()
    matched = [c for c in cards if q in c[1].lower() or q in c[2].lower() or (len(c) > 3 and q in c[3].lower())] if q else cards

    print("=" * 80)
    print(f"🃏 ANKI SPACED-REPETITION DECK: \"{deck_tsv.name}\" ({len(cards)} total cards | {len(matched)} matching)")
    print(f"   Ready for direct import into Anki (Note Type: Cloze)")
    print("=" * 80)

    for c in matched[:5]:
        print(f"[{c[0]}]")
        print(f"Text  : {c[1]}")
        print(f"Source: {c[2]}")
        if len(c) > 3:
            print(f"Tags  : {c[3]}")
        print("-" * 40)

    if len(matched) > 5:
        print(f"... and {len(matched) - 5} more cards in {deck_tsv}")
    print("=" * 80)

def run_never_events(workspace: Path, query: Optional[str]):
    matrix_csv = workspace / "08_EXPORTS" / "PHARMACOVIGILANCE" / "never_events_toxic_drug_matrix.csv"
    if not matrix_csv.exists():
        print(f"Error: Matrix not found at {matrix_csv}. Run pipeline stage 'extended-modalities' first.")
        return

    with matrix_csv.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    q = (query or "").lower()
    matched = [r for r in rows if q in r["prescribed_agent"].lower() or q in r["forbidden_clinical_context"].lower() or q in r["lethal_adverse_consequence"].lower()] if q else rows

    print("=" * 80)
    print(f"⚠️  WARD PHARMACOVIGILANCE & 'NEVER-EVENTS' MATRIX ({len(matched)} alerts)")
    print("=" * 80)

    for r in matched:
        print(f"🛑 [{r['id']}] {r['prescribed_agent']}")
        print(f"   FORBIDDEN CONTEXT: {r['forbidden_clinical_context']}")
        print(f"   LETHAL CONSEQUENCE: {r['lethal_adverse_consequence']}")
        print(f"   PATHOPHYSIOLOGY  : {r['underlying_pathophysiology']}")
        print(f"   SAFE ALTERNATIVE : {r['safe_clinical_alternative']}")
        print(f"   CORPUS PRECEDENT : {r['record_id']}\n")

    print("=" * 80)

# ==============================================================================
# CLINICAL RUNTIME DISPATCHER
# ==============================================================================
def dispatch_runtime(workspace: Path, args: argparse.Namespace):
    # Check Extended 7 Modalities first
    if args.visual_spotter is not None:
        run_visual_spotter(workspace, args.visual_spotter)
        return
    if args.curriculum is not None:
        run_curriculum(workspace, args.curriculum)
        return
    if args.causal_graph is not None:
        run_causal_graph(workspace, args.causal_graph)
        return
    if args.sbar is not None:
        run_sbar(workspace, args.sbar)
        return
    if args.patient_leaflet is not None:
        run_patient_leaflet(workspace, args.patient_leaflet)
        return
    if args.anki_deck is not None:
        run_anki_deck(workspace, args.anki_deck)
        return
    if args.never_events is not None:
        run_never_events(workspace, args.never_events)
        return

    # Forward Core 6 Modalities to skill/navigator
    nav_script = workspace / "tools" / "habijabi_navigator.py"
    skill_nav = Path(r"C:\Users\User\.gemini\config\skills\kawsar-habijabi-cdss-navigator\scripts\habijabi_navigator.py")

    target_script = skill_nav if skill_nav.exists() else nav_script
    if not target_script.exists():
        print(f"Error: Could not locate clinical runtime engine at {target_script}")
        return

    import subprocess
    cmd = [sys.executable, str(target_script)]
    if args.preceptor:
        cmd.extend(["--preceptor", args.preceptor])
    elif args.exam_sba:
        cmd.extend(["--exam-sba", args.exam_sba])
    elif args.prescribing_safety:
        cmd.extend(["--prescribing-safety", args.prescribing_safety])
    elif args.federated:
        cmd.extend(["--federated", args.federated])
    elif args.tropical_calc:
        cmd.extend(["--tropical-calc", args.tropical_calc])
        if args.calc_args:
            cmd.append("--calc-args")
            cmd.extend(args.calc_args)
    elif args.ward_facilities:
        cmd.extend(["--ward-facilities", args.ward_facilities])
    elif args.search:
        cmd.extend(["--search", args.search, "--lang", args.lang, "--top_k", str(args.top_k)])

    subprocess.run(cmd)

# ==============================================================================
# MASTER CLI PARSER
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Clinical Preceptor CDSS Orchestrator (v1.1.0) — Universal Pipeline & 13-Modality Runtime Engine"
    )
    parser.add_argument("--workspace", type=str, default=None, help="Target clinical corpus workspace (default: D:\\HABIJABI_FULL)")
    parser.add_argument("--init-workspace", action="store_true", help="Pre-scaffold standardized CDSS architecture")
    parser.add_argument("--clinician-name", type=str, default="Clinician", help="Clinician name for initialization")
    parser.add_argument("--series-name", type=str, default="Clinical Cases", help="Series name for initialization")
    parser.add_argument("--pipeline", type=str, choices=["auto", "prune-comments", "english-synthesis", "claims", "bridge", "extended-modalities", "audits"], help="Run autonomous manufacturing pipeline stage")

    # Core 6 Modalities
    parser.add_argument("--preceptor", type=str, help="1. Socratic Ward Preceptor for a case")
    parser.add_argument("--exam-sba", type=str, nargs="?", const="random", help="2. Postgraduate SBA exam question")
    parser.add_argument("--prescribing-safety", type=str, help="3. Prescribing safety interceptor")
    parser.add_argument("--federated", type=str, help="4. Federated 4-Textbook cross-grounding")
    parser.add_argument("--tropical-calc", type=str, help="5. Tropical ward calculator (dengue, drop, mentzer)")
    parser.add_argument("--calc-args", type=str, nargs="*", default=[], help="Arguments for tropical calculator")
    parser.add_argument("--ward-facilities", type=str, help="6. Diagnostic laboratory facilities lookup")
    parser.add_argument("--search", type=str, help="6b. Hybrid bilingual semantic search")
    parser.add_argument("--lang", type=str, default="any", choices=["any", "en", "bn"], help="Language filter for search")
    parser.add_argument("--top_k", type=int, default=3, help="Number of search results")

    # Extended 7 Modalities
    parser.add_argument("--visual-spotter", type=str, nargs="?", const="random", help="7. Clinical OSCE Visual Spotter (image + diagnostic questions)")
    parser.add_argument("--curriculum", type=str, nargs="?", const="all", help="8. Residency Progression Curriculum (tier1, tier2, tier3, or all)")
    parser.add_argument("--causal-graph", type=str, nargs="?", const="all", help="9. GraphRAG Pathophysiological Causal Graph Triplets")
    parser.add_argument("--sbar", type=str, nargs="?", const="all", help="10. Acute On-Call SBAR Ward Handover Cards")
    parser.add_argument("--patient-leaflet", type=str, nargs="?", const="all", help="11. Patient Health Literacy & Counseling Leaflets (বাংলা)")
    parser.add_argument("--anki-deck", type=str, nargs="?", const="all", help="12. High-Yield Anki Spaced-Repetition Cloze Decks")
    parser.add_argument("--never-events", type=str, nargs="?", const="all", help="13. Ward Pharmacovigilance & 'Never-Events' Toxic Drug Matrix")

    args = parser.parse_args()
    workspace = resolve_workspace(args.workspace)

    if args.init_workspace:
        init_workspace(workspace, args.clinician_name, args.series_name)
    elif args.pipeline:
        run_pipeline_stage(workspace, args.pipeline)
    elif any([
        args.preceptor, args.exam_sba, args.prescribing_safety, args.federated,
        args.tropical_calc, args.ward_facilities, args.search,
        args.visual_spotter is not None, args.curriculum is not None,
        args.causal_graph is not None, args.sbar is not None,
        args.patient_leaflet is not None, args.anki_deck is not None,
        args.never_events is not None
    ]):
        dispatch_runtime(workspace, args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
