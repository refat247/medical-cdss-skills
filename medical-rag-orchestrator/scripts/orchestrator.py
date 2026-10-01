"""
Medical RAG Master Orchestrator (v1.4.0)
Autonomous pipeline chainer and lifecycle orchestrator across:
  0. cdss-unicode-mojibake-guard (Corpus encoding, UTF-8 normalization, ISMP safety)
  1. medical-book-split-ocr-organizer (PDF split & OCR downloads staging)
  2. davidson-ocr-preready (Markdown inlining & figure decoupling)
  3. davidson-rag-pipeline-antigravity (18-stage RAG chunking & gate validation)
  4. medical-index-rag-compiler (26-asset index suite & GraphRAG compilation)
  5. cdss-retrieval-packager (Pruning, relative path patching, and federated CLI)
  6. cdss-bridge-note-publisher (Cognitive Bridge Note synthesis & Word docx)

Usage:
  python orchestrator.py status --book-dir "D:\\01_Medical_Study\\SPLIT Pdfs\\Davidson_25_Split"
  python orchestrator.py organize --target-dir "D:\\01_Medical_Study\\SPLIT Pdfs\\Davidson_25_Split" --source-dir "C:\\Users\\User\\Downloads"
  python orchestrator.py preready --chapter-dir "D:\\path\\to\\ch_dir" [--skip-completed]
  python orchestrator.py rag --source "D:\\path\\to\\ch.markdown_inlined.md" [--skip-completed]
  python orchestrator.py index --book "Davidson's Principles and Practice of Medicine" --edition "25th Edition" --corpus "D:\\path" --index "D:\\path\\index.md"
  python orchestrator.py package --package-dir "D:\\01_Medical_Study\\CDSS_Retrieval_Package"
  python orchestrator.py auto --book-dir "D:\\01_Medical_Study\\SPLIT Pdfs\\Davidson_25_Split" [--process-chapters] [--skip-completed]
"""

__version__ = "1.4.0"

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Skills root = the folder that contains this skill (override with env CDSS_SKILLS_ROOT)
SKILLS_ROOT = Path(os.environ.get("CDSS_SKILLS_ROOT", str(Path(__file__).resolve().parents[2])))
DEFAULT_DOWNLOADS_DIR = os.environ.get("CDSS_DOWNLOADS_DIR", str(Path.home() / "Downloads"))
GUARD_SCRIPT = SKILLS_ROOT / "cdss-unicode-mojibake-guard" / "scripts" / "guard.py"
ORGANIZER_SCRIPT = SKILLS_ROOT / "medical-book-split-ocr-organizer" / "scripts" / "organizer.py"
PREREADY_DIR = SKILLS_ROOT / "davidson-ocr-preready"
RAG_DIR = SKILLS_ROOT / "davidson-rag-pipeline-antigravity"
INDEX_COMPILER_DIR = SKILLS_ROOT / "medical-index-rag-compiler"
PACKAGER_SCRIPT = SKILLS_ROOT / "cdss-retrieval-packager" / "scripts" / "packager.py"
BUMPER_SCRIPT = SKILLS_ROOT / "version-manager" / "scripts" / "bump_version.py"
BRIDGE_PUBLISHER_DIR = SKILLS_ROOT / "cdss-bridge-note-publisher"
BRIDGE_PUBLISHER_SCRIPT = BRIDGE_PUBLISHER_DIR / "scripts" / "synthesize_bridge_note.py"


