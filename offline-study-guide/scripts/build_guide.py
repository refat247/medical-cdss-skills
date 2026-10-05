#!/usr/bin/env python3
"""Build an offline study-guide HTML file from markdown, PDF, or Word.

Output uses the same reader shell as the V4 investigation guide:
contents, search, section-aware bookmarks, themes, chapter menu, A4 print.
"""
import argparse
import html
import re
from pathlib import Path

ASSETS = Path(__file__).resolve().parents[1] / "assets"

def slug(text, used):
    base = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "chapter"
    n = base
    i = 2
    while n in used:
        n = f"{base}-{i}"
        i += 1
    used.add(n)
    return n

def _safe_href(url):
    from urllib.parse import urlsplit
    url = (url or "").strip()
    try:
        scheme = urlsplit(url).scheme.lower()
    except Exception:
        return None
    return url if scheme in {"http", "https"} else None


def _inline_markup(text):
    escaped = html.escape(str(text))
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"`(.+?)`", r"<code>\1</code>", escaped)
    return escaped


def _render_link(label, href):
    safe = _safe_href(href)
    label_html = _inline_markup(label)
    if not safe:
        # Preserve visible source information without creating an executable link.
        return label_html + " (" + html.escape(str(href)) + ")"
    return f'<a href="{html.escape(safe, quote=True)}" rel="noopener noreferrer">{label_html}</a>'


def inline(text):
    """Render controlled inline markup while escaping arbitrary source HTML.

    Markdown strings support **strong**, `code`, and ordinary [label](http/https)
    links. DOCX may provide a structured segment object so hyperlink relationships
    can be preserved without allowing raw HTML through the source.
    """
    if isinstance(text, dict) and "segments" in text:
        out = []
        for seg in text.get("segments", []):
            if seg.get("type") == "link":
                out.append(_render_link(seg.get("text", ""), seg.get("href", "")))
            else:
                out.append(html.escape(str(seg.get("text", ""))))
        return "".join(out).strip()

    raw = str(text).strip()
    links = []
    link_re = re.compile(r"\[([^]\n]+)\]\(([^)\n]+)\)")

    def hold(match):
        idx = len(links)
        links.append(_render_link(match.group(1), match.group(2)))
        return f"\ue000OSGLINK{idx}\ue001"

    protected = link_re.sub(hold, raw)
    rendered = _inline_markup(protected)
    for idx, link_html in enumerate(links):
        rendered = rendered.replace(f"\ue000OSGLINK{idx}\ue001", link_html)
    return rendered


def blocks_to_html(blocks):
    parts = []
    for kind, data in blocks:
        if kind == "p":
            parts.append(f"<p>{inline(data)}</p>")
        elif kind == "ul":
            parts.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in data) + "</ul>")
        elif kind == "ol":
            parts.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in data) + "</ol>")
        elif kind == "table":
            rows = data
            if not rows:
                continue
            head = "".join(f"<th scope=\"col\">{inline(c)}</th>" for c in rows[0])
            body = []
            for row in rows[1:]:
                body.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>")
            parts.append("<div class=\"table-wrapper\"><table><thead><tr>" + head + "</tr></thead><tbody>" + "".join(body) + "</tbody></table></div>")
        elif kind == "h3":
            parts.append(f"<h3 class=\"source-subheading\">{inline(data)}</h3>")
        elif kind == "pre":
            parts.append(f"<pre><code>{html.escape(str(data))}</code></pre>")
    return "\n".join(parts)

def parse_markdown(text):
    lines = text.splitlines()
    title = "Study guide"
    sections = []
    intro = []
    current = None
    chapter = None
    para = []
    listbuf = None
    table = []
    recognized = []
    inferred_sections = []
    dropped = 0
    placed = 0

    def blocks():
        if chapter is not None:
            return chapter["blocks"]
        if current is not None:
            return current["intro"]
        return intro

    def flush_para():
        nonlocal para, placed
        if not para:
            return
        blocks().append(("p", " ".join(para)))
        placed += 1
        para = []

    def flush_list():
        nonlocal listbuf, placed
        if not listbuf:
            return
        blocks().append(listbuf)
        placed += 1
        listbuf = None

    def flush_table():
        nonlocal table, placed
        if not table:
            return
        blocks().append(("table", table))
        placed += 1
        table = []

    def start_section(name, inferred=False):
        nonlocal current, chapter
        flush_para(); flush_list(); flush_table()
        if current and (current["chapters"] or current["intro"]):
            sections.append(current)
        current = {"title": name, "chapters": [], "intro": [], "inferred": inferred}
        chapter = None
        if inferred:
            inferred_sections.append(name)
        else:
            recognized.append(name)

    def ensure_chapter(name):
        nonlocal chapter
        flush_para(); flush_list(); flush_table()
        if current is None:
            start_section("Guide", inferred=True)
        chapter = {"title": name, "blocks": []}
        current["chapters"].append(chapter)
        recognized.append(name)

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("# "):
            flush_para(); flush_list(); flush_table()
            title = line[2:].strip()
            recognized.append(title)
            continue
        if line.startswith("## "):
            start_section(line[3:].strip())
            continue
        if line.startswith("### "):
            ensure_chapter(line[4:].strip())
            continue
        if line.startswith("|") and "|" in line[1:]:
            flush_para(); flush_list()
            cells = [c.strip() for c in line.strip("|").split("|")]
            # Markdown alignment/separator row: --- / :--- / ---: / :---:
            if cells and all(re.fullmatch(r":?-{3,}:?", c.replace(" ", "")) for c in cells):
                continue
            table.append(cells)
            continue
        flush_table()
        m = re.match(r"^[-*] (.+)", line)
        n = re.match(r"^\d+\. (.+)", line)
        if m or n:
            flush_para()
            kind = "ul" if m else "ol"
            item = (m or n).group(1)
            if not listbuf or listbuf[0] != kind:
                flush_list()
                listbuf = (kind, [])
            listbuf[1].append(item)
            continue
        flush_list()
        if not line.strip():
            flush_para()
            continue
        para.append(line.strip())
    flush_para(); flush_list(); flush_table()
    if current and (current["chapters"] or current["intro"]):
        sections.append(current)
    parse_markdown.meta = {
        "recognized": recognized,
        "dropped_blocks": dropped,
        "placed_blocks": placed,
        "section_intro_blocks": sum(len(sec.get("intro") or []) for sec in sections),
        "fallback_chapters": [],
        "inferred_sections": inferred_sections,
    }
    return title, sections, intro

