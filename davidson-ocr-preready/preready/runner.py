"""Unified Runner CLI for Davidson OCR Pre-Ready Pipeline .

v2.6.3 SAFETY GUARDRAIL: Pre-processing helper for asset extraction and markdown inlining.
Only writes to target chapter output directory and assets/figures/.
"""
import argparse
import os
import re
import sys

from preready.table_inliner import find_table_files, inline_tables
from preready.image_normalizer import find_image_files, normalize_images
from preready.header_normalizer import clean_ocr_running_headers, normalize_heading_hierarchy
from preready.auditor import _format_provenance_header, write_audit_reports



_GUIDELINE_TOKENS = frozenset({"guideline", "guidelines", "consensus", "kdigo", "ada", "esc", "nice", "who"})


def detect_document_archetype(source_dir: str) -> str:
    """Detects whether the input is a textbook chapter or a clinical guideline/monograph.
    Whole-token match on the folder name: the old substring test ("ada_", "nice_", "who_") classified
    'canada_...' and 'venice_...' as guidelines."""
    base = os.path.basename(os.path.abspath(source_dir)).lower()
    tokens = [x for x in re.split(r"[^a-z0-9]+", base) if x]
    if any(tok in _GUIDELINE_TOKENS for tok in tokens) or "standards_of_care" in base.replace("-", "_").replace(" ", "_"):
        return "GUIDELINE"
    return "TEXTBOOK"


ROMAN_MAP = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
    "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10,
    "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15,
    "XVI": 16, "XVII": 17, "XVIII": 18, "XIX": 19, "XX": 20
}


def resolve_chapter_number(source_dir: str, ch_arg: int = None) -> int:
    """Extracts chapter integer from folder name or argument.
    
    Guaranteed to ignore 4-digit publication years (1900-2099) and defaults
    guideline monographs to chapter 1. Supports Roman numerals for sections/parts.
    Prioritizes Part numbers over edition numbers for multi-part textbooks like Harrison.
    """
    if ch_arg is not None:
        return ch_arg
    base = os.path.basename(os.path.abspath(source_dir))
    m_harrison = re.search(r"Harrison[_-]\d+[_-]PART[_\-\s]*(\d+)", base, re.IGNORECASE)
    if m_harrison:
        return int(m_harrison.group(1))
    m_part = re.search(r"(?:^|[_\-\s])(?:part|section|sec)[_\-\s]+(\d+)(?:[_\-\s]|$)", base, re.IGNORECASE)
    if m_part:
        return int(m_part.group(1))
    m_davidson = re.search(r"Davidson[_-]\d+[_-](\d+)", base, re.IGNORECASE)
    if m_davidson:
        return int(m_davidson.group(1))
    m_roman = re.search(r"(?:^|[_\-\s])(?:section|sec|part|ch(?:apter)?)[_\-\s]+([IVXLCDM]+)(?:[_\-\s]|$)", base, re.IGNORECASE)
    if m_roman and m_roman.group(1).upper() in ROMAN_MAP:
        return ROMAN_MAP[m_roman.group(1).upper()]
    m = re.search(r"ch(?:apter)?[_-]?(\d+)", base, re.IGNORECASE)
    if m:
        return int(m.group(1))
    # Match isolated chapter digits that are not 4-digit publication years
    m_num = re.search(r"(?:^|[_\-\s])(?!19\d\d|20\d\d)(\d{1,3})(?:[_\-\s]|$)", base)
    if m_num:
        return int(m_num.group(1))
    return 1


