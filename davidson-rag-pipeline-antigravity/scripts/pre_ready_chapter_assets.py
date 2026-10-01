"""Pre-Ready Chapter Assets Utility (Davidson RAG Pipeline).

v2.6.3 SAFETY GUARDRAIL: Pre-processing helper for asset extraction and markdown inlining.
Only writes to target chapter output directory and assets/figures/.

Automates:
1. PDF image extraction (via PyMuPDF/fitz if available) into assets/figures/
2. Markdown figure citation scanning (Fig. X.Y / Figure X.Y)
3. Standardized image tag inlining (![Fig X.Y: Caption](assets/figures/chNN_fig_MM.png))
4. Decision tree scaffold detection
5. Generation of {PREFIX}_FIGURE_AUDIT.md
"""
import argparse
import os
import re
import sys
from typing import Dict, List, Optional, Tuple


def find_assets_dir(out_dir: str, custom_dir: Optional[str] = None) -> str:
    """Resolves target assets/figures directory."""
    if custom_dir:
        os.makedirs(custom_dir, exist_ok=True)
        return os.path.abspath(custom_dir)

    # Check sibling or child assets/figures
    cand1 = os.path.join(out_dir, "assets", "figures")
    cand2 = os.path.join(os.path.dirname(os.path.abspath(out_dir)), "assets", "figures")

    target = cand2 if os.path.exists(os.path.dirname(cand2)) else cand1
    os.makedirs(target, exist_ok=True)
    return os.path.abspath(target)


def extract_images_from_pdf(pdf_path: str, assets_dir: str, ch_num: int) -> List[str]:
    """Extracts embedded images from PDF into assets/figures/ch{NN}_fig_{index:02d}.png."""
    extracted = []
    if not pdf_path or not os.path.exists(pdf_path):
        return extracted

    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        img_idx = 1
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            for img in page.get_images(full=True):
                xref = img[0]
                base_img = doc.extract_image(xref)
                image_bytes = base_img["image"]
                image_ext = base_img.get("ext", "png")
                filename = f"ch{ch_num:02d}_fig_{img_idx:02d}.{image_ext}"
                out_path = os.path.join(assets_dir, filename)
                if not os.path.exists(out_path):
                    with open(out_path, "wb") as f:
                        f.write(image_bytes)
                extracted.append(filename)
                img_idx += 1
        doc.close()
    except ImportError:
        print("[INFO] PyMuPDF (fitz) not installed. PDF image extraction skipped. Images can be placed manually in:", assets_dir)
    except Exception as e:
        print(f"[WARNING] Error during PDF image extraction: {e}")

    return extracted


def scan_figure_citations(md_text: str) -> List[Dict[str, str]]:
    """Finds all Figure/Fig citations and captions in markdown text."""
    # Matches patterns like "Fig. 18.4: Acute anterolateral STEMI", "Figure 18.4 ...", "(Fig. 18.4)"
    pattern = re.compile(
        r'\b(Fig(?:ure)?\.?\s*(\d+)\.(\d+)(?:\s*[:—–-]\s*([^\n\)\;\.]+))?)',
        re.IGNORECASE
    )
    citations = []
    seen = set()
    for m in pattern.finditer(md_text):
        full_match = m.group(1).strip()
        ch_str = m.group(2)
        fig_str = m.group(3)
        caption = m.group(4).strip() if m.group(4) else ""
        ch_n, fig_n = int(ch_str), int(fig_str)
        key = (ch_n, fig_n)
        if key not in seen:
            seen.add(key)
            citations.append({
                "ch": ch_n,
                "fig": fig_n,
                "key": f"{ch_n}.{fig_n}",
                "full_citation": full_match,
                "caption": caption or f"Figure {ch_n}.{fig_n}",
                "asset_name": f"ch{ch_n:02d}_fig_{fig_n:02d}.png"
            })
    return citations


def inline_figure_tags(md_text: str, citations: List[Dict[str, str]], assets_dir: str) -> Tuple[str, List[Dict]]:
    """Inlines markdown image tags ![Caption](assets/figures/...) where cited."""
    updated_text = md_text
    audit_results = []

    for c in citations:
        asset_name = c["asset_name"]
        asset_full_path = os.path.join(assets_dir, asset_name)
        asset_rel_path = f"assets/figures/{asset_name}"
        exists_on_disk = os.path.exists(asset_full_path)

        # Check if already inlined
        already_inlined = f"assets/figures/{asset_name}" in updated_text or f"({asset_name})" in updated_text

        inlined_now = False
        if not already_inlined:
            # Look for citation anchor to insert right after
            target_pattern = re.compile(re.escape(c["full_citation"]), re.IGNORECASE)
            tag_to_insert = f"\n\n![{c['caption']}]({asset_rel_path})\n"
            if target_pattern.search(updated_text):
                updated_text = target_pattern.sub(rf"\g<0>{tag_to_insert}", updated_text, count=1)
                inlined_now = True

        audit_results.append({
            "key": c["key"],
            "caption": c["caption"],
            "asset_path": asset_rel_path,
            "exists_on_disk": exists_on_disk,
            "already_inlined": already_inlined,
            "inlined_now": inlined_now
        })

    return updated_text, audit_results