def list_kind(document, paragraph):
    from docx.oxml.ns import qn
    style = (paragraph.style.name or "").lower()
    if "list bullet" in style or style in {"list paragraph"} and "number" not in style:
        if "list bullet" in style:
            return "ul"
    if "list number" in style or "list numbered" in style:
        return "ol"
    pPr = paragraph._p.pPr
    if pPr is None or pPr.numPr is None or pPr.numPr.numId is None:
        return None
    num_id = str(pPr.numPr.numId.val)
    try:
        numbering = document.part.numbering_part._element
        abstract = None
        for num in numbering.findall(qn("w:num")):
            if num.get(qn("w:numId")) == num_id:
                abs_el = num.find(qn("w:abstractNumId"))
                abstract = abs_el.get(qn("w:val")) if abs_el is not None else None
                break
        for abs_el in numbering.findall(qn("w:abstractNum")):
            if abstract is not None and abs_el.get(qn("w:abstractNumId")) != abstract:
                continue
            lvl = abs_el.find(qn("w:lvl"))
            fmt = lvl.find(qn("w:numFmt")) if lvl is not None else None
            if fmt is not None and fmt.get(qn("w:val")) == "bullet":
                return "ul"
            return "ol"
    except Exception:
        return "ul"
    return "ul"

def _docx_visible_text(paragraph):
    from docx.oxml.ns import qn
    texts = []
    for node in paragraph._p.iter():
        if node.tag == qn("w:t") and node.text:
            texts.append(node.text)
        elif node.tag == qn("w:tab"):
            texts.append("\t")
        elif node.tag == qn("w:br"):
            texts.append("\n")
    return "".join(texts)


def _docx_inline(document, paragraph):
    """Return plain text or controlled inline segments with hyperlink targets."""
    from docx.oxml.ns import qn
    has_hyperlink = any(child.tag == qn("w:hyperlink") for child in paragraph._p)
    if not has_hyperlink:
        return paragraph.text
    segments = []
    for child in paragraph._p:
        if child.tag == qn("w:hyperlink"):
            label = "".join((t.text or "") for t in child.iter(qn("w:t")))
            rid = child.get(qn("r:id"))
            href = ""
            if rid:
                rel = document.part.rels.get(rid)
                if rel is not None:
                    href = getattr(rel, "target_ref", "") or ""
            if label:
                if href:
                    segments.append({"type": "link", "text": label, "href": href})
                else:
                    segments.append({"type": "text", "text": label})
        else:
            text = "".join((t.text or "") for t in child.iter(qn("w:t")))
            if text:
                segments.append({"type": "text", "text": text})
    return {"segments": segments}


def _inline_plain_text(value):
    if isinstance(value, dict) and "segments" in value:
        return "".join(str(seg.get("text", "")) for seg in value.get("segments", []))
    return str(value)


def _docx_cell_inline(document, cell):
    parts = [_docx_inline(document, p) for p in cell.paragraphs]
    parts = [p for p in parts if _inline_plain_text(p).strip()]
    if not parts:
        return ""
    if all(isinstance(p, str) for p in parts):
        return "\n".join(parts)
    segs = []
    for i, part in enumerate(parts):
        if i:
            segs.append({"type": "text", "text": "\n"})
        if isinstance(part, dict):
            segs.extend(part.get("segments", []))
        else:
            segs.append({"type": "text", "text": part})
    return {"segments": segs}


def parse_docx(path):
    import docx
    from docx.oxml.ns import qn
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    document = docx.Document(path)
    title = path.stem
    sections = []
    intro = []
    current = None
    chapter = None
    recognized = []
    fallback = []
    inferred_sections = []
    dropped = 0

    def ensure(name, is_fallback=False):
        nonlocal chapter, current
        if current is None:
            current = {"title": "Guide", "chapters": [], "intro": [], "inferred": True, "provenance": "parser-inferred"}
            inferred_sections.append("Guide")
        chapter = {"title": name, "blocks": [], "fallback": is_fallback}
        current["chapters"].append(chapter)
        if is_fallback:
            fallback.append(name)

    def add_block(kind, data):
        if chapter is not None:
            if kind in {"ul", "ol"} and chapter["blocks"] and chapter["blocks"][-1][0] == kind:
                chapter["blocks"][-1][1].append(data)
            else:
                chapter["blocks"].append((kind, [data] if kind in {"ul", "ol"} else data))
            return
        if current is not None:
            if kind in {"ul", "ol"} and current["intro"] and current["intro"][-1][0] == kind:
                current["intro"][-1][1].append(data)
            else:
                current["intro"].append((kind, [data] if kind in {"ul", "ol"} else data))
            return
        intro.append((kind, [data] if kind in {"ul", "ol"} else data))

    for child in document.element.body.iterchildren():
        if child.tag == qn("w:p"):
            p = Paragraph(child, document)
            style = (p.style.name or "").lower()
            rich = _docx_inline(document, p)
            text = _inline_plain_text(rich).strip()
            if not text:
                continue
            if style.startswith("title") or style == "heading 1":
                title = text
                recognized.append(text)
                continue
            if style == "heading 2":
                if current and (current["chapters"] or current["intro"]):
                    sections.append(current)
                current = {"title": text, "chapters": [], "intro": [], "provenance": "source"}
                chapter = None
                recognized.append(text)
                continue
            if style == "heading 3":
                ensure(text)
                recognized.append(text)
                continue
            kind = list_kind(document, p)
            if kind:
                add_block(kind, rich)
                continue
            add_block("p", rich)
        elif child.tag == qn("w:tbl"):
            table_obj = Table(child, document)
            rows = [[_docx_cell_inline(document, c) for c in row.cells] for row in table_obj.rows]
            if rows:
                add_block("table", rows)
        elif child.tag != qn("w:sectPr"):
            dropped += 1
    if current and (current["chapters"] or current["intro"]):
        sections.append(current)
    parse_docx.meta = {
        "recognized": recognized,
        "dropped_blocks": dropped,
        "fallback_chapters": fallback,
        "inferred_sections": inferred_sections,
        "section_intro_blocks": sum(len(sec.get("intro") or []) for sec in sections),
    }
    return title, sections, intro

