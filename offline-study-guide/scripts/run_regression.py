#!/usr/bin/env python3
"""Regression matrix for the offline study-guide input contract."""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "scripts" / "build_guide.py"
CHECK = ROOT / "scripts" / "check_guide.py"
PY = sys.executable

def run(args):
    return subprocess.run([PY, *args], capture_output=True, text=True)

def write_pdf(path, lines):
    # Minimal text PDF. Lines are drawn as separate text objects.
    chunks = []
    y = 760
    for line in lines:
        safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        chunks.append(f"BT /F1 12 Tf 72 {y} Td ({safe}) Tj ET")
        y -= 18
    stream = "\n".join(chunks).encode()
    pdf = f"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
4 0 obj << /Length {len(stream)} >> stream
{stream.decode()}
endstream
endobj
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
0000000{266+len(stream)+40:06d} n 
trailer << /Size 6 /Root 1 0 R >>
startxref
0
%%EOF
""".encode()
    # pypdf is more reliable than a hand xref. Rebuild with pypdf if import works.
    path.write_bytes(pdf)

def pdf_with_pypdf(path, lines):
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject, NumberObject
    # Fall back to report-free text PDF via pypdf page merge is awkward.
    write_pdf(path, lines)
    from pypdf import PdfReader
    try:
        PdfReader(str(path)).pages[0].extract_text()
    except Exception:
        pass

def make_docx(path, blocks):
    import docx
    d = docx.Document()
    for kind, text in blocks:
        if kind == "h1":
            d.add_heading(text, 1)
        elif kind == "h2":
            d.add_heading(text, 2)
        elif kind == "h3":
            d.add_heading(text, 3)
        elif kind == "p":
            d.add_paragraph(text)
        elif kind == "ul":
            d.add_paragraph(text, style="List Bullet")
        elif kind == "ol":
            d.add_paragraph(text, style="List Number")
        elif kind == "bold":
            p = d.add_paragraph()
            run = p.add_run(text)
            run.bold = True
            run.font.size = docx.shared.Pt(28)
        elif kind == "table":
            table = d.add_table(rows=len(text), cols=len(text[0]))
            for r, row in enumerate(text):
                for c, cell in enumerate(row):
                    table.rows[r].cells[c].text = cell
    d.save(path)

def main_html(text):
    i = text.find("<main")
    return text[i:] if i >= 0 else text

def expect(name, code, out, pred, note):
    ok = pred(code, out)
    print(("PASS" if ok else "FAIL"), name, note)
    return ok

def main():
    tmp = Path(tempfile.mkdtemp(prefix="guide-reg-"))
    results = []
    md = tmp / "md01.md"
    md.write_text("# Book\n\n## Part\n\n### Chapter\n\nA sentence.\n\n- bullet\n\n1. one\n\n| Unit | Value |\n| --- | --- |\n| bhori | 11.664 g |\n", encoding="utf-8")
    out = tmp / "md01.html"
    r = run([str(BUILD), str(md), "--out", str(out)])
    html = out.read_text(encoding="utf-8") if out.exists() else ""
    results.append(expect("MD-01", r.returncode, html, lambda c, t: c == 0 and "11.664 g" in t and "<li>bullet</li>" in t and "PARSE SUCCESS" in r.stdout, "structured markdown"))
    c = run([str(CHECK), str(out)])
    results.append(expect("MD-01-check", c.returncode, c.stdout, lambda code, t: code == 0, "checker"))

    paste = tmp / "md02.md"
    paste.write_text("This is unstructured prose. " * 80, encoding="utf-8")
    r = run([str(BUILD), str(paste), "--out", str(tmp / "md02.html")])
    results.append(expect("MD-02", r.returncode, r.stdout, lambda c, t: c != 0 and "PARSE SUCCESS" not in t and not (tmp / "md02.html").exists(), "unstructured paste blocked"))

    docx = tmp / "docx01.docx"
    make_docx(docx, [("h1", "Book"), ("h2", "Part"), ("h3", "Chapter"), ("p", "Body sentence.")])
    r = run([str(BUILD), str(docx), "--out", str(tmp / "docx01.html")])
    html = (tmp / "docx01.html").read_text(encoding="utf-8")
    results.append(expect("DOCX-01", r.returncode, html, lambda c, t: c == 0 and "Body sentence." in t and "Part — Chapter" in t or "chapter-title\">Chapter" in t, "word styles"))

    docx = tmp / "docx02.docx"
    make_docx(docx, [
        ("h1", "Book"), ("h2", "Metals"), ("h3", "Gold"),
        ("p", "Before table."), ("ul", "bullet item"), ("ol", "numbered item"),
        ("table", [["Unit", "Value"], ["bhori", "11.664 g"]]),
        ("p", "After table."), ("h3", "Silver"), ("p", "Silver body."),
    ])
    r = run([str(BUILD), str(docx), "--out", str(tmp / "docx02.html")])
    html = main_html((tmp / "docx02.html").read_text(encoding="utf-8"))
    order = html.find("Before table.") < html.find("11.664 g") < html.find("After table.") < html.find("Silver body.")
    results.append(expect("DOCX-02", r.returncode, html, lambda c, t: c == 0 and "<table>" in t and "<ul>" in t and "<li>bullet item</li>" in t and "<ol>" in t and "<li>numbered item</li>" in t and order, "table and list semantics"))

    docx = tmp / "docx03.docx"
    make_docx(docx, [("bold", "Introduction"), ("p", "Not a heading. " * 30)])
    r = run([str(BUILD), str(docx), "--out", str(tmp / "docx03.html")])
    results.append(expect("DOCX-03", r.returncode, r.stdout, lambda c, t: c != 0 and "PARSE SUCCESS" not in t, "bold is not a heading"))

    docx = tmp / "docx04.docx"
    make_docx(docx, [("bold", "Introduction"), ("p", "Short body.")])
    r = run([str(BUILD), str(docx), "--out", str(tmp / "docx04.html")])
    results.append(expect("DOCX-04", r.returncode, r.stdout, lambda c, t: c != 0 and "PARSE SUCCESS" not in t and not (tmp / "docx04.html").exists(), "short fake heading blocked"))

    docx = tmp / "docx05.docx"
    make_docx(docx, [("h1", "Book"), ("p", "Preface before the part."), ("h2", "Part"), ("h3", "Chapter"), ("p", "Body sentence.")])
    r = run([str(BUILD), str(docx), "--out", str(tmp / "docx05.html")])
    html = (tmp / "docx05.html").read_text(encoding="utf-8") if (tmp / "docx05.html").exists() else ""
    results.append(expect("DOCX-05", r.returncode, html, lambda c, t: c == 0 and "Preface before the part." in t and "chapter-title\">Guide" not in t and "fallback_chapters\": []" in t, "preface kept as front matter"))

    md = tmp / "md03.md"
    md.write_text("# Book\n\n## Part A\n\nThis belongs to Part A intro.\n\n- Preface bullet under Part A\n\n### Topic A\n\nTopic body.\n", encoding="utf-8")
    r = run([str(BUILD), str(md), "--out", str(tmp / "md03.html")])
    html = main_html((tmp / "md03.html").read_text(encoding="utf-8"))
    part = html.find("Part A")
    topic = html.find("chapter-title\">Topic A")
    results.append(expect("MD-03", r.returncode, html, lambda c, t: c == 0 and part < t.find("This belongs to Part A intro.") < topic and "Preface bullet under Part A" in t, "section intro paragraph"))
    results.append(expect("MD-04", r.returncode, html, lambda c, t: "<ul>" in t and "<li>Preface bullet under Part A</li>" in t and t.find("<ul>") < t.find("Topic body."), "section intro list"))

    md = tmp / "md05.md"
    md.write_text("# Book\n\n## Part A\n\n1. First\n2. Second\n\n### Topic A\n\nTopic body.\n", encoding="utf-8")
    r = run([str(BUILD), str(md), "--out", str(tmp / "md05.html")])
    html = (tmp / "md05.html").read_text(encoding="utf-8")
    results.append(expect("MD-05", r.returncode, html, lambda c, t: c == 0 and "<ol>" in t and "<li>First</li>" in t and t.find("<ol>") < t.find("Topic body."), "section intro ordered list"))

    md = tmp / "md06.md"
    md.write_text("# Book\n\n## Part A\n\n| Item | Value |\n| --- | --- |\n| A | 1 |\n\n### Topic A\n\nTopic body.\n", encoding="utf-8")
    r = run([str(BUILD), str(md), "--out", str(tmp / "md06.html")])
    html = (tmp / "md06.html").read_text(encoding="utf-8")
    results.append(expect("MD-06", r.returncode, html, lambda c, t: c == 0 and "<table>" in t and ">A<" in t and t.find("<table>") < t.find("Topic body."), "section intro table"))

    md = tmp / "md07.md"
    md.write_text("# Book\n\n## Part A\n\nPart introduction.\n\n- Bullet A\n- Bullet B\n\n1. First\n2. Second\n\n| Item | Value |\n| --- | --- |\n| A | 1 |\n\n### Topic A\n\nTopic body.\n", encoding="utf-8")
    r = run([str(BUILD), str(md), "--out", str(tmp / "md07.html")])
    html = main_html((tmp / "md07.html").read_text(encoding="utf-8"))
    order = [html.find(x) for x in ["Part introduction.", "<ul>", "<ol><li>First</li>", "<table>", "Topic body."]]
    results.append(expect("MD-07", r.returncode, html, lambda c, t: c == 0 and order == sorted(order) and all(i > 0 for i in order), "mixed section intro order"))

    results.append(expect("MD-08", r.returncode, (tmp / "md07.html").read_text(encoding="utf-8"), lambda c, t: "\"parser\": \"md\"" in t and "Part A" in t and "Topic A" in t, "markdown census ownership"))

    docx = tmp / "docx06.docx"
    make_docx(docx, [
        ("h1", "Book"), ("h2", "Part A"), ("p", "Part introduction."),
        ("ul", "Bullet A"), ("ol", "First"),
        ("table", [["Item", "Value"], ["A", "1"]]),
        ("h3", "Topic A"), ("p", "Topic body."),
    ])
    r = run([str(BUILD), str(docx), "--out", str(tmp / "docx06.html")])
    html = main_html((tmp / "docx06.html").read_text(encoding="utf-8"))
    order = [html.find(x) for x in ["Part introduction.", "<ul>", "<ol><li>First</li>", "<table>", "Topic body."]]
    results.append(expect("DOCX-06", r.returncode, html, lambda c, t: c == 0 and order == sorted(order) and "<li>Bullet A</li>" in t and "<li>First</li>" in t, "docx section intro"))

    results.append(expect("FRONTMATTER-01", 0, main_html((tmp / "docx05.html").read_text(encoding="utf-8")), lambda c, t: "Preface before the part." in t and t.find("Preface before the part.") < t.find("section-title"), "book preface stays global"))

    write_pdf(tmp / "override.pdf", ["Introduction", "Background prose. " * 20])
    r = run([str(BUILD), str(tmp / "override.pdf"), "--out", str(tmp / "override.html"), "--override-structure"])
    html = (tmp / "override.html").read_text(encoding="utf-8") if (tmp / "override.html").exists() else ""
    c = run([str(CHECK), str(tmp / "override.html")]) if html else r
    results.append(expect("OVERRIDE-01", r.returncode, html + c.stdout, lambda code, t: "FILE READ SUCCESS" in html and "PARSE SUCCESS" not in html and c.returncode != 0, "override stays non-certifiable"))

    md = tmp / "md09.md"
    md.write_text("# Book\n\n## Part A\n\n### Guide\n\nLegitimate chapter.\n", encoding="utf-8")
    r = run([str(BUILD), str(md), "--out", str(tmp / "md09.html")])
    html = (tmp / "md09.html").read_text(encoding="utf-8") if (tmp / "md09.html").exists() else ""
    results.append(expect("MD-09", r.returncode, html, lambda c, t: c == 0 and "PARSE SUCCESS" in t and "Legitimate chapter." in t and "inferred_sections\": []" in t, "real chapter named Guide"))

    docx = tmp / "docx07.docx"
    make_docx(docx, [("h1", "Book"), ("h2", "Part A"), ("h3", "Guide"), ("p", "Legitimate chapter.")])
    r = run([str(BUILD), str(docx), "--out", str(tmp / "docx07.html")])
    html = (tmp / "docx07.html").read_text(encoding="utf-8") if (tmp / "docx07.html").exists() else ""
    results.append(expect("DOCX-07", r.returncode, html, lambda c, t: c == 0 and "PARSE SUCCESS" in t and "Legitimate chapter." in t, "real heading Guide"))

    md = tmp / "md10.md"
    md.write_text("# Book\n\n## Part A\n\nShort intro only.\n", encoding="utf-8")
    r = run([str(BUILD), str(md), "--out", str(tmp / "md10.html")])
    results.append(expect("MD-10", r.returncode, r.stdout, lambda c, t: c != 0 and "PARSE SUCCESS" not in t and not (tmp / "md10.html").exists(), "section without chapter blocked"))

    docx = tmp / "docx08.docx"
    make_docx(docx, [("h1", "Book"), ("h2", "Part A"), ("p", "Intro only")])
    r = run([str(BUILD), str(docx), "--out", str(tmp / "docx08.html")])
    results.append(expect("DOCX-08", r.returncode, r.stdout, lambda c, t: c != 0 and "PARSE SUCCESS" not in t, "docx section without chapter blocked"))

    md = tmp / "census01.md"
    md.write_text("# Book\n\nShort body.\n", encoding="utf-8")
    r = run([str(BUILD), str(md), "--out", str(tmp / "census01.html")])
    census = (tmp / "census01.census.json").read_text(encoding="utf-8") if (tmp / "census01.census.json").exists() else ""
    results.append(expect("CENSUS-01", r.returncode, census, lambda c, t: c != 0 and "PARSE SUCCESS" not in t and "FILE READ SUCCESS" in t, "no chapter census not success"))

    md = tmp / "md11.md"
    md.write_text("# Book\n\n### Chapter A\n\nBody.\n", encoding="utf-8")
    r = run([str(BUILD), str(md), "--out", str(tmp / "md11.html")])
    census = (tmp / "md11.census.json").read_text(encoding="utf-8") if (tmp / "md11.census.json").exists() else ""
    results.append(expect("MD-11", r.returncode, census, lambda c, t: c != 0 and "inferred_sections" in t and "PARSE SUCCESS" not in t, "h3 before h2 blocked"))

    docx = tmp / "docx09.docx"
    make_docx(docx, [("h1", "Book"), ("h3", "Chapter A"), ("p", "Body.")])
    r = run([str(BUILD), str(docx), "--out", str(tmp / "docx09.html")])
    census = (tmp / "docx09.census.json").read_text(encoding="utf-8") if (tmp / "docx09.census.json").exists() else ""
    results.append(expect("DOCX-09", r.returncode, census, lambda c, t: c != 0 and "inferred_sections" in t and "PARSE SUCCESS" not in t, "heading 3 before heading 2 blocked"))

    md = tmp / "guide-section.md"
    md.write_text("# Book\n\n## Guide\n\n### Topic\n\nBody.\n", encoding="utf-8")
    r = run([str(BUILD), str(md), "--out", str(tmp / "guide-section.html")])
    html = (tmp / "guide-section.html").read_text(encoding="utf-8") if (tmp / "guide-section.html").exists() else ""
    results.append(expect("MD-GUIDE-SECTION", r.returncode, html, lambda c, t: c == 0 and "PARSE SUCCESS" in t and "inferred_sections\": []" in t, "source section named Guide"))

    md = tmp / "md12.md"
    md.write_text("# Book\n\nFront paragraph.\n\n- Bullet A\n- Bullet B\n\n1. First\n2. Second\n\n| Item | Value |\n| --- | --- |\n| A | 1 |\n\n## Part A\n\n### Topic A\n\nBody.\n", encoding="utf-8")
    r = run([str(BUILD), str(md), "--out", str(tmp / "md12.html")])
    html = main_html((tmp / "md12.html").read_text(encoding="utf-8"))
    order = [html.find(x) for x in ["Front paragraph.", "<ul>", "<ol><li>First</li>", "<table>", "Part A"]]
    results.append(expect("MD-12", r.returncode, html, lambda c, t: c == 0 and order == sorted(order) and all(i > 0 for i in order), "mixed book front matter"))

    docx = tmp / "docx10.docx"
    make_docx(docx, [("h1", "Book"), ("p", "Front paragraph."), ("ul", "Bullet A"), ("ol", "First"), ("table", [["Item", "Value"], ["A", "1"]]), ("h2", "Part A"), ("h3", "Topic A"), ("p", "Body.")])
    r = run([str(BUILD), str(docx), "--out", str(tmp / "docx10.html")])
    html = main_html((tmp / "docx10.html").read_text(encoding="utf-8"))
    order = [html.find(x) for x in ["Front paragraph.", "<ul>", "<ol><li>First</li>", "<table>", "Part A"]]
    results.append(expect("DOCX-10", r.returncode, html, lambda c, t: c == 0 and order == sorted(order), "docx mixed front matter"))

    md = tmp / "front2.md"
    md.write_text("# Book\n\nFirst preface paragraph.\n\nSecond preface paragraph.\n\n## Part A\n\n### Topic\n\nBody.\n", encoding="utf-8")
    r = run([str(BUILD), str(md), "--out", str(tmp / "front2.html")])
    html = main_html((tmp / "front2.html").read_text(encoding="utf-8"))
    results.append(expect("FRONTMATTER-02", r.returncode, html, lambda c, t: c == 0 and "<p>First preface paragraph.</p>" in t and "<p>Second preface paragraph.</p>" in t, "front paragraphs stay separate"))

    bare = tmp / "zero.html"
    bare.write_text((tmp / "md01.html").read_text(encoding="utf-8").replace('"chapters": ["Chapter"]', '"chapters": []'), encoding="utf-8")
    c = run([str(CHECK), str(bare)])
    results.append(expect("CHECK-03", c.returncode, c.stdout, lambda code, t: code != 0 and "zero chapters" in t, "zero-chapter census fails checker"))

    r = run([str(BUILD), str(tmp / "legacy.doc"), "--out", str(tmp / "doc.html")])
    (tmp / "legacy.doc").write_bytes(b"not a real doc")
    r = run([str(BUILD), str(tmp / "legacy.doc"), "--out", str(tmp / "doc.html")])
    results.append(expect("DOC-01", r.returncode, r.stderr + r.stdout, lambda c, t: c != 0 and "legacy .doc" in t, "legacy doc rejected"))

    def pdf_case(name, lines, ok, note):
        path = tmp / f"{name}.pdf"
        write_pdf(path, lines)
        dest = tmp / f"{name}.html"
        r = run([str(BUILD), str(path), "--out", str(dest)])
        blob = r.stdout + r.stderr
        if ok:
            html = dest.read_text(encoding="utf-8") if dest.exists() else ""
            results.append(expect(name, r.returncode, html, lambda c, t: c == 0 and "PARSE SUCCESS" in blob, note))
        else:
            results.append(expect(name, r.returncode, blob, lambda c, t: c != 0 and "PARSE SUCCESS" not in t, note))

    pdf_case("PDF-01", ["Chapter 1 CBC", "Red cells.", "Chapter 2 ESR", "Inflammation."], True, "explicit chapters")
    pdf_case("PDF-02", ["Part I Foundations", "Chapter 1 CBC", "Red cells.", "Part II Price", "Chapter 2 ESR", "Rate."], True, "parts and chapters")
    pdf_case("PDF-03", ["Chapter 1 CBC", "Red cells.", "Appendix A Conversion", "1 bhori = 11.664 g"], True, "appendix")
    pdf_case("PDF-04", ["Introduction", "Background prose. " * 20, "Discussion", "More prose."], False, "plain headings blocked")
    pdf_case("PDF-05", ["Col A    Col B    Col C"] * 10 + ["Introduction", "Body"], False, "hostile columns blocked")
    pdf_case("PDF-05B", ["Chapter 1 First"] + ["Left    Right    Third"] * 10 + ["Chapter 2 Second"], False, "hostile columns with chapters blocked")
    blank = tmp / "PDF-06.pdf"
    from pypdf import PdfWriter
    w = PdfWriter()
    w.add_blank_page(width=612, height=792)
    w.write(blank)
    r = run([str(BUILD), str(blank), "--out", str(tmp / "pdf06.html")])
    results.append(expect("PDF-06", r.returncode, r.stdout + r.stderr, lambda c, t: c != 0 and "OCR" in t, "scan detected"))

    expect_path = tmp / "expect.json"
    expect_path.write_text(json.dumps({"min_chapters": 5, "titles": ["Missing"]}), encoding="utf-8")
    r = run([str(BUILD), str(md), "--out", str(tmp / "expect.html"), "--expect", str(expect_path)])
    results.append(expect("EXPECT", r.returncode, r.stdout, lambda c, t: c != 0 and "expected" in t.lower(), "expectation blocks"))
    stripped = (tmp / "md01.html").read_text(encoding="utf-8")
    stripped = re.sub(r"<!--STRUCTURE-CENSUS \{.*?\} -->\n", "", stripped)
    (tmp / "nocensus.html").write_text(stripped, encoding="utf-8")
    c = run([str(CHECK), str(tmp / "nocensus.html")])
    results.append(expect("CHECK-02", c.returncode, c.stdout, lambda code, t: code != 0 and "census missing" in t, "missing census fails"))
    print("RESULTS", sum(results), "/", len(results))
    return 0 if all(results) else 1

if __name__ == "__main__":
    raise SystemExit(main())
