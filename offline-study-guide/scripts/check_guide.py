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
        if not (re.search(r'data-book=["\']medicine["\']', text) and "readerChapter" in text):
            errors.append("section-chapter bookmark label missing")
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
        if info.get("layout_mode") == "fitz-column-aware-textbook":
            expected_pages = int(info.get("embedded_source_pages") or 0)
            actual_pages = len(re.findall(r'data-source-page="\d+"', text))
            if expected_pages <= 0 or actual_pages != expected_pages:
                errors.append("layout-aware PDF source-page fallback count mismatch")
            if info.get("source_toc_match_ratio", 0) < 0.8:
                errors.append("layout-aware PDF contents-heading match is below trust threshold")
    print(f"{path.name}: {'ok' if not errors else 'FAIL'}")
    for err in errors:
        print(" -", err)
    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