PART_RE = re.compile(r"^(part|section)\s+([ivxlcdm]+|\d+)\b(.*)$", re.I)
CHAPTER_RE = re.compile(r"^chapter\s+\d+\b\s*[:.\-—–]?\s*.*$", re.I)
APPENDIX_RE = re.compile(r"^appendix\s+[a-z0-9]+\b\s*[:.\-—–]?\s*.*$", re.I)
CANDIDATE_RE = re.compile(r"^(introduction|background|discussion|conclusion|overview|methods|results)\b", re.I)

def _norm_pdf_heading(text):
    import unicodedata
    text = str(text).replace("ﬁ", "fi").replace("ﬂ", "fl")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip().lower()


def _pdf_layout_probe(path):
    """Return a conservative layout-aware textbook parse candidate or None.

    This mode is intentionally narrow: it requires an extractable multi-page PDF,
    a large title on page 1, at least five page-1 contents-like entries ending in
    page numbers, and strong agreement between those entries and later display
    headings. It is used only when the strict explicit Chapter/Part parser finds
    no real chapters.
    """
    try:
        import fitz
    except Exception:
        return None
    try:
        doc = fitz.open(str(path))
    except Exception:
        return None
    if len(doc) < 2:
        return None
    flags = fitz.TEXT_DEHYPHENATE | fitz.TEXT_PRESERVE_LIGATURES

    # Page-1 title / contents census.
    first = doc[0].get_text("dict", flags=flags)
    title_candidates = []
    author_parts = []
    toc_entries = []
    toc_labels = []
    for block in first.get("blocks", []):
        if "lines" not in block:
            continue
        for line in block["lines"]:
            spans = [sp for sp in line.get("spans", []) if (sp.get("text") or "").strip()]
            if not spans:
                continue
            # Ignore decorative giant numerals when forming the visible line.
            visible = [sp for sp in spans if not (sp.get("size", 0) > 40 and (sp.get("text") or "").strip().isdigit())]
            text = "".join(sp.get("text", "") for sp in visible).strip()
            if not text:
                continue
            sizes = [float(sp.get("size", 0)) for sp in visible]
            max_size = max(sizes) if sizes else 0
            y0 = min(float(sp["bbox"][1]) for sp in visible)
            if max_size >= 20 and any(ch.isalpha() for ch in text):
                title_candidates.append((max_size, y0, text))
            m = re.match(r"(.+?)\s+(\d{1,3})\s*$", text)
            if m and 5 <= max_size <= 10 and len(m.group(1).strip()) >= 4:
                label = m.group(1).strip()
                toc_entries.append(label)
                toc_labels.append(text)
    if not title_candidates or len(toc_entries) < 5:
        doc.close()
        return None
    title_candidates.sort(reverse=True)
    title = title_candidates[0][2]
    title_y = title_candidates[0][1]

    # Preserve author/byline text above the detected title, excluding decorations.
    for block in first.get("blocks", []):
        if "lines" not in block:
            continue
        for line in block["lines"]:
            spans = [sp for sp in line.get("spans", []) if (sp.get("text") or "").strip()]
            if not spans:
                continue
            visible = [sp for sp in spans if not (sp.get("size", 0) > 40 and (sp.get("text") or "").strip().isdigit())]
            if not visible:
                continue
            text = "".join(sp.get("text", "") for sp in visible).strip()
            sizes = [float(sp.get("size", 0)) for sp in visible]
            y0 = min(float(sp["bbox"][1]) for sp in visible)
            if y0 < title_y and 10 <= max(sizes) <= 18 and any(ch.isalpha() for ch in text):
                author_parts.append(text)

    # Body font mode and heading candidates.
    body_sizes = []
    heading_candidates = []
    page_dicts = []
    for pno in range(1, len(doc)):
        page = doc[pno]
        d = page.get_text("dict", flags=flags)
        page_dicts.append(d)
        for block in d.get("blocks", []):
            if "lines" not in block:
                continue
            spans = [sp for ln in block.get("lines", []) for sp in ln.get("spans", []) if (sp.get("text") or "").strip()]
            if not spans:
                continue
            text = " ".join("".join(sp.get("text", "") for sp in ln.get("spans", [])).strip() for ln in block.get("lines", [])).strip()
            if not text:
                continue
            max_size = max(float(sp.get("size", 0)) for sp in spans)
            x0, y0, x1, y1 = map(float, block.get("bbox", (0, 0, 0, 0)))
            # Running headers / decorative chapter-number stripe.
            if y0 < 28 or (x0 > page.rect.width - 35 and re.fullmatch(r"(?:1\s*)+", text)):
                continue
            for sp in spans:
                sz = round(float(sp.get("size", 0)), 1)
                if 6.5 <= sz <= 9.5 and any(ch.isalpha() for ch in (sp.get("text") or "")):
                    body_sizes.append(sz)
            if max_size >= 10.5 and len(text) <= 150 and any(ch.isalpha() for ch in text):
                heading_candidates.append((pno, max_size, text))
    if not body_sizes:
        doc.close()
        return None
    from collections import Counter
    body_size = Counter(body_sizes).most_common(1)[0][0]
    normalized_headings = {_norm_pdf_heading(t) for _, _, t in heading_candidates}
    toc_match = [t for t in toc_entries if _norm_pdf_heading(t) in normalized_headings]
    match_ratio = len(toc_match) / max(1, len(toc_entries))
    if len(toc_match) < 5 or match_ratio < 0.60:
        doc.close()
        return None

    intro = []
    for a in author_parts:
        intro.append(("p", a))
    if toc_labels:
        intro.append(("h3", "Source contents"))
        intro.append(("ul", toc_labels))

    # A renderer container is not asserted as source hierarchy.
    section = {"title": title, "chapters": [], "intro": [], "provenance": "renderer-container"}
    sections = [section]
    chapter = None
    recognized = []
    warnings = []
    dropped = 0
    placed = 0
    table_count = 0
    source_box_count = 0
    source_blocks = 0
    layout_ignored = []
    toc_norm = {_norm_pdf_heading(t) for t in toc_entries}

    def start_chapter(name):
        nonlocal chapter
        chapter = {"title": name, "blocks": [], "fallback": False, "provenance": "source-display-heading"}
        section["chapters"].append(chapter)
        recognized.append(name)

    def add_block(kind, data):
        nonlocal placed, chapter
        if chapter is None:
            # Body prose before the first display heading is retained as front matter.
            intro.append((kind, data))
        else:
            chapter["blocks"].append((kind, data))
        placed += 1

    def clean_block_text(text):
        lines = [re.sub(r"\s+", " ", ln).strip() for ln in str(text).splitlines()]
        return "\n".join(ln for ln in lines if ln)

    def make_text_block(text):
        text = clean_block_text(text)
        if not text:
            return None
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if lines and all(ln.startswith("•") for ln in lines):
            items = [ln.lstrip("•").strip() for ln in lines if ln.lstrip("•").strip()]
            return ("ul", items) if items else None
        # Blocks can contain several bullets compressed into one line.
        if text.startswith("•") and text.count("•") >= 2:
            items = [p.strip() for p in text.split("•") if p.strip()]
            return ("ul", items) if items else None
        return ("p", re.sub(r"\s+", " ", text).strip())

    def table_rows_from_words(page, tab):
        """Reconstruct table columns from source coordinates when PyMuPDF merges cells."""
        tx0, ty0, tx1, ty1 = map(float, tab.bbox)
        xs = []
        for row in tab.rows:
            for cell in row.cells:
                if cell:
                    xs.extend([float(cell[0]), float(cell[2])])
        xs.sort()
        clustered = []
        for x in xs:
            if not clustered or abs(x - clustered[-1]) > 2.0:
                clustered.append(x)
            else:
                clustered[-1] = (clustered[-1] + x) / 2.0
        xs = [x for x in clustered if tx0 - 2 <= x <= tx1 + 2]
        if len(xs) < 3:
            return None
        rows = []
        for ri, row in enumerate(tab.rows):
            cells = [c for c in row.cells if c]
            if not cells:
                continue
            ry0 = min(float(c[1]) for c in cells)
            ry1 = max(float(c[3]) for c in cells)
            words = page.get_text("words", clip=fitz.Rect(tx0, ry0, tx1, ry1), sort=True)
            full = re.sub(r"\s+", " ", " ".join(w[4] for w in words)).strip()
            ncols = len(xs) - 1
            # Numbered box title and compact footnote rows span the table width.
            span_last = bool(ri == len(tab.rows) - 1 and len(cells) == 1 and re.match(r"^(Adapted from|\(|\*|Sensitivity\s*=|Positive predictive value\s*=)", full, re.I))
            if ri == 0 or span_last:
                rows.append([full] + [""] * (ncols - 1))
                continue
            out = [""] * ncols
            line_groups = [[] for _ in range(ncols)]
            for w in words:
                cx = (float(w[0]) + float(w[2])) / 2.0
                ci = ncols - 1
                for i in range(ncols):
                    if xs[i] <= cx < xs[i + 1]:
                        ci = i
                        break
                line_groups[ci].append(w)
            for ci, ws in enumerate(line_groups):
                if ws:
                    out[ci] = re.sub(r"\s+", " ", " ".join(w[4] for w in ws)).strip()
            rows.append(out)
        return rows

    for pno in range(1, len(doc)):
        page = doc[pno]
        d = page_dicts[pno - 1]
        page_w = float(page.rect.width)
        # Conservative table detection. Wide chart grids with dozens of columns are rejected.
        table_items = []
        try:
            found = page.find_tables()
            for tab in found.tables:
                raw_rows = tab.extract() or []
                width = float(tab.bbox[2] - tab.bbox[0])
                cols = max((len(r) for r in raw_rows), default=0)
                nonempty = sum(1 for r in raw_rows for c in r if c and str(c).strip())
                first = " ".join(str(c or "").strip() for c in (raw_rows[0] if raw_rows else []))
                is_box_title = bool(re.match(r"^\s*\d+\.\d+\b", first))
                # In guarded textbook mode, only numbered boxed tables are promoted
                # to semantic HTML. Other grids may be diagrams; source-page images
                # remain the visual-fidelity fallback for those.
                if width >= 140 and 2 <= len(raw_rows) <= 40 and 2 <= cols <= 8 and nonempty >= 3 and is_box_title:
                    rebuilt = table_rows_from_words(page, tab)
                    cleaned = rebuilt or [[re.sub(r"\s+", " ", str(c or "")).strip() for c in r] for r in raw_rows]
                    table_items.append({"bbox": tuple(map(float, tab.bbox)), "rows": cleaned})
        except Exception as exc:
            warnings.append("table detection unavailable on page %d: %s" % (pno + 1, exc))

        used_tables = set()
        blocks = []
        for block in d.get("blocks", []):
            if "lines" not in block:
                continue
            spans = [sp for ln in block.get("lines", []) for sp in ln.get("spans", []) if (sp.get("text") or "").strip()]
            if not spans:
                continue
            text = "\n".join("".join(sp.get("text", "") for sp in ln.get("spans", [])).strip() for ln in block.get("lines", [])).strip()
            if not text:
                continue
            x0, y0, x1, y1 = map(float, block.get("bbox", (0, 0, 0, 0)))
            max_size = max(float(sp.get("size", 0)) for sp in spans)
            # Running headers and decorative right-edge chapter numerals are metadata, not body.
            if y0 < 28:
                layout_ignored.append({"page": pno + 1, "reason": "running-header", "text": clean_block_text(text)[:120]})
                continue
            compact = re.sub(r"\s+", " ", text).strip()
            if re.match(r"^\d+\.\d+\b", compact) and len(compact) < 180 and max_size >= 8.5:
                source_box_count += 1
            if x0 > page_w - 35 and re.fullmatch(r"(?:1\s*)+", compact):
                layout_ignored.append({"page": pno + 1, "reason": "decorative-chapter-stripe", "text": compact[:120]})
                continue
            if y0 > page.rect.height - 35 and not any(ch.isalnum() for ch in compact):
                layout_ignored.append({"page": pno + 1, "reason": "decorative-footer", "text": compact[:120]})
                continue
            # If this text block lies inside a retained table, emit the table once instead.
            matched_table = None
            for idx, ti in enumerate(table_items):
                tx0, ty0, tx1, ty1 = ti["bbox"]
                ix = max(0, min(x1, tx1) - max(x0, tx0))
                iy = max(0, min(y1, ty1) - max(y0, ty0))
                inter = ix * iy
                area = max(1.0, (x1 - x0) * (y1 - y0))
                if inter / area >= 0.55:
                    matched_table = idx
                    break
            if matched_table is not None:
                if matched_table not in used_tables:
                    ti = table_items[matched_table]
                    blocks.append({"x0": ti["bbox"][0], "y0": ti["bbox"][1], "x1": ti["bbox"][2], "y1": ti["bbox"][3], "kind": "table", "rows": ti["rows"], "size": 9.0})
                    used_tables.add(matched_table)
                continue
            blocks.append({"x0": x0, "y0": y0, "x1": x1, "y1": y1, "kind": "text", "text": text, "size": max_size})

        # Reading order: left column top->bottom, then right column top->bottom.
        # Full-width blocks are ordered by y and assigned to the nearer stream.
        mid = page_w / 2.0
        def col_key(item):
            center = (item["x0"] + item["x1"]) / 2.0
            width = item["x1"] - item["x0"]
            if width > page_w * 0.70:
                return (0, item["y0"], item["x0"])
            return (0 if center < mid else 1, item["y0"], item["x0"])
        blocks.sort(key=col_key)

        for item in blocks:
            source_blocks += 1
            if item["kind"] == "table":
                add_block("table", item["rows"])
                table_count += 1
                continue
            text = clean_block_text(item["text"])
            compact = re.sub(r"\s+", " ", text).strip()
            if not compact:
                continue
            ntext = _norm_pdf_heading(compact)
            is_toc_heading = ntext in toc_norm
            is_display_heading = item["size"] >= max(10.5, body_size + 2.5) and len(compact) <= 150 and any(ch.isalpha() for ch in compact)
            # Real source TOC entries are navigation headings. Also admit large display
            # headings absent from the first-page TOC (e.g. Further information / MCQs).
            # Source-contents entries at the normal section-heading size become
            # navigation chapters. Smaller repeats inside a worked example stay
            # local subheadings even if their wording matches a contents entry.
            if (is_toc_heading and item["size"] >= body_size + 4.0) or (is_display_heading and item["size"] >= body_size + 5.0):
                start_chapter(compact)
                continue
            if is_display_heading:
                add_block("h3", compact)
                continue
            block = make_text_block(text)
            if block:
                add_block(*block)
            else:
                dropped += 1

    # Validate that the source contents page and body display headings agree strongly.
    recognized_norm = {_norm_pdf_heading(x) for x in recognized}
    toc_matched_final = [t for t in toc_entries if _norm_pdf_heading(t) in recognized_norm]
    final_ratio = len(toc_matched_final) / max(1, len(toc_entries))
    parse_meta = {
        "recognized": recognized,
        "candidates": [t for _, _, t in heading_candidates[:80]],
        "warnings": warnings,
        "gap_lines": 0,
        "pages": len(doc),
        "extract_chars": sum(len(page.get_text("text", flags=flags).strip()) for page in doc),
        "fallback_chapters": [],
        "inferred_sections": [],
        "renderer_sections": [title],
        "section_intro_blocks": 0,
        "dropped_blocks": dropped,
        "placed_blocks": placed,
        "layout_mode": "fitz-column-aware-textbook",
        "layout_safe": True,
        "body_font_size": body_size,
        "source_toc_entries": toc_entries,
        "source_toc_match_count": len(toc_matched_final),
        "source_toc_match_ratio": round(final_ratio, 4),
        "layout_ignored": layout_ignored[:30],
        "detected_tables": table_count,
        "source_box_tables": source_box_count,
        "visual_only_tables": max(0, source_box_count - table_count),
        "source_blocks": source_blocks,
    }
    doc.close()
    return title, sections, intro, parse_meta


