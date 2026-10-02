#!/usr/bin/env python3
"""Static checks for an offline study-guide HTML file."""
import json
import re
import sys
from pathlib import Path

def main():
    legacy = "--legacy-v4" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--legacy-v4"]
    if len(args) != 1:
        print("usage: check_guide.py FILE.html [--legacy-v4]", file=sys.stderr)
        return 2
    path = Path(args[0])
    text = path.read_text(encoding="utf-8")
    errors = []
    if "maximum-scale" in text or "user-scalable=no" in text:
        errors.append("pinch zoom disabled")
    if not re.search(r'name="viewport"[^>]+width=device-width', text):
        errors.append("viewport missing width=device-width")
    if "reader-header" not in text or "readerChapter" not in text:
        errors.append("reader chrome missing")
    if "@page" not in text or "A4" not in text:
        errors.append("A4 page rule missing")
    if re.search(r"<script[^>]+src=", text) or re.search(r"<link[^>]+href=[\"']https?:", text):
        errors.append("external script or stylesheet")
    if "section —" not in text and "section+' — '" not in text and "section+' — '+title" not in text:
        medicine = re.search(r'data-book=["\']medicine["\']', text) and "readerChapter" in text
        titled = "ch.title" in text or "· '+ch.title" in text
        if not (medicine and titled):
            errors.append("section-chapter bookmark label missing")
    if "break-before:page" not in text and "page-break-before:always" not in text:
        errors.append("chapter print page-break missing")
    if "table-header-group" not in text:
        errors.append("repeating table header missing")
    if "orphans:3" not in text and "orphans: 3" not in text:
        errors.append("print orphans/widows missing")
    if re.search(r"<pre><code>(?:graph|flowchart|sequenceDiagram)\b", text) and "diagram-source" not in text and "Diagram source" not in text:
        errors.append("mermaid source is not captioned")
    if 'id="readerCalcTemplate"' in text or "id='readerCalcTemplate'" in text:
        for drug in ("iron-iv", "dopamine-low", "norepinephrine", "amino-acid"):
            if not re.search(rf'value="{drug}"[^>]*disabled|value=\'{drug}\'[^>]*disabled', text):
                errors.append(f"calculator entry not disabled: {drug}")
        if "0.5" not in text or "300" not in text:
            errors.append("calculator weight range 0.5–300 missing")
    if re.search(r"fonts\.google", text) or re.search(r"cdn\.", text):
        errors.append("CDN asset")
    m = re.search(r"<!--STRUCTURE-CENSUS (\{.*?\}) -->", text)
    if not m and not legacy:
        errors.append("structure census missing")
    if m:
        info = json.loads(m.group(1))
        if info.get("status") != "PARSE SUCCESS":
            errors.append("census status is not PARSE SUCCESS")
        if not info.get("chapters"):
            errors.append("zero chapters certified")
        if info.get("inferred_sections") or info.get("fallback_chapters"):
            errors.append("parser-inferred structure certified")
        if info.get("dummy_chapter") and not info.get("recognized_headings"):
            errors.append("dummy chapter certified")
        extract = int(info.get("extract_chars") or 0)
        body = re.sub(r"<[^>]+>", " ", text)
        if extract > 2000 and len(body) < extract * 0.3:
            errors.append("output text unexpectedly small versus source extract")
    print(f"{path.name}: {'ok' if not errors else 'FAIL'}")
    for err in errors:
        print(" -", err)
    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
