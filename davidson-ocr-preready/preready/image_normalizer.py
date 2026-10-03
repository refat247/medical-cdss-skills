"""Image Normalizer & Decoupled Asset Extractor for Davidson OCR Pre-Ready Pipeline."""
import filecmp
import glob
import os
import re
import shutil
from typing import Dict, List, Optional, Tuple


def find_image_files(source_dir: str) -> Dict[str, str]:
    """Scans pages/page-*/ subdirectories and maps image filename to absolute path."""
    image_map = {}
    pattern = os.path.join(source_dir, "**", "img-*.*")
    for path in glob.glob(pattern, recursive=True):
        filename = os.path.basename(path)
        image_map[filename] = os.path.abspath(path)
    return image_map


def _scan_nearby_caption(clean_lines: List[str], line_idx: int) -> Tuple[Optional[int], Optional[int], Optional[str]]:
    """Scans forward (up to 30 lines) and backward (up to 5 lines) for a Figure X.Y caption."""
    # 1. Forward scan (e.g. caption after footnotes/notes)
    for k in range(line_idx + 1, min(len(clean_lines), line_idx + 30)):
        lk = clean_lines[k].strip()
        if not lk:
            continue
        if re.search(r'!\[[^\]]*\]\(img-\d+\.[a-zA-Z0-9]+\)', lk):
            break
        if re.match(r'^#{1,2}\s+[A-Z0-9]', lk) and not lk.startswith('###') and 'GLP-1' not in lk:
            break
        m_fig = re.match(r'^(?:\*{1,2}|#{1,4}\s*)?Fig(?:ure)?\.?\s*(\d+)(?:[\.\-–—](\d+))?(?:\s*[:—–-]?\s*(.*))?', lk, re.I)
        if m_fig:
            fig_ch = int(m_fig.group(1)) if m_fig.group(2) is not None else None
            fig_num = int(m_fig.group(2)) if m_fig.group(2) is not None else int(m_fig.group(1))
            cap_text = m_fig.group(3).strip() if m_fig.group(3) else lk
            cap_text = cap_text.strip('*_ ').strip()
            return fig_ch, fig_num, cap_text

    return None, None, None


