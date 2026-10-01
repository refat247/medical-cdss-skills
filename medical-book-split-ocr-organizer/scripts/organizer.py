#!/usr/bin/env python3
"""
Medical Book Split & OCR Ingestion Organizer
Automates directory structure setup, source PDF organization, and OCR extraction routing
for medical textbooks and clinical practice guidelines.
"""

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path


def normalize_name(name: str) -> str:
    """Normalizes section/part names for flexible matching.
    Strips .pdf extension, converts underscores/hyphens to spaces, collapses whitespace,
    and converts to lowercase.
    """
    clean = re.sub(r"\.pdf$", "", name, flags=re.IGNORECASE)
    clean = re.sub(r"[_\-]+", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip().lower()
    return clean


def is_ignorable_dir(p: Path) -> bool:
    """Filters out hidden, cache, and audit report package directories."""
    name = p.name.lower()
    if name.startswith("."):
        return True
    if any(k in name for k in [
        "audit", "package", "__pycache__", "pytest_cache", "ocr markdown",
        "global_index", "verification_bundle", "bundle_build"
    ]):
        return True
    return False


def get_default_downloads_dir() -> str:
    """Determines user Downloads directory safely across Windows/Linux."""
    home = Path.home()
    downloads = home / "Downloads"
    return str(downloads) if downloads.exists() else str(home)


def cmd_init(target_dir: str) -> int:
    """Initializes book split directory:
    - Finds all top-level .pdf files
    - Creates section folder matching file's base name
    - Moves .pdf into section folder
    - Creates 'ocr markdown/' subfolder inside section folder
    """
    target = Path(target_dir).resolve()
    if not target.exists() or not target.is_dir():
        print(f"Error: Target directory does not exist or is not a directory: {target}", file=sys.stderr)
        return 1

    pdf_files = [f for f in target.iterdir() if f.is_file() and f.suffix.lower() == ".pdf"]
    
    # Auto-detect if target itself is an unorganized section folder (e.g. named *.pdf or contains markdown.md)
    if target.name.lower().endswith(".pdf") or (target / "markdown.md").exists():
        print(f"Detected individual section directory: {target.name}. Organizing into canonical layout...")
        return cmd_organize_section(str(target))

    if not pdf_files:
        print(f"No top-level PDF files found in {target}.")
        # Check if already organized into subdirectories
        subdirs = [d for d in target.iterdir() if d.is_dir() and not is_ignorable_dir(d)]
        if subdirs:
            print(f"Found {len(subdirs)} existing subdirectories. Ensuring 'ocr markdown/' folders exist...")
            created_ocr = 0
            for d in subdirs:
                ocr_dir = d / "ocr markdown"
                if not ocr_dir.exists():
                    ocr_dir.mkdir(parents=True, exist_ok=True)
                    created_ocr += 1
            print(f"Created {created_ocr} missing 'ocr markdown/' directories.")
        return 0

    print(f"Found {len(pdf_files)} PDF file(s) in {target} to initialize.")
    for pdf in sorted(pdf_files, key=lambda x: x.name):
        base_name = pdf.stem
        section_dir = target / base_name
        section_dir.mkdir(parents=True, exist_ok=True)

        ocr_dir = section_dir / "ocr markdown"
        ocr_dir.mkdir(parents=True, exist_ok=True)

        dest_pdf = section_dir / pdf.name
        if dest_pdf.exists():
            print(f"  [SKIP] Destination PDF already exists: {dest_pdf}")
        else:
            try:
                shutil.move(str(pdf), str(dest_pdf))
                print(f"  [OK] Initialized: {base_name} (moved PDF & created 'ocr markdown')")
            except Exception as e:
                print(f"  [ERROR] Failed moving {pdf.name}: {e}", file=sys.stderr)

    print("\nInitialization complete.")
    return 0


def cmd_ingest(target_dir: str, source_dir: str = None, force: bool = False) -> int:
    """Ingests OCR extraction folders from source_dir into corresponding section folders:
    - Scans source_dir for folders (typically named <Prefix>.pdf containing markdown.md/pages/)
    - Matches them flexibly against section folders in target_dir
    - Moves folder into <Section>/ocr markdown/<FolderName>
    - Cleans up empty extraction folders (e.g. ocr-playground-download-*)
    """
    target = Path(target_dir).resolve()
    if not target.exists() or not target.is_dir():
        print(f"Error: Target directory does not exist: {target}", file=sys.stderr)
        return 1

    src = Path(source_dir).resolve() if source_dir else Path(get_default_downloads_dir())
    if not src.exists() or not src.is_dir():
        print(f"Error: Source directory does not exist: {src}", file=sys.stderr)
        return 1

    print(f"Scanning target directory: {target}")
    print(f"Scanning source OCR path: {src}")

    # Discover candidate folders in source_dir
    # Check if src itself is an OCR directory (e.g. contains markdown.md or pages/)
    is_direct_ocr_folder = (src / "markdown.md").exists() or (src / "pages").exists()
    if is_direct_ocr_folder:
        source_items = [src]
    else:
        source_items = [d for d in src.iterdir() if d.is_dir()]

    # Build map of normalized section name -> section Path in target_dir
    section_dirs = [d for d in target.iterdir() if d.is_dir() and not is_ignorable_dir(d)]
    section_map = {}
    for d in section_dirs:
        norm = normalize_name(d.name)
        section_map[norm] = d

    # Also check if target itself is a section (contains PDFs or is an individual guideline section)
    target_pdfs = [f for f in target.iterdir() if f.is_file() and f.suffix.lower() == ".pdf"]
    target_norm = normalize_name(target.name)

    moved_count = 0
    skipped_count = 0
    unmatched_count = 0

    cleanup_candidates = []

    for item in sorted(source_items, key=lambda x: x.name):
        # Check for empty staging folders (e.g. ocr-playground-download-*)
        if item.name.lower().startswith("ocr-playground-download"):
            try:
                if not any(item.iterdir()):
                    cleanup_candidates.append(item)
            except Exception:
                pass
            continue

        norm = normalize_name(item.name)
        target_section = section_map.get(norm)

        if not target_section:
            # Fallback: check if the normalized item name is contained in or contains any section name
            for sec_norm, sec_path in section_map.items():
                if sec_norm == norm or (len(norm) > 10 and (norm in sec_norm or sec_norm in norm)):
                    target_section = sec_path
                    break

        # Check if target itself matches the item (single section mode)
        if not target_section:
            matched_pdf = False
            for pdf in target_pdfs:
                pdf_norm = normalize_name(pdf.name)
                if pdf_norm == norm or (len(norm) > 10 and (norm in pdf_norm or pdf_norm in norm)):
                    matched_pdf = True
                    break

            if matched_pdf or target_norm == norm or (len(norm) > 10 and (norm in target_norm or target_norm in norm)) or (is_direct_ocr_folder and (target_pdfs or not section_dirs)):
                target_section = target

        if not target_section:
            print(f"  [UNMATCHED] No section folder matching: '{item.name}'")
            unmatched_count += 1
            continue

        dest_ocr_parent = target_section / "ocr markdown"
        dest_ocr_parent.mkdir(parents=True, exist_ok=True)
        dest_item = dest_ocr_parent / item.name

        if dest_item.exists() and any(dest_item.iterdir() if dest_item.is_dir() else [1]):
            if not force:
                print(f"  [SKIP] Target already exists (use --force to overwrite): {dest_item}")
                skipped_count += 1
                continue
            else:
                print(f"  [OVERWRITE] Removing existing folder: {dest_item}")
                if dest_item.is_dir():
                    shutil.rmtree(dest_item)
                else:
                    dest_item.unlink()

        try:
            shutil.move(str(item), str(dest_item))
            print(f"  [MOVED] {item.name} -> {target_section.name}/ocr markdown/")
            moved_count += 1
        except Exception as e:
            print(f"  [ERROR] Failed to move {item.name}: {e}", file=sys.stderr)

    # Clean up empty staging folders
    for cleanup in cleanup_candidates:
        try:
            cleanup.rmdir()
            print(f"  [CLEANUP] Removed empty download folder: {cleanup.name}")
        except Exception:
            pass

    print(f"\nIngest Summary: Moved={moved_count}, Skipped={skipped_count}, Unmatched={unmatched_count}")
    return 0


def cmd_auto(target_dir: str, source_dir: str = None, force: bool = False) -> int:
    """Runs init followed by ingest."""
    print("=== Step 1: Initializing Book Split Directory ===")
    res1 = cmd_init(target_dir)
    if res1 != 0:
        return res1

    print("\n=== Step 2: Ingesting OCR Extractions ===")
    return cmd_ingest(target_dir, source_dir, force)


def cmd_status(target_dir: str) -> int:
    """Scans and reports audit status of each section in target_dir."""
    target = Path(target_dir).resolve()
    if not target.exists() or not target.is_dir():
        print(f"Error: Target directory does not exist: {target}", file=sys.stderr)
        return 1

    subdirs = sorted([d for d in target.iterdir() if d.is_dir() and not is_ignorable_dir(d)], key=lambda x: x.name)
    target_pdfs = [f for f in target.iterdir() if f.is_file() and f.suffix.lower() == ".pdf"]
    target_ocr = target / "ocr markdown"

    # If target itself is a single section (e.g. contains PDF directly or ocr markdown and no section subdirectories)
    if (target_pdfs or target_ocr.exists()) and not subdirs:
        print(f"\nAudit Report for Single Section: {target.name} ({target})")
        pdf_str = f"[YES] ({target_pdfs[0].name})" if target_pdfs else "[NO]"
        ocr_str = "[NO OCR]"
        if target_ocr.exists():
            ocr_items = [item for item in target_ocr.iterdir()]
            if ocr_items:
                ocr_str = f"[YES] ({len(ocr_items)} item(s): {', '.join(x.name for x in ocr_items)})"
        print(f"{'Source PDF':<12}: {pdf_str}")
        print(f"{'OCR Data':<12}: {ocr_str}\n")
        return 0

    if not subdirs:
        print(f"No section directories found in {target}.")
        uninit_pdfs = target_pdfs
        if uninit_pdfs:
            print(f"Found {len(uninit_pdfs)} uninitialized PDF files in root. Run 'init' to organize them.")
        return 0

    print(f"\nAudit Report for: {target}")
    print(f"{'Section Directory':<65} | {'Source PDF':<10} | {'OCR Data':<25}")
    print("-" * 105)

    has_pdf_count = 0
    has_ocr_count = 0

    for d in subdirs:
        # Check for PDF
        pdf_present = any(f.is_file() and f.suffix.lower() == ".pdf" for f in d.iterdir())
        if pdf_present:
            has_pdf_count += 1
            pdf_str = "[YES]"
        else:
            pdf_str = "[NO]"

        # Check for OCR markdown
        ocr_dir = d / "ocr markdown"
        ocr_str = "[NO OCR]"
        if ocr_dir.exists():
            ocr_items = [item for item in ocr_dir.iterdir()]
            if ocr_items:
                has_ocr_count += 1
                ocr_str = f"[YES] ({len(ocr_items)} item(s))"

        # Truncate long section names for clean console printing
        disp_name = (d.name[:62] + "...") if len(d.name) > 65 else d.name
        print(f"{disp_name:<65} | {pdf_str:<10} | {ocr_str:<25}")

    print("-" * 105)
    print(f"Total Sections: {len(subdirs)} | With PDF: {has_pdf_count}/{len(subdirs)} | With OCR: {has_ocr_count}/{len(subdirs)}\n")
    return 0


def cmd_organize_section(target_dir: str, force: bool = False, pdf_source_dir: str = None, move_pdf: bool = False) -> int:
    """Organizes an individual section directory into canonical layout:
    <Parent>/<CleanName>/
    ├── <CleanName>.pdf (source PDF)
    └── ocr markdown/
        └── <CleanName>.pdf/
            ├── markdown.md
            ├── pages/
            └── ...
    """
    target = Path(target_dir).resolve()
    if not target.exists() or not target.is_dir():
        print(f"Error: Target directory does not exist or is not a directory: {target}", file=sys.stderr)
        return 1

    clean_name = re.sub(r"\.pdf$", "", target.name, flags=re.IGNORECASE)
    parent = target.parent
    canonical_sec = parent / clean_name
    canonical_sec.mkdir(parents=True, exist_ok=True)

    ocr_dir = canonical_sec / "ocr markdown"
    ocr_dir.mkdir(parents=True, exist_ok=True)
    ocr_item = ocr_dir / (clean_name + ".pdf")

    print(f"Organizing section: {clean_name}")
    print(f"  Target Section Dir: {canonical_sec}")
    print(f"  OCR Workspace:      {ocr_item}")

    # 1. Locate and move/copy source PDF file
    pdf_candidates = [f for f in target.iterdir() if f.is_file() and f.suffix.lower() == ".pdf"]
    best_pdf = None
    source_is_internal = True

    if pdf_candidates:
        best_pdf = pdf_candidates[0]
        for p in pdf_candidates:
            if p.stem.lower() == clean_name.lower():
                best_pdf = p
                break
    else:
        # Check external candidate locations
        search_dirs = []
        if pdf_source_dir:
            search_dirs.append(Path(pdf_source_dir).resolve())
        if parent.parent.exists():
            search_dirs.append(parent.parent.resolve())
        if parent.exists():
            search_dirs.append(parent.resolve())

        norm_clean = normalize_name(clean_name)
        for sdir in search_dirs:
            if not sdir.is_dir():
                continue
            # Direct match
            direct_cand = sdir / (clean_name + ".pdf")
            if direct_cand.exists() and direct_cand.is_file():
                best_pdf = direct_cand
                source_is_internal = False
                break
            # Normalized match
            for cand in sdir.glob("*.pdf"):
                if normalize_name(cand.name) == norm_clean:
                    best_pdf = cand
                    source_is_internal = False
                    break
            if best_pdf:
                break

    dest_pdf = canonical_sec / (clean_name + ".pdf")
    if best_pdf and best_pdf.exists():
        if best_pdf.resolve() != dest_pdf.resolve():
            if dest_pdf.exists() and not force:
                print(f"  [SKIP] Destination PDF already exists: {dest_pdf.name}")
            else:
                if source_is_internal or move_pdf:
                    shutil.move(str(best_pdf), str(dest_pdf))
                    print(f"  [MOVED] Source PDF {best_pdf.name} -> {canonical_sec.name}/")
                else:
                    shutil.copy2(str(best_pdf), str(dest_pdf))
                    print(f"  [COPIED] Source PDF {best_pdf.name} -> {canonical_sec.name}/")
    else:
        if dest_pdf.exists():
            print(f"  [OK] Source PDF already present in section: {dest_pdf.name}")
        else:
            print(f"  [WARN] No source PDF found for {clean_name}")

    # 2. Move OCR files & directories into ocr_item
    ocr_item.mkdir(parents=True, exist_ok=True)

    items_to_move = [
        item for item in target.iterdir()
        if item.resolve() != canonical_sec.resolve() and item.resolve() != ocr_dir.resolve()
    ]

    for item in items_to_move:
        if target == canonical_sec and item.name == (clean_name + ".pdf"):
            continue
        if target == canonical_sec and item.name == "ocr markdown":
            continue

        dest_entry = ocr_item / item.name
        if dest_entry.exists():
            if force:
                if dest_entry.is_dir():
                    shutil.rmtree(dest_entry)
                else:
                    dest_entry.unlink()
                shutil.move(str(item), str(dest_entry))
                print(f"  [OVERWRITE] {item.name} -> ocr markdown/{ocr_item.name}/")
            else:
                print(f"  [SKIP] Already exists in OCR workspace: {dest_entry.name}")
        else:
            shutil.move(str(item), str(dest_entry))
            print(f"  [MOVED] {item.name} -> ocr markdown/{ocr_item.name}/")

    # 3. If target was named <Name>.pdf and is now empty, remove it
    if target.resolve() != canonical_sec.resolve():
        try:
            if not any(target.iterdir()):
                target.rmdir()
                print(f"  [CLEANUP] Removed old section directory: {target.name}")
        except Exception as e:
            print(f"  [NOTE] Could not remove old directory {target.name}: {e}", file=sys.stderr)

    # 4. Update CHECKPOINT.json if present
    rag_dir = ocr_item / "rag_pipeline_output"
    if rag_dir.exists():
        for ckpt_path in rag_dir.glob("*_CHECKPOINT.json"):
            try:
                with open(ckpt_path, "r", encoding="utf-8") as f:
                    ckpt_data = json.load(f)
                ch_info = ckpt_data.get("chapter_info", {})
                new_out = str(rag_dir.resolve())
                inlined_candidates = list(ocr_item.glob("*.markdown_inlined.md"))
                new_src = str(inlined_candidates[0].resolve()) if inlined_candidates else ch_info.get("source_path", "")

                ch_info["output_dir"] = new_out
                ch_info["source_path"] = new_src
                with open(ckpt_path, "w", encoding="utf-8") as f:
                    json.dump(ckpt_data, f, indent=2)
                print(f"  [UPDATED] RAG Checkpoint paths updated to: {ocr_item.name}")
            except Exception as e:
                print(f"  [NOTE] Could not update checkpoint {ckpt_path.name}: {e}", file=sys.stderr)

    print(f"\n[SUCCESS] Section '{clean_name}' organized into canonical layout!")
    return 0


def cmd_organize_book(target_dir: str, pdf_source_dir: str = None, force: bool = False, move_pdf: bool = False) -> int:
    """Batch-organizes all section directories within a book root directory into canonical layout:
    - Normalizes section folder names (removing trailing .pdf)
    - Incorporates matching source PDFs from pdf_source_dir into each section root
    - Relocates OCR outputs (markdown.md, pages/, assets/, rag_pipeline_output/) into ocr markdown/<Prefix>.pdf/
    - Updates RAG pipeline checkpoint JSON paths
    """
    target = Path(target_dir).resolve()
    if not target.exists() or not target.is_dir():
        print(f"Error: Target directory does not exist or is not a directory: {target}", file=sys.stderr)
        return 1

    subdirs = sorted([d for d in target.iterdir() if d.is_dir() and not is_ignorable_dir(d)], key=lambda x: x.name)
    if not subdirs:
        print(f"No candidate section directories found in {target}.")
        return 0

    print(f"=== Batch Organizing Book Sections in: {target} ===")
    print(f"Discovered {len(subdirs)} section candidates.")
    if pdf_source_dir:
        print(f"External PDF Source Directory: {pdf_source_dir}")

    success_count = 0
    fail_count = 0

    for d in subdirs:
        is_canonical_name = not d.name.lower().endswith(".pdf")
        has_local_pdf = any(f.is_file() and f.suffix.lower() == ".pdf" for f in d.iterdir())
        ocr_dir = d / "ocr markdown"
        has_ocr_markdown = ocr_dir.exists() and any(ocr_dir.iterdir())
        has_loose_ocr = (d / "markdown.md").exists() or (d / "pages").exists()

        if is_canonical_name and has_local_pdf and has_ocr_markdown and not has_loose_ocr:
            print(f"Section already canonical: {d.name} (skipping)")
            success_count += 1
            continue

        ret = cmd_organize_section(str(d), force=force, pdf_source_dir=pdf_source_dir, move_pdf=move_pdf)
        if ret == 0:
            success_count += 1
        else:
            fail_count += 1

    print(f"\nBatch Organization Finished: {success_count} succeeded, {fail_count} failed.")
    print("\nRunning post-organization status audit...\n")
    return cmd_status(str(target))


def main():
    parser = argparse.ArgumentParser(
        description="Medical Book Split & OCR Ingestion Organizer CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run organizer.py init --target-dir "D:\\01_Medical_Study\\Fcps\\cardiology_book\\Fuster & Hurst's The Heart_split"
  uv run organizer.py ingest --target-dir "D:\\01_Medical_Study\\SPLIT Pdfs\\harrison split" --source-dir "C:\\Users\\User\\Downloads"
  uv run organizer.py auto --target-dir "D:\\01_Medical_Study\\SPLIT Pdfs\\harrison split"
  uv run organizer.py status --target-dir "D:\\01_Medical_Study\\SPLIT Pdfs\\harrison split"
  uv run organizer.py organize-book --target-dir "D:\\davidson_25_true\\TRUE_MD_WITH_IMAGES(v2.23.0_made)" --pdf-source-dir "D:\\davidson_25_true"
  uv run organizer.py organize-section --target-dir "D:\\01_Medical_Study\\guideline\\...\\MyGuideline.pdf"
        """
    )

    subparsers = parser.add_subparsers(dest="command", required=True, help="Subcommand to execute")

    # init
    p_init = subparsers.add_parser("init", help="Initialize book split folders from top-level PDFs")
    p_init.add_argument("--target-dir", "--target", "-t", required=True, help="Target book split or section root directory")

    # ingest
    p_ingest = subparsers.add_parser("ingest", help="Ingest OCR folders into section ocr markdown directories")
    p_ingest.add_argument("--target-dir", "--target", "-t", required=True, help="Target book split or section directory")
    p_ingest.add_argument("--source-dir", "--source", "-s", default=None, help="Source directory with OCR extractions or direct OCR folder (default: Downloads)")
    p_ingest.add_argument("--force", "-f", action="store_true", help="Force overwrite existing OCR directories")

    # auto
    p_auto = subparsers.add_parser("auto", help="Execute both init and ingest in one pass")
    p_auto.add_argument("--target-dir", "--target", "-t", required=True, help="Target book split or section directory")
    p_auto.add_argument("--source-dir", "--source", "-s", default=None, help="Source directory with OCR extractions or direct OCR folder (default: Downloads)")
    p_auto.add_argument("--force", "-f", action="store_true", help="Force overwrite existing OCR directories")

    # status
    p_status = subparsers.add_parser("status", help="Audit section directories for PDF and OCR data completeness")
    p_status.add_argument("--target-dir", "--target", "-t", required=True, help="Target book split or section directory")

    # organize-book
    p_book = subparsers.add_parser("organize-book", aliases=["book", "organize-all", "batch-organize"], help="Batch organize all section directories in a book root directory")
    p_book.add_argument("--target-dir", "--target", "-t", required=True, help="Target book root directory containing section folders")
    p_book.add_argument("--pdf-source-dir", "--pdf-dir", "-p", default=None, help="Optional external directory containing source split PDFs to incorporate")
    p_book.add_argument("--force", "-f", action="store_true", help="Force overwrite/merge if target exists")
    p_book.add_argument("--move-pdf", "-m", action="store_true", help="Move source PDFs instead of copying them from pdf-source-dir")

    # organize-section
    p_sec = subparsers.add_parser("organize-section", aliases=["section"], help="Organize an individual section directory into canonical layout")
    p_sec.add_argument("--target-dir", "--target", "-t", required=True, help="Target section directory to organize")
    p_sec.add_argument("--pdf-source-dir", "--pdf-dir", "-p", default=None, help="Optional external directory containing source split PDFs")
    p_sec.add_argument("--force", "-f", action="store_true", help="Force overwrite/merge if target exists")
    p_sec.add_argument("--move-pdf", "-m", action="store_true", help="Move source PDF instead of copying it from pdf-source-dir")

    args = parser.parse_args()

    if args.command == "init":
        sys.exit(cmd_init(args.target_dir))
    elif args.command == "ingest":
        sys.exit(cmd_ingest(args.target_dir, args.source_dir, args.force))
    elif args.command == "auto":
        sys.exit(cmd_auto(args.target_dir, args.source_dir, args.force))
    elif args.command == "status":
        sys.exit(cmd_status(args.target_dir))
    elif args.command in ("organize-book", "book", "organize-all", "batch-organize"):
        sys.exit(cmd_organize_book(args.target_dir, args.pdf_source_dir, args.force, args.move_pdf))
    elif args.command in ("organize-section", "section"):
        sys.exit(cmd_organize_section(args.target_dir, args.force, args.pdf_source_dir, args.move_pdf))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