def parse_pdf(path):
    """Parse PDF strictly first, then use conservative layout-aware textbook mode.

    The strict path recognizes only explicit Chapter / Part / Appendix markers.
    If it yields no genuine chapter, a guarded PyMuPDF layout mode may activate
    when a title-page contents list is strongly corroborated by display headings.
    """
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    pages = len(reader.pages)
    lines = []
    for page in reader.pages:
        lines.extend((page.extract_text() or "").splitlines())
    title = path.stem
    sections = []
    intro = []
    current = {"title": "Guide", "chapters": [], "intro": [], "provenance": "renderer-container"}
    chapter = None
    para = []
    warnings = []
    recognized = []
    candidates = []
    gap_lines = 0
    renderer_sections = ["Guide"]

    def flush():
        nonlocal para
        if not para:
            return
        block = ("p", " ".join(para))
        if chapter is not None:
            chapter["blocks"].append(block)
        elif current.get("provenance") == "source":
            current["intro"].append(block)
        else:
            intro.append(block)
        para = []

    def ensure(name):
        nonlocal chapter
        flush()
        chapter = {"title": name, "blocks": [], "fallback": False}
        current["chapters"].append(chapter)

    for raw in lines:
        line = raw.strip()
        if not line:
            flush()
            continue
        if re.search(r"\s{3,}\S", line):
            gap_lines += 1
            warnings.append("possible table or column flattened: " + line[:80])
        if PART_RE.match(line) and len(line) < 90:
            flush()
            if current["chapters"] or current.get("intro"):
                sections.append(current)
            current = {"title": line, "chapters": [], "intro": [], "provenance": "source"}
            chapter = None
            recognized.append(line)
            continue
        if APPENDIX_RE.match(line) and len(line) < 110:
            flush()
            if current["title"] != "Appendices" or current.get("provenance") != "renderer-container":
                if current["chapters"] or current.get("intro"):
                    sections.append(current)
                current = {"title": "Appendices", "chapters": [], "intro": [], "provenance": "renderer-container"}
                renderer_sections.append("Appendices")
                chapter = None
            ensure(line)
            recognized.append(line)
            continue
        if CHAPTER_RE.match(line) and len(line) < 140:
            ensure(line)
            recognized.append(line)
            continue
        if CANDIDATE_RE.match(line) and len(line) < 80:
            candidates.append(line)
        para.append(line)
    flush()
    if current["chapters"] or current.get("intro"):
        sections.append(current)
    extract = "\n".join(lines)

    # If the strict parser did not find a genuine chapter, attempt the guarded
    # layout-aware textbook mode. This does not override explicit-structure PDFs.
    if not any(sec.get("chapters") for sec in sections):
        layout = _pdf_layout_probe(path)
        if layout is not None:
            ltitle, lsections, lintro, lmeta = layout
            parse_pdf.meta = lmeta
            return ltitle, lsections, lintro

    parse_pdf.meta = {
        "recognized": recognized,
        "candidates": candidates[:20],
        "warnings": warnings[:12],
        "gap_lines": gap_lines,
        "pages": pages,
        "extract_chars": len(extract.strip()),
        "fallback_chapters": [],
        "inferred_sections": [],
        "renderer_sections": renderer_sections,
        "section_intro_blocks": sum(len(sec.get("intro") or []) for sec in sections),
        "dropped_blocks": 0,
        "layout_mode": "strict-explicit-headings",
        "layout_safe": False,
    }
    return title, sections, intro