def normalize_images(
    md_text: str,
    image_map: Dict[str, str],
    assets_dir: str,
    ch_num: int
) -> Tuple[str, List[Dict]]:
    """Copies images to assets/figures/ and replaces placeholders with standardized tags."""
    import bisect
    os.makedirs(assets_dir, exist_ok=True)
    audit_results = []
    updated_text = md_text

    # Pattern matches:
    # ![img-0.jpeg](img-0.jpeg)
    # followed optionally by: Fig. 1.1 Caption text...
    img_placeholder_re = re.compile(
        r'!\[(?P<alt>[^\]]*)\]\((?P<img_name>img-\d+\.[a-zA-Z0-9]+)\)'
        r'(?:\s*\n+\s*(?P<caption_line>(?:\*{1,2}|#{1,4}\s*)?Fig(?:ure)?\.?\s*(\d+)(?:[\.\-–—](\d+))?[^\n]*))?',
        re.IGNORECASE
    )

    matches = list(img_placeholder_re.finditer(updated_text))

    doc_lines = updated_text.splitlines(keepends=True)
    line_offsets = []
    curr_off = 0
    for l in doc_lines:
        line_offsets.append(curr_off)
        curr_off += len(l)

    def get_line_idx(char_offset: int) -> int:
        idx = bisect.bisect_right(line_offsets, char_offset) - 1
        return max(0, idx)

    clean_lines = [l.rstrip("\r\n") for l in doc_lines]
    
    # Pre-scan: collect all explicitly mentioned figure numbers for the current chapter
    explicit_fig_nums = set()
    for m in matches:
        caption_line = m.group("caption_line") or ""
        if caption_line:
            clean_c = re.sub(r'^\*+|\*+$', '', caption_line.strip()).strip()
            fig_match = re.search(r'Fig(?:ure)?\.?\s*(\d+)(?:[\.\-–—](\d+))?', clean_c, re.IGNORECASE)
            if fig_match:
                if fig_match.group(2) is not None:
                    if int(fig_match.group(1)) == ch_num:
                        explicit_fig_nums.add(int(fig_match.group(2)))
                else:
                    explicit_fig_nums.add(int(fig_match.group(1)))
        else:
            l_idx = get_line_idx(m.start())
            f_ch, f_num, _ = _scan_nearby_caption(clean_lines, l_idx)
            if f_num is not None:
                if f_ch == ch_num or f_ch is None:
                    explicit_fig_nums.add(f_num)
    
    fallback_fig_idx = 1
    used_asset_names = set()

    # First pass (forward): resolve figure numbers, captions, and file names in document order
    match_data = []
    for m in matches:
        img_name = m.group("img_name")
        alt = m.group("alt") or ""
        caption_line = m.group("caption_line") or ""
        start_idx = m.start()
        end_idx = m.end()

        # Determine figure numbering from caption or fallback (preserving ch_num parameter)
        fig_ch = ch_num
        caption_text = ""
        is_explicit = False

        if caption_line:
            clean_c = re.sub(r'^\*+|\*+$', '', caption_line.strip()).strip()
            fig_match = re.search(r'Fig(?:ure)?\.?\s*(\d+)(?:[\.\-–—](\d+))?(?:\s*[:—–-]?\s*(.*))?', clean_c, re.IGNORECASE)
            if fig_match:
                if fig_match.group(2) is not None:
                    fig_ch = int(fig_match.group(1))
                    fig_num = int(fig_match.group(2))
                else:
                    fig_ch = ch_num
                    fig_num = int(fig_match.group(1))
                caption_text = fig_match.group(3).strip() if fig_match.group(3) else clean_c
                caption_text = caption_text.strip("*_ ").strip()
                is_explicit = True
            else:
                while (fig_ch == ch_num and fallback_fig_idx in explicit_fig_nums) or any(f"ch{fig_ch:02d}_fig_{fallback_fig_idx:02d}." in u for u in used_asset_names):
                    fallback_fig_idx += 1
                fig_num = fallback_fig_idx
                fallback_fig_idx += 1
                caption_text = clean_c
        else:
            l_idx = get_line_idx(start_idx)
            f_ch, f_num, c_text = _scan_nearby_caption(clean_lines, l_idx)
            if f_num is not None:
                fig_ch = f_ch if f_ch is not None else ch_num
                fig_num = f_num
                caption_text = c_text
                is_explicit = True
            else:
                while (fig_ch == ch_num and fallback_fig_idx in explicit_fig_nums) or any(f"ch{fig_ch:02d}_fig_{fallback_fig_idx:02d}." in u for u in used_asset_names):
                    fallback_fig_idx += 1
                fig_num = fallback_fig_idx
                fallback_fig_idx += 1
                caption_text = alt or f"Figure {fig_ch}.{fig_num}"

        ext = os.path.splitext(img_name)[1] or ".jpeg"
        base_asset_name = f"ch{fig_ch:02d}_fig_{fig_num:02d}{ext}"

        if base_asset_name not in used_asset_names:
            canonical_asset_name = base_asset_name
        else:
            # Sub-asset numbering for multi-image / multi-panel figures
            sub_k = 1
            while f"ch{fig_ch:02d}_fig_{fig_num:02d}_sub{sub_k:02d}{ext}" in used_asset_names:
                sub_k += 1
            canonical_asset_name = f"ch{fig_ch:02d}_fig_{fig_num:02d}_sub{sub_k:02d}{ext}"

        used_asset_names.add(canonical_asset_name)
        canonical_target_path = os.path.join(assets_dir, canonical_asset_name)
        rel_asset_path = f"assets/figures/{canonical_asset_name}"

        match_data.append({
            "start_idx": start_idx,
            "end_idx": end_idx,
            "img_name": img_name,
            "fig_ch": fig_ch,
            "fig_num": fig_num,
            "caption_text": caption_text,
            "caption_line": caption_line,
            "is_explicit": is_explicit,
            "canonical_asset_name": canonical_asset_name,
            "canonical_target_path": canonical_target_path,
            "rel_asset_path": rel_asset_path,
        })

    # M18 cross-run collision guard. used_asset_names only protects
    # collisions created inside this invocation; a caller may reuse one
    # shared assets_dir across separate runs. Never let a later run silently
    # overwrite a different already-published canonical figure.
    # Preflight every target before copying anything so a conflict is a
    # no-partial-mutation refusal. Identical existing files are safe to reuse.
    for d in match_data:
        src_img_path = image_map.get(d["img_name"])
        target = d["canonical_target_path"]
        if src_img_path and os.path.exists(src_img_path) and os.path.exists(target):
            if not filecmp.cmp(src_img_path, target, shallow=False):
                raise FileExistsError(
                    "Refusing cross-run figure overwrite: canonical asset "
                    f"{target!r} already exists with different content from "
                    f"{src_img_path!r}. Use a run-specific --assets-dir/--out-dir "
                    "or reconcile the figure identity explicitly."
                )

    # Second pass (reverse): perform string slice replacements and copy assets
    for d in reversed(match_data):
        src_img_path = image_map.get(d["img_name"])
        file_copied = False
        if src_img_path and os.path.exists(src_img_path):
            if not os.path.exists(d["canonical_target_path"]):
                shutil.copyfile(src_img_path, d["canonical_target_path"])
            file_copied = True

        # Build clean markdown block
        clean_tag = f"\n\n![Fig {d['fig_ch']}.{d['fig_num']}: {d['caption_text']}]({d['rel_asset_path']})\n"
        if d["caption_line"]:
            clean_tag += f"\n{d['caption_line'].strip()}\n"

        updated_text = updated_text[:d["start_idx"]] + clean_tag + updated_text[d["end_idx"]:]

        audit_results.append({
            "placeholder": d["img_name"],
            "fig_key": f"{d['fig_ch']}.{d['fig_num']}",
            "caption": d["caption_text"],
            "canonical_name": d["canonical_asset_name"],
            "asset_path": d["rel_asset_path"],
            "src_path": src_img_path or "NOT FOUND",
            "copied": file_copied
        })

    audit_results.reverse()
    return updated_text, audit_results