def run_subcommand(cmd: List[str], cwd: Optional[Path] = None, extra_pythonpath: Optional[Path] = None) -> int:
    """Execute a subprocess command with enhanced environment paths."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    if extra_pythonpath:
        current_pypath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{extra_pythonpath}{os.pathsep}{current_pypath}" if current_pypath else str(extra_pythonpath)

    print(f"\n[RUNNING] {' '.join(cmd)}")
    if cwd:
        print(f"[CWD] {cwd}")

    proc = subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=env)
    return proc.returncode


# ----------------------------------------------------------------------
# 0. Chapter trust evaluation (single source of truth for "RAG READY")
# ----------------------------------------------------------------------
DONE_STATUSES = ("COMPLETE", "COMPLETED", "PASS", "SUCCESS")
BAD_STATUSES = ("BLOCKED", "FAIL", "FAILED", "ERROR")


def _is_side_copy(p: Path, root: Path) -> bool:
    """Backup / audit / verification-bundle copies inside a chapter folder are never the live output."""
    try:
        rel = str(p.relative_to(root)).lower()
    except ValueError:
        rel = p.name.lower()
    return any(k in rel for k in ("backup", "audit", "bundle"))


def _load_trust_classifier():
    """The pipeline's own classifier (davidson-rag-pipeline-antigravity trust_ledger) is the single source
    of truth for trust. Stage 8's checkpoint flag is a snapshot taken before Stage 8 completes and is NOT
    authoritative."""
    added = str(RAG_DIR) not in sys.path
    try:
        if added:
            sys.path.insert(0, str(RAG_DIR))
        from pipeline.stages.trust_ledger import build_chapter_trust_record
        return build_chapter_trust_record
    except Exception as e:  # pragma: no cover - reported to the user instead
        print(f"[WARN] Cannot load pipeline trust classifier from {RAG_DIR}: {e}", file=sys.stderr)
        return None
    finally:
        # never leave the pipeline folder on sys.path: its regular "scripts" package would shadow others
        if added and str(RAG_DIR) in sys.path:
            sys.path.remove(str(RAG_DIR))


TRUST_CLASSIFIER = None  # resolved lazily; tests may replace it


def _checkpoint_verdict(out_dir: Path) -> Dict[str, Any]:
    """Trust verdict for one RAG output folder, via the pipeline's classify_trust()."""
    global TRUST_CLASSIFIER
    if TRUST_CLASSIFIER is None:
        TRUST_CLASSIFIER = _load_trust_classifier() or (lambda *a, **k: "UNAVAILABLE")
    rec = TRUST_CLASSIFIER(str(out_dir), out_dir.parent.name)
    if rec == "UNAVAILABLE":
        return {"ready": False, "label": "RAG TRUST UNKNOWN (pipeline classifier unavailable)"}
    if not rec:
        return {"ready": False, "label": "RAG INCOMPLETE (NO CHECKPOINT)"}
    if rec.get("trusted_for_downstream_use") is True:
        return {"ready": True, "label": "RAG READY", "classification": rec.get("classification")}
    return {"ready": False, "label": f"RAG UNTRUSTED ({rec.get('classification')})",
            "classification": rec.get("classification"), "reasons": rec.get("reasons")}


def evaluate_chapter_trust(search_dirs: List[Path]) -> Dict[str, Any]:
    """Decides whether a chapter's RAG output is trusted for downstream use.

    Uses the pipeline's own classify_trust() (the logic behind CORPUS_TRUST_STATUS.md):
      - CORPUS_OUTPUT_PROTECTED.json is a mutation-safety marker only, never evidence of trust.
      - Trust is judged from the evidence in the SAME folder as the *_RAG_Optimised.md
        (checkpoint, Stage 6, Stage 4.5d gate, 4.6/4.7 reviews, Stage 8 precision).
      - When a chapter holds several output folders (v22 copies, *_extracted, *_candidate...), the canonical
        folder named exactly "rag_pipeline_output" (shallowest) decides; side copies are ignored.
    """
    search_dirs = [d for d in search_dirs if d and d.exists()]
    out_dirs = []
    for d in search_dirs:
        out_dirs.extend(p.parent for p in d.glob("**/*_RAG_Optimised.md") if not _is_side_copy(p, d))
    out_dirs = sorted(set(out_dirs), key=lambda p: (p.name != "rag_pipeline_output", len(p.parts)))
    if not out_dirs:
        return {"ready": False, "label": "RAG INCOMPLETE (NO RAG OUTPUT)"}
    verdict = _checkpoint_verdict(out_dirs[0])
    verdict["output_dir"] = str(out_dirs[0])
    return verdict