def render(title, book, sections, calculator=False, intro=None, source_pdf=None, embed_source_pages=False):
    used = set()
    toc = []
    intro = intro or []
    front = blocks_to_html(intro) if intro and isinstance(intro[0], tuple) else (f"<p>{inline(' '.join(intro))}</p>" if intro else "")
    body = [f"<h1>{html.escape(title)}</h1>", front]
    for sec in sections:
        sid = slug(sec["title"], used)
        toc.append(f"<h3>{html.escape(sec['title'])}</h3><ol>")
        articles = []
        for ch in sec["chapters"]:
            cid = slug(ch["title"], used)
            toc.append(f"<li><a href=\"#{cid}\">{html.escape(ch['title'])}</a></li>")
            articles.append(
                f"<article class=\"chapter\" id=\"{cid}\"><h2 class=\"chapter-title\">{html.escape(ch['title'])}</h2>\n{blocks_to_html(ch['blocks'])}\n</article>"
            )
        toc.append("</ol>")
        body.append(
            f"<section class=\"doc-section\" id=\"{sid}\"><h2 class=\"section-title\" id=\"section-{sid}\"><span class=\"section-badge\">Section</span>{html.escape(sec['title'])}</h2>\n"
            + blocks_to_html(sec.get("intro") or []) + "\n"
            + "\n".join(articles) + "\n</section>"
        )
    body.append("<h2>Table of Contents</h2>\n" + "\n".join(toc))
    if source_pdf and embed_source_pages:
        try:
            import base64
            import fitz
            src_doc = fitz.open(str(source_pdf))
            page_bits = [
                '<section class="source-page-appendix" id="source-page-appendix"><h2>Original PDF pages</h2><p class="source-page-note">Visual fidelity fallback for figures, boxed tables, and page layout. The extracted reader text remains the searchable study layer.</p>'
            ]
            for pno, page in enumerate(src_doc, 1):
                pix = page.get_pixmap(matrix=fitz.Matrix(1.20, 1.20), alpha=False)
                try:
                    blob = pix.tobytes("jpeg", jpg_quality=60)
                except TypeError:
                    blob = pix.tobytes("jpeg")
                data = base64.b64encode(blob).decode("ascii")
                page_bits.append(f'<details class="source-page-fallback" data-source-page="{pno}"><summary>Source page {pno}</summary><img loading="lazy" alt="Original PDF page {pno}" src="data:image/jpeg;base64,{data}"></details>')
            page_bits.append('</section>')
            src_doc.close()
            body.append("\n".join(page_bits))
        except Exception as exc:
            raise RuntimeError(f"failed to embed source PDF pages: {exc}")
    brand = html.escape(title)
    calc_btn = "<button id=\"readerCalculator\" type=\"button\" aria-label=\"Medicine calculator\" title=\"Medicine calculator\">Calc</button>" if calculator else ""
    css = (ASSETS / "reader.css").read_text(encoding="utf-8")
    js = (ASSETS / "reader.js.html").read_text(encoding="utf-8")
    calc = (ASSETS / "calc-template.html").read_text(encoding="utf-8") if calculator else ""
    return f"""<!DOCTYPE html><html lang=\"en\"><head>
<meta charset=\"utf-8\" />
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">
<title>{brand}</title>
<style>
{css}
@page {{size:A4;margin:14mm 12mm}}
 .source-page-appendix{{margin-top:2rem}}.source-page-fallback{{margin:.6rem 0;border:1px solid #bbb;border-radius:.5rem;padding:.35rem .5rem}}.source-page-fallback img{{display:block;max-width:100%;height:auto;margin:.5rem auto}}.source-page-note{{font-size:.9rem;opacity:.8}}
@media print {{.reader-header,.reader-dialog,.reader-status,.reader-skip,.chapter-nav,.sidebar,.site-header,.source-page-appendix{{display:none!important}} body{{background:#fff!important;color:#000!important}}}}
</style>
</head>
<body class=\"ui-reader\" data-book=\"{html.escape(book)}\"><a id=\"readerSkip\" class=\"reader-skip\" href=\"#main-content\">Skip to content</a>
<header id=\"readerHeader\" class=\"reader-header\" aria-label=\"{brand} reader controls\">
  <div class=\"reader-topline\"><span class=\"reader-brand\">{brand}</span></div>
  <nav class=\"reader-actions\" aria-label=\"Reader tools\"><button id=\"readerContents\" type=\"button\">Contents</button><button id=\"readerSearch\" type=\"button\">Search</button><button id=\"readerBookmarks\" type=\"button\">Bookmarks</button>{calc_btn}<button id=\"readerSettings\" type=\"button\">Settings</button></nav>
  <nav class=\"reader-chapterline\" aria-label=\"Chapter navigation\"><button id=\"readerPrev\" type=\"button\" aria-label=\"Previous chapter\">‹</button><select id=\"readerChapter\" aria-label=\"Current chapter\"></select><button id=\"readerNext\" type=\"button\" aria-label=\"Next chapter\">›</button><select id=\"readerTheme\" class=\"reader-theme\" aria-label=\"Theme\"><option value=\"light\">Light</option><option value=\"sepia\">Sepia</option><option value=\"dark\">Dark</option><option value=\"auto\">Auto</option></select></nav><div id=\"readerProgress\" class=\"reader-progress\" aria-hidden=\"true\"></div>
</header>
<dialog id=\"readerDialog\" class=\"reader-dialog\" aria-labelledby=\"readerDialogTitle\"><div class=\"reader-dialog-top\"><h2 id=\"readerDialogTitle\">Reader</h2><button id=\"readerClose\" type=\"button\" aria-label=\"Close dialog\">×</button></div><div id=\"readerDialogBody\" class=\"reader-dialog-body\"></div></dialog>
<div id=\"readerStatus\" class=\"reader-status\" role=\"status\" aria-live=\"polite\"></div>
<main id=\"main-content\" class=\"main-wrap\" role=\"main\">
{chr(10).join(body)}
</main>
{calc}
{js}
</body></html>
"""

