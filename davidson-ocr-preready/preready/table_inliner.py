"""Table Inliner Module for Davidson OCR Pre-Ready Pipeline."""
import glob
import os
import re
from typing import Dict, List, Tuple


def find_table_files(source_dir: str) -> Dict[str, str]:
    """Scans pages/page-*/ subdirectories and maps table filename to absolute path."""
    table_map = {}
    pattern = os.path.join(source_dir, "**", "tbl-*.md")
    for path in glob.glob(pattern, recursive=True):
        filename = os.path.basename(path)
        table_map[filename] = os.path.abspath(path)
    return table_map


def ensure_table_delimiters(table_str: str) -> str:
    """Ensures a markdown table has a valid GFM delimiter row (|---|---|) under the header."""
    lines = table_str.strip().splitlines()
    if len(lines) >= 1 and lines[0].strip().startswith("|"):
        if len(lines) == 1 or not re.match(r'^\s*\|?\s*:?-+:?\s*\|', lines[1]):
            col_count = len(lines[0].strip().strip("|").split("|"))   # empty header cells still count
            if col_count > 0:
                delim = "| " + " | ".join(["---"] * col_count) + " |"
                lines.insert(1, delim)
                return "\n".join(lines)
    return table_str


def inline_tables(md_text: str, table_map: Dict[str, str]) -> Tuple[str, List[Dict]]:
    """Replaces [tbl-X.md](tbl-X.md) placeholders with actual table contents."""
    audit_results = []
    updated_text = md_text

    # Pattern matches lines like:
    # 1.1 Root causes of diagnostic error in studies
    # [tbl-0.md](tbl-0.md)
    # OR standalone [tbl-0.md](tbl-0.md)
    placeholder_pattern = re.compile(
        r'(?:(?P<title_line>(?:(?:\*{1,2}|#{1,4}\s*)?(?:(?:Box\s*|Table\s*|Fig(?:ure)?\.?\s*)\d+(?:[\.\-–—]\d+)?|\d+\.\d+)[^\n]*))\n+)?'
        r'\[(?P<tbl_name>tbl-\d+\.md)\](?:\((?P<tbl_link>[^\)]+)\))?',
        re.IGNORECASE | re.MULTILINE
    )

    matches = list(placeholder_pattern.finditer(updated_text))
    
    # We replace from end to beginning to preserve match indices
    for m in reversed(matches):
        full_match_text = m.group(0)
        title_line = m.group("title_line") or ""
        tbl_name = m.group("tbl_name")
        start_idx = m.start()
        end_idx = m.end()

        # If title_line wasn't captured immediately preceding, check lookback in preceding text
        lookback_start = None
        if not title_line:
            preceding_text = updated_text[:start_idx].rstrip()
            preceding_lines = preceding_text.splitlines()
            if preceding_lines:
                last_line = preceding_lines[-1].strip()
                if re.match(r'^(?:(?:\*{1,2}|#{1,4}\s*)?(?:Box|Table|Fig(?:ure)?\.?)\s*\d+(?:[\.\-–—]\d+)?|\d+\.\d+\s+[A-Z])', last_line, re.IGNORECASE):
                    title_line = last_line
                    lookback_start = updated_text[:start_idx].rfind(preceding_lines[-1])

        # Also check lookahead immediately following table if still no title
        if not title_line:
            following_text = updated_text[end_idx:end_idx + 300].lstrip()
            following_lines = following_text.splitlines()
            if following_lines:
                first_following = following_lines[0].strip()
                m_fig_follow = re.match(r'^(?:Fig(?:ure)?\.?\s*\d+(?:[\.\-–—]\d+)?[^\n]*)', first_following, re.IGNORECASE)
                if m_fig_follow:
                    title_line = first_following

        effective_start = lookback_start if lookback_start is not None else start_idx

        # Check if table represents a tabular figure
        fig_key = None
        is_tabular_fig = False
        if title_line:
            m_fig = re.search(r'Fig(?:ure)?\.?\s*(\d+(?:[\.\-–—]\d+)?)', title_line, re.IGNORECASE)
            if m_fig:
                fig_key = m_fig.group(1)
                is_tabular_fig = True

        table_path = table_map.get(tbl_name)
        if table_path and os.path.exists(table_path):
            with open(table_path, "r", encoding="utf-8") as f:
                tbl_content = ensure_table_delimiters(f.read().strip())

            # Format standardized title if present
            formatted_block = ""
            if title_line:
                clean_title = title_line.strip().strip("*_ ")
                if not clean_title.startswith("#") and not is_tabular_fig:
                    clean_title = f"### {clean_title}"
                formatted_block = f"{clean_title}\n\n{tbl_content}\n"
            else:
                formatted_block = f"\n{tbl_content}\n"

            updated_text = updated_text[:effective_start] + formatted_block + updated_text[end_idx:]

            audit_results.append({
                "placeholder": tbl_name,
                "title": title_line.strip() if title_line else "Untitled Table",
                "table_path": table_path,
                "status": "INLINED",
                "rows": tbl_content.count("\n") + 1,
                "is_tabular_figure": is_tabular_fig,
                "fig_key": fig_key
            })
        else:
            audit_results.append({
                "placeholder": tbl_name,
                "title": title_line.strip() if title_line else "Untitled Table",
                "table_path": table_path or "NOT FOUND",
                "status": "MISSING",
                "rows": 0,
                "is_tabular_figure": is_tabular_fig,
                "fig_key": fig_key
            })

    audit_results.reverse()
    return updated_text, audit_results