# ----------------------------------------------------------------------
# 1. Status & Inspection
# ----------------------------------------------------------------------
def audit_book_status(book_dir: Path) -> None:
    """Audits the pipeline progress of each section inside a book directory."""
    if not book_dir.exists():
        print(f"[ERROR] Target book directory does not exist: {book_dir}")
        return

    print(f"\n================================================================================")
    print(f" MEDICAL RAG PIPELINE STATUS AUDIT")
    print(f" Target Book: {book_dir.resolve()}")
    print(f"================================================================================")

    entries = sorted([p for p in book_dir.iterdir() if p.is_dir()])
    if not entries:
        print("[WARNING] No chapter directories found.")
        return

    table_rows = []
    for d in entries:
        name = d.name
        # Check Stage 0 (PDF / OCR)
        has_pdf = any(d.glob("*.pdf"))
        ocr_md_dir = d / "ocr markdown"
        has_ocr = ocr_md_dir.exists() and any(f for f in ocr_md_dir.iterdir() if not f.name.startswith("."))
        
        # Check Stage 1 (Inlined markdown)
        inlined_files = [f for f in d.glob("*markdown_inlined.md") if f.is_file() and f.stat().st_size > 0] or \
                        [f for f in d.glob("**/*markdown_inlined.md") if f.is_file() and f.stat().st_size > 0]
        has_inlined = bool(inlined_files)
        
        # Check Stage 2 (RAG Chunks & Optimized)
        has_chunks = any(d.glob("**/*_chunks.md"))
        has_rag_opt = any(d.glob("**/*_RAG_Optimised.md"))
        status_tag = "NOT STARTED"
        if has_rag_opt:
            status_tag = evaluate_chapter_trust([d])["label"]
        elif has_inlined:
            status_tag = "INLINED"
        elif has_ocr:
            status_tag = "OCR INGESTED"
        elif has_pdf:
            status_tag = "PDF ONLY"

        table_rows.append({
            "section": name[:45],
            "pdf": "YES" if has_pdf else "NO",
            "ocr": "YES" if has_ocr else "NO",
            "inlined": "YES" if has_inlined else "NO",
            "chunks": "YES" if has_chunks else "NO",
            "rag_opt": "YES" if has_rag_opt else "NO",
            "status": status_tag
        })

    print(f"{'Section / Chapter':<48} | {'PDF':<4} | {'OCR':<4} | {'INL':<4} | {'CHK':<4} | {'OPT':<4} | {'STATUS'}")
    print("-" * 92)
    for r in table_rows:
        print(f"{r['section']:<48} | {r['pdf']:<4} | {r['ocr']:<4} | {r['inlined']:<4} | {r['chunks']:<4} | {r['rag_opt']:<4} | {r['status']}")
    print("-" * 92)



# ----------------------------------------------------------------------
# 2. Stage Runners
# ----------------------------------------------------------------------
def cmd_organize(target_dir: str, source_dir: Optional[str] = None) -> int:
    cmd = [sys.executable, str(ORGANIZER_SCRIPT), "auto", "--target-dir", target_dir]
    if source_dir:
        cmd.extend(["--source-dir", source_dir])
    return run_subcommand(cmd)


def cmd_preready(source_dirs: List[str], skip_completed: bool = False) -> int:
    dirs_to_run = []
    for s in source_dirs:
        sp = Path(s)
        inlined_valid = [f for f in sp.glob("*markdown_inlined.md") if f.is_file() and f.stat().st_size > 0] or \
                        [f for f in sp.glob("**/*markdown_inlined.md") if f.is_file() and f.stat().st_size > 0]
        if skip_completed and inlined_valid:
            print(f"[SKIP] Chapter already has inlined markdown: {sp.name}")
            continue
        dirs_to_run.append(s)

    if not dirs_to_run:
        print("[SKIP] All chapter directories already have markdown_inlined.md. Nothing to do.")
        return 0

    cmd = [sys.executable, "-m", "preready.runner", "--source-dir"] + dirs_to_run
    return run_subcommand(cmd, cwd=PREREADY_DIR, extra_pythonpath=PREREADY_DIR)


def cmd_rag(source_path: str, out_dir: Optional[str] = None, skip_completed: bool = False) -> int:
    sp = Path(source_path)
    target_out = Path(out_dir) if out_dir else (sp.parent / "rag_pipeline_output")
    has_rag_opt = any(target_out.glob("*_RAG_Optimised.md")) or any(sp.parent.glob("**/*_RAG_Optimised.md"))
    trust = evaluate_chapter_trust([target_out, sp.parent])
    if skip_completed and has_rag_opt and trust["ready"]:
        print(f"[SKIP] Chapter is already verified RAG READY: {sp.parent.name}")
        return 0
    if skip_completed and has_rag_opt:
        print(f"[RERUN] {sp.parent.name}: {trust['label']} - resuming pipeline")

    cmd = [sys.executable, "-m", "pipeline.run_stage", "--stage", "auto", "--source", source_path]
    if out_dir:
        cmd.extend(["--out", out_dir])
    return run_subcommand(cmd, cwd=RAG_DIR, extra_pythonpath=RAG_DIR)