def source_chars(path, kind):
    if kind == "md":
        return len(path.read_text(encoding="utf-8"))
    if kind == "docx":
        import docx
        d = docx.Document(str(path))
        bits = [p.text for p in d.paragraphs]
        bits += [c.text for table in d.tables for row in table.rows for c in row.cells]
        return len(" ".join(bits))
    if kind == "pdf":
        return parse_pdf.meta.get("extract_chars", 0)
    return 0

def census_for(path, kind, title, sections, intro):
    chapters = [ch["title"] for sec in sections for ch in sec["chapters"]]
    chapter_tables = sum(
        1 for sec in sections for ch in sec["chapters"]
        for kindb, _ in ch["blocks"] if kindb == "table"
    )
    section_intro_tables = sum(
        1 for sec in sections for kindb, _ in (sec.get("intro") or []) if kindb == "table"
    )
    front_matter_tables = sum(1 for kindb, _ in (intro or []) if kindb == "table")
    tables = chapter_tables + section_intro_tables + front_matter_tables
    if kind == "pdf":
        meta = getattr(parse_pdf, "meta", {})
    elif kind == "docx":
        meta = getattr(parse_docx, "meta", {})
    else:
        meta = getattr(parse_markdown, "meta", {})
    recognized = meta.get("recognized", [])
    fallback = meta.get("fallback_chapters", [])
    inferred = meta.get("inferred_sections", [])
    dummy = bool(fallback) or bool(inferred)
    return {
        "source": path.name,
        "source_type": kind,
        "extract_chars": source_chars(path, kind),
        "title": title,
        "sections": [sec["title"] for sec in sections],
        "section_provenance": [
            {"title": sec["title"], "provenance": sec.get("provenance", "source")}
            for sec in sections
        ],
        "chapters": chapters,
        "appendices": [ch for ch in chapters if ch.lower().startswith("appendix")],
        "heading_candidates": meta.get("candidates", []),
        "recognized_headings": recognized,
        "orphan_chars": len(blocks_to_html(intro or [])),
        "tables": tables,
        "front_matter_tables": front_matter_tables,
        "section_intro_tables": section_intro_tables,
        "chapter_tables": chapter_tables,
        "dummy_chapter": dummy,
        "fallback_chapters": fallback,
        "inferred_sections": inferred,
        "renderer_sections": meta.get("renderer_sections", []),
        "front_matter": [list(block) if isinstance(block, tuple) else block for block in (intro or [])],
        "pages": meta.get("pages", 0),
        "gap_lines": meta.get("gap_lines", 0),
        "dropped_blocks": meta.get("dropped_blocks", 0),
        "section_intro_blocks": meta.get("section_intro_blocks", sum(len(sec.get("intro") or []) for sec in sections)),
        "parser": kind,
        "warnings": meta.get("warnings", []),
        "layout_mode": meta.get("layout_mode", ""),
        "layout_safe": bool(meta.get("layout_safe", False)),
        "source_toc_entries": meta.get("source_toc_entries", []),
        "source_toc_match_count": meta.get("source_toc_match_count", 0),
        "source_toc_match_ratio": meta.get("source_toc_match_ratio", 0),
        "detected_tables": meta.get("detected_tables", tables),
        "source_box_tables": meta.get("source_box_tables", 0),
        "visual_only_tables": meta.get("visual_only_tables", 0),
        "source_blocks": meta.get("source_blocks", 0),
        "layout_ignored": meta.get("layout_ignored", []),
        "embedded_source_pages": meta.get("pages", 0) if meta.get("layout_mode") == "fitz-column-aware-textbook" else 0,
        "visual_fidelity_fallback": bool(meta.get("layout_mode") == "fitz-column-aware-textbook"),
    }