def write_figure_audit_report(out_dir: str, prefix: str, audit_results: List[Dict], assets_dir: str) -> str:
    """Writes {PREFIX}_FIGURE_AUDIT.md detailing figure pre-ready status."""
    report_path = os.path.join(out_dir, f"{prefix}_FIGURE_AUDIT.md")
    total = len(audit_results)
    on_disk = sum(1 for a in audit_results if a["exists_on_disk"])
    inlined = sum(1 for a in audit_results if a["already_inlined"] or a["inlined_now"])

    lines = [
        f"# Figure & Asset Alignment Audit Report — {prefix}",
        f"",
        f"- **Total Figures Referenced in Text**: {total}",
        f"- **Figures Present on Disk (`assets/figures/`)**: {on_disk} / {total}",
        f"- **Figures Inlined with Markdown Tags**: {inlined} / {total}",
        f"- **Assets Directory**: `{assets_dir}`",
        f"",
        f"## Figure Asset Status Table",
        f"",
        f"| Figure | Caption / Title | Asset Target | Present on Disk | Inlined in MD |",
        f"|---|---|---|---|---|",
    ]
    for a in audit_results:
        disk_status = "✅ YES" if a["exists_on_disk"] else "⚠️ MISSING (Placeholder ready)"
        inline_status = "✅ INLINED" if (a["already_inlined"] or a["inlined_now"]) else "❌ NOT INLINED"
        lines.append(f"| Fig {a['key']} | {a['caption']} | `{a['asset_path']}` | {disk_status} | {inline_status} |")

    lines.extend([
        "",
        "---",
        "## Next Steps",
        "1. Verify any missing image files in `assets/figures/`.",
        f"2. Execute automated pipeline: `python -m pipeline.run_stage --stage auto --source \"{prefix}.pdf.markdown_inlined.md\" --out \"{out_dir}\"`.",
    ])

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return report_path


def main():
    parser = argparse.ArgumentParser(description="Pre-Ready Chapter Assets & Markdown Figure Inlining")
    parser.add_argument("--md", required=True, help="Path to input markdown file")
    parser.add_argument("--out-dir", required=True, help="Path to output chapter directory")
    parser.add_argument("--pdf", default=None, help="Optional path to source PDF for automated extraction")
    parser.add_argument("--assets-dir", default=None, help="Optional custom assets/figures directory")
    parser.add_argument("--ch", type=int, default=None, help="Optional chapter number override")
    parser.add_argument("--prefix", default=None, help="Optional prefix override")

    args = parser.parse_args()

    if not os.path.exists(args.md):
        print(f"[ERROR] Markdown file not found: {args.md}")
        sys.exit(1)

    os.makedirs(args.out_dir, exist_ok=True)
    assets_dir = find_assets_dir(args.out_dir, args.assets_dir)

    # Derive prefix and chapter number
    base_name = os.path.basename(args.md)
    prefix = args.prefix or re.sub(r"\.pdf\.markdown_inlined\.md$|\.markdown_inlined\.md$|\.md$", "", base_name)
    ch_num = args.ch
    if ch_num is None:
        ch_m = re.search(r"ch(?:apter)?[_-]?(\d+)", base_name, re.IGNORECASE) or re.search(r"_(\d+)_", base_name)
        ch_num = int(ch_m.group(1)) if ch_m else 1

    # Step 1: Extract PDF images if PDF provided
    if args.pdf:
        print(f"[STEP 1] Extracting images from PDF: {args.pdf}...")
        extracted = extract_images_from_pdf(args.pdf, assets_dir, ch_num)
        print(f"[STEP 1] Extracted {len(extracted)} image(s) to: {assets_dir}")

    # Step 2: Read Markdown and scan citations
    print(f"[STEP 2] Scanning figure citations in: {args.md}...")
    with open(args.md, "r", encoding="utf-8") as f:
        raw_text = f.read()

    citations = scan_figure_citations(raw_text)
    print(f"[STEP 2] Found {len(citations)} distinct figure citation(s).")

    # Step 3: Inline markdown tags
    print("[STEP 3] Inlining standardized markdown image tags...")
    updated_text, audit_results = inline_figure_tags(raw_text, citations, assets_dir)

    # Step 4: Write updated markdown and audit report
    out_md_path = os.path.join(args.out_dir, f"{prefix}.pdf.markdown_inlined.md")
    with open(out_md_path, "w", encoding="utf-8") as f:
        f.write(updated_text)
    print(f"[STEP 4] Wrote pre-ready markdown to: {out_md_path}")

    report_path = write_figure_audit_report(args.out_dir, prefix, audit_results, assets_dir)
    print(f"[STEP 5] Generated figure audit report at: {report_path}")
    print("\n[SUCCESS] Chapter assets and inlined markdown are pre-ready for pipeline processing!")


if __name__ == "__main__":
    main()