def cmd_index(book: str, edition: str, corpus: str, index: str, output: str) -> int:
    cmd = [
        sys.executable, "-m", "scripts.compiler",
        "--book", book,
        "--edition", edition,
        "--corpus", corpus,
        "--index", index,
        "--output", output
    ]
    return run_subcommand(cmd, cwd=INDEX_COMPILER_DIR, extra_pythonpath=INDEX_COMPILER_DIR)


def cmd_package(package_dir: str) -> int:
    cmd = [sys.executable, str(PACKAGER_SCRIPT), "auto", "--package-dir", package_dir]
    return run_subcommand(cmd)


def cmd_guard(target_dir: str, fix: bool = False, enforce_ismp: bool = True) -> int:
    action = "fix" if fix else "audit"
    cmd = [sys.executable, str(GUARD_SCRIPT), action, "--target-dir", target_dir]
    if enforce_ismp:
        cmd.append("--enforce-ismp")
    return run_subcommand(cmd)


def cmd_publish_note(topic: str, output_dir: str, note_id: Optional[str] = None) -> int:
    """Stage 6: Synthesizes a discrete Cognitive Bridge Note with figures & Word docx."""
    cmd = [
        sys.executable, str(BRIDGE_PUBLISHER_SCRIPT),
        "--topic", topic,
        "--output-dir", output_dir
    ]
    if note_id:
        cmd.extend(["--note-id", note_id])
    return run_subcommand(cmd, cwd=BRIDGE_PUBLISHER_DIR, extra_pythonpath=BRIDGE_PUBLISHER_DIR)


def cmd_publish_manifest(manifest_path: str, output_dir: str) -> int:
    """Stage 6 Multi-Topic: Reads a chapter topic manifest and builds all discrete topic bridge notes."""
    mpath = Path(manifest_path)
    if not mpath.exists():
        print(f"[ERROR] Topic manifest not found: {mpath}")
        return 1

    import json
    with open(mpath, "r", encoding="utf-8") as f:
        data = json.load(f)

    chapter = data.get("chapter", "Unknown")
    title = data.get("title", "Unknown")
    topics = data.get("topics", [])
    print(f"\n================================================================================")
    print(f" STAGE 6: EXECUTING CHAPTER MANIFEST")
    print(f" Chapter {chapter}: {title} ({len(topics)} discrete clinical entities)")
    print(f"================================================================================")

    failures = 0
    for idx, t in enumerate(topics, start=1):
        t_id = t.get("topic_id", f"{chapter}.{idx}")
        t_title = t.get("title", "")
        print(f"\n>>> [{idx}/{len(topics)}] Publishing Note {t_id}: {t_title}...")
        code = cmd_publish_note(topic=t_title, output_dir=output_dir, note_id=t_id)
        if code != 0:
            print(f"[ERROR] Note {t_id} finished with returncode {code}")
            failures += 1

    if failures > 0:
        print(f"\n[STAGE 6 ERROR] {failures} note(s) failed during manifest publishing.")
        return 1

    print("\n[STAGE 6 COMPLETE] All manifest topics processed successfully.")
    return 0


def cmd_verify_versions() -> int:
    """Verifies zero-drift version consistency across all pipeline skills via version-manager --suite."""
    print("\n================================================================================")
    print(" PIPELINE SUB-SKILLS ZERO-DRIFT VERSION AUDIT (VIA VERSION-MANAGER SUITE)")
    print("================================================================================")
    cmd = [sys.executable, str(BUMPER_SCRIPT), "--suite", str(SKILLS_ROOT), "--verify"]
    return run_subcommand(cmd)