def resolve_prefix(source_dir: str, prefix_arg: str = None) -> str:
    """Derives canonical prefix from source directory name."""
    if prefix_arg:
        return prefix_arg
    base = os.path.basename(os.path.abspath(source_dir))
    clean = re.sub(r"\.pdf$|\.md$", "", base)
    m_harrison = re.search(r"Harrison[_-](\d+)[_-]PART[_\-\s]*(\d+)[_\-\s]*(.*)", clean, re.IGNORECASE)
    if m_harrison:
        ed = m_harrison.group(1)
        part_num = int(m_harrison.group(2))
        part_slug = re.sub(r"\s+", "_", m_harrison.group(3).strip("_-"))
        return f"Harrison_{ed}_Part{part_num:02d}_{part_slug}" if part_slug else f"Harrison_{ed}_Part{part_num:02d}"
    # Replace spaces with underscores
    return re.sub(r"\s+", "_", clean)


def expand_source_dirs(source_dirs: list) -> list:
    """Expands root directories containing chapter folders into a list of chapter folders."""
    expanded = []
    for s_dir in source_dirs:
        if not os.path.exists(s_dir):
            expanded.append(s_dir)
            continue
        if os.path.exists(os.path.join(s_dir, "markdown.md")):
            expanded.append(s_dir)
        else:
            discovered = []
            for root, dirs, files in os.walk(s_dir):
                parts = root.replace("\\", "/").split("/")
                if "pages" in parts:
                    continue
                if "markdown.md" in files:
                    base_name = os.path.basename(root).lower()
                    parent_name = os.path.basename(os.path.dirname(root)).lower()
                    if base_name == "index.pdf" or parent_name == "index":
                        continue
                    discovered.append(root)
            if discovered:
                discovered.sort()
                expanded.extend(discovered)
            else:
                expanded.append(s_dir)
    return expanded


