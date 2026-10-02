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

def inline(text):
    escaped = html.escape(text.strip())
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"`(.+?)`", r"<code>\1</code>", escaped)
    return escaped

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
            head = "".join(f"<th scope=\"col\">{inline(c)}</th>" for c in rows[0])
            body = []
            for row in rows[1:]:
                body.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>")
            parts.append("<div class=\"table-wrapper\"><table><thead><tr>" + head + "</tr></thead><tbody>" + "".join(body) + "</tbody></table></div>")
        elif kind == "pre":
            raw = data.strip()
            if raw.startswith(("graph", "flowchart", "sequenceDiagram")):
                parts.append(
                    '<figure class="diagram-source" role="group" aria-label="Diagram source code">'
                    '<figcaption>Diagram source (Mermaid) — not rendered offline</figcaption>'
                    f"<pre><code>{html.escape(data)}</code></pre></figure>"
                )
            else:
                parts.append(f"<pre><code>{html.escape(data)}</code></pre>")
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
            if re.match(r"^\|\s*-+", line):
                continue
            flush_para(); flush_list()
            cells = [c.strip() for c in line.strip("|").split("|")]
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
            current = {"title": "Guide", "chapters": [], "intro": [], "inferred": True}
            inferred_sections.append("Guide")
        chapter = {"title": name, "blocks": [], "fallback": is_fallback}
        current["chapters"].append(chapter)
        if is_fallback:
            fallback.append(name)

    def add_block(kind, data):
        nonlocal dropped
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
        if kind == "p":
            intro.append(("p", data))
            return
        intro.append((kind, [data] if kind in {"ul", "ol"} else data))
        return

    def add_list(kind, item):
        add_block(kind, item)

    for child in document.element.body.iterchildren():
        if child.tag == qn("w:p"):
            p = Paragraph(child, document)
            style = (p.style.name or "").lower()
            text = p.text.strip()
            if not text:
                continue
            if style.startswith("title") or style == "heading 1":
                title = text
                recognized.append(text)
                continue
            if style == "heading 2":
                if current and (current["chapters"] or current["intro"]):
                    sections.append(current)
                current = {"title": text, "chapters": [], "intro": []}
                chapter = None
                recognized.append(text)
                continue
            if style == "heading 3":
                ensure(text)
                recognized.append(text)
                continue
            kind = list_kind(document, p)
            if kind:
                add_list(kind, text)
                continue
            if chapter is None:
                add_block("p", text)
                continue
            chapter["blocks"].append(("p", text))
        elif child.tag == qn("w:tbl"):
            rows = [[c.text.strip() for c in row.cells] for row in Table(child, document).rows]
            if rows:
                if chapter is not None:
                    chapter["blocks"].append(("table", rows))
                elif current is not None:
                    current["intro"].append(("table", rows))
                else:
                    intro.append(("table", rows))
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

def parse_pdf(path):
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    pages = len(reader.pages)
    lines = []
    for page in reader.pages:
        lines.extend((page.extract_text() or "").splitlines())
    title = path.stem
    sections = []
    current = {"title": "Guide", "chapters": []}
    chapter = None
    para = []
    warnings = []
    recognized = []
    candidates = []
    gap_lines = 0

    def flush():
        nonlocal para
        if para and chapter is not None:
            chapter["blocks"].append(("p", " ".join(para)))
        para = []

    def ensure(name):
        nonlocal chapter
        flush()
        chapter = {"title": name, "blocks": []}
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
            if current["chapters"]:
                sections.append(current)
            current = {"title": line, "chapters": []}
            chapter = None
            recognized.append(line)
            continue
        if APPENDIX_RE.match(line) and len(line) < 110:
            if current["title"] != "Appendices":
                flush()
                if current["chapters"]:
                    sections.append(current)
                current = {"title": "Appendices", "chapters": []}
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
        if chapter is None:
            ensure(current["title"])
        para.append(line)
    flush()
    if current["chapters"]:
        sections.append(current)
    extract = "\n".join(lines)
    parse_pdf.meta = {
        "recognized": recognized,
        "candidates": candidates[:20],
        "warnings": warnings[:12],
        "gap_lines": gap_lines,
        "pages": pages,
        "extract_chars": len(extract.strip()),
    }
    return title, sections, []

def render(title, book, sections, calculator=False, intro=None):
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
    brand = html.escape(title)
    calc_btn = "<button id=\"readerCalculator\" type=\"button\" aria-label=\"Medicine calculator\" title=\"Medicine calculator\">Calc</button>" if calculator else ""
    css = (ASSETS / "reader.css").read_text(encoding="utf-8")
    print_css = (ASSETS / "print-v5.css").read_text(encoding="utf-8")
    js = (ASSETS / "reader.js.html").read_text(encoding="utf-8")
    calc = (ASSETS / "calc-template.html").read_text(encoding="utf-8") if calculator else ""
    return f"""<!DOCTYPE html><html lang=\"en\"><head>
<meta charset=\"utf-8\" />
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">
<title>{brand}</title>
<style>
{css}
{print_css}
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
    tables = sum(1 for sec in sections for ch in sec["chapters"] for kindb, _ in ch["blocks"] if kindb == "table")
    tables += sum(1 for kindb, _ in intro or [] if isinstance(intro[0], tuple) and kindb == "table")
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
        "chapters": chapters,
        "appendices": [ch for ch in chapters if ch.lower().startswith("appendix")],
        "heading_candidates": meta.get("candidates", []),
        "recognized_headings": recognized,
        "orphan_chars": len(blocks_to_html(intro) if intro and isinstance(intro[0], tuple) else " ".join(intro or [])),
        "tables": tables,
        "dummy_chapter": dummy,
        "fallback_chapters": fallback,
        "inferred_sections": inferred,
        "front_matter": [list(block) if isinstance(block, tuple) else block for block in (intro or [])],
        "pages": meta.get("pages", 0),
        "gap_lines": meta.get("gap_lines", 0),
        "dropped_blocks": meta.get("dropped_blocks", 0),
        "section_intro_blocks": meta.get("section_intro_blocks", sum(len(sec.get("intro") or []) for sec in sections)),
        "parser": kind,
        "warnings": meta.get("warnings", []),
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
    if info["source_type"] == "pdf" and info["gap_lines"] >= 8:
        errors.append("STRUCTURE REVIEW: column or table layout is not safe regardless of recognized chapters")
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
    if not sections:
        raise SystemExit("no chapters found")
    if args.calculator and args.book != "medicine":
        raise SystemExit("calculator is medicine-only; pass --book medicine")
    html_text = render(title, args.book, sections, args.calculator, intro)
    marker = "<!--STRUCTURE-CENSUS " + json.dumps(info, ensure_ascii=False) + " -->\n"
    Path(args.out).write_text(marker + html_text, encoding="utf-8")
    print(f"wrote {args.out}")

if __name__ == "__main__":
    main()