def quality_gate(info, expect=None):
    errors = []
    chapters = info["chapters"]
    if info["source_type"] == "pdf" and info["pages"] and info["extract_chars"] < 40:
        errors.append("inadequate extractable text; OCR or another workflow is required")
    if info.get("inferred_sections"):
        errors.append("parser inferred a section that was not in the source")
    if not chapters:
        errors.append("no genuine chapter; structure review required")
    if info.get("dropped_blocks", 0) > 0:
        errors.append("meaningful source blocks were dropped")
    if info["source_type"] == "pdf" and info["heading_candidates"] and not info["recognized_headings"]:
        errors.append("plain prose headings were not promoted; structure is uncertain")
    if info["source_type"] == "pdf" and info["gap_lines"] >= 8 and not info.get("layout_safe"):
        errors.append("STRUCTURE REVIEW: column or table layout is not safe regardless of recognized chapters")
    if info.get("layout_mode") == "fitz-column-aware-textbook":
        if info.get("source_toc_match_ratio", 0) < 0.80:
            errors.append("layout-aware textbook parse did not match enough source contents headings")
    if info["source_type"] == "md" and info["extract_chars"] > 400 and not chapters:
        errors.append("unstructured markdown has no section or chapter headings")
    if expect:
        if info["chapters"] and expect.get("min_chapters") and len(chapters) < expect["min_chapters"]:
            errors.append("chapter count below expected minimum")
        if expect.get("min_sections") and len(info["sections"]) < expect["min_sections"]:
            errors.append("section count below expected minimum")
        for name in expect.get("titles", []):
            if not any(name.lower() in ch.lower() or name.lower() in sec.lower() for ch in chapters for sec in info["sections"]):
                errors.append("expected title missing: " + name)
        for name in expect.get("appendices", []):
            if not any(name.lower() in ch.lower() for ch in info["appendices"]):
                errors.append("expected appendix missing: " + name)
    return errors