def run_preready(
    source_dir: str,
    out_dir: str = None,
    assets_dir: str = None,
    ch_num: int = None,
    prefix: str = None
) -> dict:
    """Main execution function for converting raw OCR output into canonical markdown_inlined.md.
    
    If out_dir is not provided, defaults to source_dir (in-place generation inside corresponding input folder).
    """
    if not os.path.exists(source_dir):
        raise FileNotFoundError(f"Source OCR directory not found: {source_dir}")

    raw_md_path = os.path.join(source_dir, "markdown.md")
    if not os.path.exists(raw_md_path):
        raise FileNotFoundError(f"markdown.md not found in source directory: {source_dir}")

    if not out_dir:
        out_dir = source_dir

    os.makedirs(out_dir, exist_ok=True)
    archetype = detect_document_archetype(source_dir)
    ch = resolve_chapter_number(source_dir, ch_num)
    pfx = resolve_prefix(source_dir, prefix)

    if not assets_dir:
        assets_dir = os.path.join(out_dir, "assets", "figures")
    os.makedirs(assets_dir, exist_ok=True)

    print(f"[1/5] Reading raw OCR markdown from: {raw_md_path}")
    print(f"      Document Archetype: {archetype} (Chapter: {ch}, Prefix: {pfx})")
    with open(raw_md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    print("[2/5] Locating and inlining markdown tables from pages/...")
    table_map = find_table_files(source_dir)
    inlined_text, table_audits = inline_tables(md_text, table_map)
    print(f"      Inlined {sum(1 for t in table_audits if t['status'] == 'INLINED')} / {len(table_audits)} table(s).")

    print(f"[3/5] Decoupling figure images to: {assets_dir}...")
    image_map = find_image_files(source_dir)
    normalized_text, image_audits = normalize_images(inlined_text, image_map, assets_dir, ch)
    print(f"      Decoupled & linked {sum(1 for img in image_audits if img['copied'])} / {len(image_audits)} image(s).")

    print("[4/5] Normalizing heading hierarchy and stripping OCR running headers...")
    clean_text = clean_ocr_running_headers(normalized_text)
    final_text = normalize_heading_hierarchy(clean_text)

    # Prepend standardized provenance header
    prov_header = _format_provenance_header(raw_md_path)
    final_text_with_prov = prov_header + final_text

    # Sanitize and normalize Unicode (NFC, safe ligatures, strip zero-width artifacts, repair mojibake)
    import unicodedata
    final_text_with_prov = unicodedata.normalize("NFC", final_text_with_prov)
    ligature_map = {
        "\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl",
        "\ufb03": "ffi", "\ufb04": "ffl", "\ufb05": "ft", "\ufb06": "st",
    }
    for lig, rep in ligature_map.items():
        if lig in final_text_with_prov:
            final_text_with_prov = final_text_with_prov.replace(lig, rep)

    final_text_with_prov = final_text_with_prov.replace("\ufeff", "").replace("\u200b", "").replace("\u00ad", "")
    final_text_with_prov = final_text_with_prov.replace("â‰¥", ">=").replace("â‰¤", "<=").replace("Â±", "+/-")

    # Write output canonical file atomically via temporary swap file
    canonical_output_path = os.path.join(out_dir, f"{pfx}.pdf.markdown_inlined.md")
    tmp_output_path = canonical_output_path + ".tmp"
    with open(tmp_output_path, "w", encoding="utf-8") as f:
        f.write(final_text_with_prov)
    os.replace(tmp_output_path, canonical_output_path)
    print(f"      Wrote canonical inlined markdown to: {canonical_output_path}")

    print("[5/5] Generating audit reports...")
    tbl_rep, fig_rep, master_rep = write_audit_reports(out_dir, pfx, table_audits, image_audits, assets_dir, source_dir=source_dir)
    print(f"      Wrote master audit report to: {master_rep}")

    return {
        "status": "SUCCESS" if all(t["status"] == "INLINED" for t in table_audits)
                  and all(i["copied"] for i in image_audits) else "PARTIAL",
        "output_file": canonical_output_path,
        "tables_inlined": len(table_audits),
        "figures_decoupled": len(image_audits),
        "assets_dir": assets_dir,
        "master_report": master_rep
    }


def main():
    parser = argparse.ArgumentParser(description="Davidson OCR Pre-Ready Pipeline Runner")
    parser.add_argument("--source-dir", "-s", nargs="+", required=True, help="Path(s) to raw OCR chapter directory (containing markdown.md and pages/)")
    parser.add_argument("--out-dir", "-o", default=None, help="Optional destination directory (defaults to corresponding input folder)")
    parser.add_argument("--assets-dir", default=None, help="Optional custom assets/figures directory (defaults to assets/figures in output folder)")
    parser.add_argument("--ch", type=int, default=None, help="Optional chapter number override")
    parser.add_argument("--prefix", default=None, help="Optional chapter prefix override")

    args = parser.parse_args()
    raw_source_dirs = args.source_dir if isinstance(args.source_dir, list) else [args.source_dir]
    source_dirs = expand_source_dirs(raw_source_dirs)
    results = []
    has_error = False
    has_partial = False

    print(f"Discovered {len(source_dirs)} chapter folder(s) to process.")

    for s_dir in source_dirs:
        try:
            print(f"\n=======================================================")
            print(f"Processing OCR Chapter: {s_dir}")
            print(f"=======================================================")
            ch_override = args.ch if len(source_dirs) == 1 else None
            pfx_override = args.prefix if len(source_dirs) == 1 else None

            res = run_preready(
                source_dir=s_dir,
                out_dir=args.out_dir,
                assets_dir=args.assets_dir,
                ch_num=ch_override,
                prefix=pfx_override
            )
            if res["status"] == "PARTIAL":
                print("\n[PARTIAL] Pre-ready finished but some tables/figures were not resolved; see the audit reports.",
                      file=sys.stderr)
                has_partial = True
            else:
                print("\n[SUCCESS] Pre-ready pipeline completed cleanly!")
            print(f"Ready for RAG pipeline: {res['output_file']}")
            results.append(res)
        except Exception as e:
            print(f"\n[ERROR] Pre-ready pipeline failed for '{s_dir}': {e}", file=sys.stderr)
            has_error = True

    if has_error:
        sys.exit(1)
    if has_partial:
        sys.exit(3)


if __name__ == "__main__":
    main()