# ----------------------------------------------------------------------
# 3. Main CLI Dispatcher
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Master RAG Orchestrator: Chains Ingestion -> Pre-ready -> RAG -> Index Compiler -> Packager."
    )
    subparsers = parser.add_subparsers(dest="command", help="Pipeline subcommand")

    # status
    p_status = subparsers.add_parser("status", help="Audit pipeline status of all sections in a book")
    p_status.add_argument("--book-dir", required=True, help="Directory containing split book chapter folders")

    # organize
    p_org = subparsers.add_parser("organize", help="Run medical-book-split-ocr-organizer")
    p_org.add_argument("--target-dir", required=True, help="Target split book directory")
    p_org.add_argument("--source-dir", default=DEFAULT_DOWNLOADS_DIR, help="Source folder with OCR downloads (env CDSS_DOWNLOADS_DIR)")

    # preready
    p_pre = subparsers.add_parser("preready", help="Run davidson-ocr-preready table inlining & figure decoupling")
    p_pre.add_argument("--chapter-dir", nargs="+", required=True, help="One or more chapter directories")
    p_pre.add_argument("--skip-completed", action="store_true", default=False, help="Skip chapters that already have markdown_inlined.md")

    # rag
    p_rag = subparsers.add_parser("rag", help="Run davidson-rag-pipeline-antigravity 18-stage RAG chain")
    p_rag.add_argument("--source", required=True, help="Path to markdown_inlined.md")
    p_rag.add_argument("--out", help="Output directory for rag_pipeline_output")
    p_rag.add_argument("--skip-completed", action="store_true", default=False, help="Skip chapters that already have RAG_Optimised.md")

    # index
    p_idx = subparsers.add_parser("index", help="Run medical-index-rag-compiler")
    p_idx.add_argument("--book", required=True, help="Textbook name (e.g. 'Davidson')")
    p_idx.add_argument("--edition", required=True, help="Edition (e.g. '25th Edition')")
    p_idx.add_argument("--corpus", required=True, help="Corpus root directory containing chapter RAG outputs")
    p_idx.add_argument("--index", required=True, help="Path to inlined back-of-book index markdown")
    p_idx.add_argument("--output", required=True, help="Output destination for Index intelligence assets")

    # package
    p_pkg = subparsers.add_parser("package", help="Run cdss-retrieval-packager")
    p_pkg.add_argument("--package-dir", required=True, help="Root path of CDSS_Retrieval_Package")

    # guard (Gate 0)
    p_guard = subparsers.add_parser("guard", help="Run Gate 0 Unicode and ISMP clinical encoding guard")
    p_guard.add_argument("--target-dir", required=True, help="Directory to audit or sanitize")
    p_guard.add_argument("--fix", action="store_true", help="Fix encoding issues in-place (default is audit only)")
    p_guard.add_argument("--enforce-ismp", action="store_true", default=True, help="Enforce FDA/ISMP safe abbreviations")

    # verify-versions
    subparsers.add_parser("verify-versions", help="Verify zero-drift version declarations across all pipeline skills")

    # publish-note (Stage 6)
    p_pub = subparsers.add_parser("publish-note", help="Stage 6: Synthesize a discrete Cognitive Bridge Note & Word document")
    p_pub.add_argument("--topic", required=True, help="Clinical topic name (e.g. 'Cardiac Murmurs & Auscultation')")
    p_pub.add_argument("--output-dir", required=True, help="Destination directory for published notes and Word docx")
    p_pub.add_argument("--note-id", help="Optional note identifier (e.g. '16.1')")

    # publish-manifest (Stage 6 Multi-Topic)
    p_man = subparsers.add_parser("publish-manifest", help="Stage 6: Build all discrete topic notes defined in a chapter manifest")
    p_man.add_argument("--manifest", required=True, help="Path to chapter_manifest.json")
    p_man.add_argument("--output-dir", required=True, help="Destination directory for published notes and Word docx")

    # auto
    p_auto = subparsers.add_parser("auto", help="Automate complete book build lifecycle")
    p_auto.add_argument("--book-dir", required=True, help="Root folder of book")
    p_auto.add_argument("--downloads-dir", default=DEFAULT_DOWNLOADS_DIR, help="Downloads staging folder (env CDSS_DOWNLOADS_DIR)")
    p_auto.add_argument("--process-chapters", action="store_true", default=False, help="Chain Stages 2 (preready) and 3 (RAG) across chapters")
    p_auto.add_argument("--skip-completed", action=argparse.BooleanOptionalAction, default=True, help="Skip chapters that are already trusted RAG READY (default: on; use --no-skip-completed to re-run)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "status":
        audit_book_status(Path(args.book_dir))
    elif args.command == "guard":
        code = cmd_guard(args.target_dir, fix=args.fix, enforce_ismp=args.enforce_ismp)
        sys.exit(code)
    elif args.command == "verify-versions":
        code = cmd_verify_versions()
        sys.exit(code)
    elif args.command == "publish-note":
        code = cmd_publish_note(args.topic, args.output_dir, note_id=args.note_id)
        sys.exit(code)
    elif args.command == "publish-manifest":
        code = cmd_publish_manifest(args.manifest, args.output_dir)
        sys.exit(code)
    elif args.command == "organize":
        code = cmd_organize(args.target_dir, args.source_dir)
        sys.exit(code)
    elif args.command == "preready":
        code = cmd_preready(args.chapter_dir, skip_completed=args.skip_completed)
        sys.exit(code)
    elif args.command == "rag":
        code = cmd_rag(args.source, args.out, skip_completed=args.skip_completed)
        sys.exit(code)
    elif args.command == "index":
        code = cmd_index(args.book, args.edition, args.corpus, args.index, args.output)
        sys.exit(code)
    elif args.command == "package":
        code = cmd_package(args.package_dir)
        sys.exit(code)
    elif args.command == "auto":
        bdir = Path(args.book_dir)
        print(f"[ORCHESTRATOR] Starting automated lifecycle for {bdir}...")
        # 1. Audit status first
        audit_book_status(bdir)
        # 2. Gate 0: Unicode & ISMP clinical encoding guard
        print("\n>>> GATE 0: Running Unicode & ISMP clinical encoding guard...")
        code = cmd_guard(args.book_dir, fix=True, enforce_ismp=True)
        if code != 0:
            print(f"[ERROR] Gate 0 Unicode guard failed with exit code {code}")
            sys.exit(code)

        # 3. Organize
        print("\n>>> STAGE 1: Organizing book directory and ingesting OCR...")
        code = cmd_organize(args.book_dir, args.downloads_dir)
        if code != 0:
            print(f"[ERROR] Stage 1 failed with exit code {code}")
            sys.exit(code)

        # 4. Optional chapter chaining (Stages 2 & 3)
        if args.process_chapters:
            print("\n>>> STAGE 2 & 3: Processing chapters (Pre-Ready Inlining & RAG)...")
            chapter_dirs = sorted([d for d in bdir.iterdir() if d.is_dir() and d.name != "Index"])
            for ch in chapter_dirs:
                has_rag_opt = any(ch.glob("**/*_RAG_Optimised.md"))
                inlined_files = sorted(f for f in ch.glob("**/*markdown_inlined.md") if f.is_file() and f.stat().st_size > 0)
                if has_rag_opt and args.skip_completed:
                    trust = evaluate_chapter_trust([ch])
                    if trust["ready"]:
                        print(f"\n[SKIP] Chapter {ch.name} is already RAG READY.")
                        continue
                    print(f"\n[RESUME] Chapter {ch.name}: {trust['label']}")
                if not inlined_files:
                    ocr_dir = ch / "ocr markdown"
                    if ocr_dir.exists() and any(f for f in ocr_dir.iterdir() if not f.name.startswith(".")):
                        print(f"\n[ORCHESTRATOR] Inlining tables & figures for {ch.name}...")
                        code = cmd_preready([str(ch)], skip_completed=args.skip_completed)
                        if code != 0:
                            print(f"[ERROR] Stage 2 (preready) failed for {ch.name} with exit code {code}")
                            sys.exit(code)
                        inlined_files = sorted(f for f in ch.glob("**/*markdown_inlined.md") if f.is_file() and f.stat().st_size > 0)
                if len(inlined_files) > 1:
                    print(f"[ERROR] {ch.name}: {len(inlined_files)} markdown_inlined.md files found; refusing to guess: {[f.name for f in inlined_files]}")
                    sys.exit(1)
                if inlined_files:
                    inlined_src = inlined_files[0]
                    print(f"\n[ORCHESTRATOR] Running 18-stage RAG for {ch.name} ({inlined_src.name})...")
                    code = cmd_rag(str(inlined_src), skip_completed=args.skip_completed)
                    if code == 3:
                        print(f"[WARN] {ch.name}: pipeline finished but Stage 8 did not mark it trusted; "
                              f"it will be excluded from indexing until reviewed/finalized.")
                        continue
                    if code != 0:
                        print(f"[ERROR] Stage 3 (RAG) failed for {ch.name} with exit code {code}")
                        sys.exit(code)

        # 5. Status after organization
        audit_book_status(bdir)
        print("\n[ORCHESTRATOR] Automated lifecycle step completed successfully.")


if __name__ == "__main__":
    main()