def load(path):
    suffix = path.suffix.lower()
    if suffix == ".doc":
        raise SystemExit("unsupported format: legacy .doc; save as .docx")
    if suffix in {".md", ".markdown", ".txt"}:
        return "md", parse_markdown(path.read_text(encoding="utf-8"))
    if suffix == ".docx":
        return "docx", parse_docx(path)
    if suffix == ".pdf":
        return "pdf", parse_pdf(path)
    raise SystemExit(f"unsupported input: {suffix}")

def main():
    import json
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--out", required=True)
    parser.add_argument("--title")
    parser.add_argument("--book", default="investigation")
    parser.add_argument("--calculator", action="store_true")
    parser.add_argument("--expect")
    parser.add_argument("--override-structure", action="store_true")
    args = parser.parse_args()
    path = Path(args.input)
    kind, loaded = load(path)
    title, sections, intro = loaded
    if args.title:
        title = args.title
    info = census_for(path, kind, title, sections, intro)
    expect = json.loads(Path(args.expect).read_text(encoding="utf-8")) if args.expect else None
    errors = quality_gate(info, expect)
    info["gate_errors"] = errors
    info["status"] = "PARSE SUCCESS" if not errors else "FILE READ SUCCESS"
    census_path = Path(args.out).with_suffix(".census.json")
    census_path.write_text(json.dumps(info, indent=2), encoding="utf-8")
    print("STRUCTURE CENSUS", info["status"])
    print(f"source={info['source']} type={info['source_type']} chars={info['extract_chars']} sections={len(info['sections'])} chapters={len(info['chapters'])} tables={info['tables']} dummy={info['dummy_chapter']}")
    for err in errors:
        print("GATE", err)
    if errors and not args.override_structure:
        raise SystemExit(3)
    render_sections = sections
    render_intro = intro
    if args.override_structure and not any(sec.get("chapters") for sec in sections):
        # Human-approved render-only fallback. The census remains FILE READ SUCCESS,
        # so the normal checker still rejects this artifact as non-certifiable.
        fallback_blocks = list(intro or [])
        for sec in sections:
            fallback_blocks.extend(sec.get("intro") or [])
        render_sections = [{
            "title": "Guide",
            "intro": [],
            "provenance": "override-render-only",
            "chapters": [{"title": "Guide", "blocks": fallback_blocks, "fallback": True}],
        }]
        render_intro = []
    if not render_sections:
        raise SystemExit("no chapters found")
    if args.calculator and args.book != "medicine":
        raise SystemExit("calculator is medicine-only; pass --book medicine")
    html_text = render(
        title, args.book, render_sections, args.calculator, render_intro,
        source_pdf=path if kind == "pdf" else None,
        embed_source_pages=bool(kind == "pdf" and info.get("layout_mode") == "fitz-column-aware-textbook"),
    )
    marker = "<!--STRUCTURE-CENSUS " + json.dumps(info, ensure_ascii=False) + " -->\n"
    Path(args.out).write_text(marker + html_text, encoding="utf-8")
    print(f"wrote {args.out}")

if __name__ == "__main__":
    main()
