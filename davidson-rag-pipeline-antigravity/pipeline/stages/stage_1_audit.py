"""Stage 1 — Forensic Audit Module (v2.13.0).

Performs structural and safety audits on raw markdown_inlined.md before any repair.
"""
import difflib
import io
import os
import re
import sys
from collections import Counter

from pipeline.checkpoint_utils import (
    format_markdown_provenance_header,
    load_checkpoint,
    mark_stage_complete,
    should_run_stage,
)


PIRACY_PATS = [
    r"Medical Higher Study",
    r"HIGHER STUDY",
    r"apps?\.apple\.com",
    r"play\.google\.com",
    r"App Store",
    r"Google Play",
    r"Join.*[Tt]elegram",
    r"t\.me/",
    r"bit\.ly/",
    r"(?:Free|free)\s+(?:Download|download)",
    r"[\u0980-\u09ff]{5,}",
]

ICON_PATS = [
    r"^Information icon:.*$",
    r"^Information icon\s*$",
    r"^Section header icon:.*$",
    r"^Medical\s*$",
    r"^HIGHER STUDY\s*$",
]


def audit_stage1(text: str) -> dict:
    """Computes forensic audit metrics and verdict for raw markdown text."""
    lines = text.splitlines()
    table_rows = len([l for l in lines if l.strip().startswith("|")])
    image_refs = len(re.findall(r"!\[.*?\]\(.*?\.jpeg\)", text))
    page_breaks = len(re.findall(r"^\{[0-9]+\}-+", text, re.MULTILINE))
    bare_pages = len([l for l in lines if re.match(r"^\d{1,3}$", l.strip())])
    running_headers = len(re.findall(r"^[0-9]+ [·•] [A-Z\s\-]+$", text, re.MULTILINE))

    first_h2 = re.search(r"^##\s", text, re.MULTILINE)
    toc_lines = 0
    if first_h2:
        toc_lines = len(re.findall(r"^.+\d{1,3}\s*$", text[:first_h2.start()], re.MULTILINE))

    dead_tbl_links = re.findall(r"\[tbl-\d+\.md\]\(tbl-\d+\.md\)", text)

    piracy_hits = []
    for pat in PIRACY_PATS:
        ms = list(re.finditer(pat, text))
        if ms:
            ctx = text[max(0, ms[0].start() - 50):ms[0].start() + 50].replace("\n", "LF")
            piracy_hits.append(f"  [{len(ms)}x] '{pat}' -> ...{ctx}...")

    headers = [l for l in lines if re.match(r"^#+\s", l)]
    h1s = [l for l in lines if re.match(r"^# [^#]", l)]

    orphan_h3 = []
    last_h2 = None
    for l in lines:
        if re.match(r"^## ", l):
            last_h2 = l
        elif re.match(r"^### ", l) and last_h2 is None:
            orphan_h3.append(l)

    icon_n = sum(len(re.findall(p, text, re.MULTILINE)) for p in ICON_PATS)

    paras = [p for p in re.split(r"\n\n+", text) if len(p) > 80]
    para_words = [set(re.findall(r"\w+", p.lower())) for p in paras]
    dupes = []
    for i in range(len(paras)):
        w1 = para_words[i]
        l1 = len(paras[i])
        for j in range(i + 1, min(i + 10, len(paras))):
            l2 = len(paras[j])
            # Length filter: if length difference ratio exceeds 25%, difflib ratio cannot exceed 0.85
            if abs(l1 - l2) / max(l1, l2) > 0.25:
                continue
            w2 = para_words[j]
            union_len = len(w1 | w2)
            if union_len == 0 or (len(w1 & w2) / union_len) < 0.65:
                continue
            r = difflib.SequenceMatcher(None, paras[i], paras[j]).ratio()
            if r > 0.85:
                dupes.append((i, j, round(r, 2)))

    hc = Counter(headers)
    rep = {k: v for k, v in hc.items() if v > 1 and len(k) > 8}

    critical = len(dead_tbl_links) + len(piracy_hits) + (1 if len(dupes) > 3 else 0)
    major = (1 if len(h1s) > 1 else 0) + (1 if orphan_h3 else 0) + (1 if icon_n > 0 else 0)

    if critical:
        verdict = "unsafe - Stage 2 REQUIRED"
    elif major > 2:
        verdict = "partially_safe - Stage 2 REQUIRED"
    elif major:
        verdict = "safe_with_conditions - Stage 2 REQUIRED"
    else:
        verdict = "production_safe - may skip Stage 2"

    return {
        "total_lines": len(lines),
        "total_chars": len(text),
        "table_rows": table_rows,
        "image_refs": image_refs,
        "page_breaks": page_breaks,
        "bare_pages": bare_pages,
        "running_headers": running_headers,
        "toc_preamble_lines": toc_lines,
        "dead_tbl_links": len(dead_tbl_links),
        "piracy_hits": piracy_hits,
        "h1s": h1s,
        "orphan_h3": orphan_h3,
        "icon_n": icon_n,
        "dupes": dupes,
        "repeated_headers": rep,
        "critical_issues": critical,
        "major_issues": major,
        "verdict": verdict,
    }


def run_stage_1(source_path: str, out_dir: str, prefix: str) -> dict:
    """Executes Stage 1 audit, writes report, and updates checkpoint."""
    checkpoint, checkpoint_path = load_checkpoint(out_dir, prefix)
    if not should_run_stage(checkpoint, "1"):
        return {"status": "skipped", "reason": "checkpoint indicates already complete"}

    with open(source_path, encoding="utf-8") as f:
        text = f.read()

    metrics = audit_stage1(text)

    prov_hdr = format_markdown_provenance_header(source_path, stage_name="1")
    log_lines = [
        prov_hdr.rstrip(),
        "",
        f"# Forensic Audit Report — {prefix}\n",
        f"Total lines: {metrics['total_lines']}",

        f"Total chars: {metrics['total_chars']}",
        f"Table rows:  {metrics['table_rows']}",
        f"Image refs:  {metrics['image_refs']}",
        f"Page-break artifacts: {metrics['page_breaks']}",
        f"Bare page numbers:    {metrics['bare_pages']}",
        f"Running headers:      {metrics['running_headers']}",
        f"TOC preamble lines:   {metrics['toc_preamble_lines']}",
        f"Dead tbl links: {metrics['dead_tbl_links']} [CRITICAL if >0]",
        f"\nPiracy/watermark: {len(metrics['piracy_hits'])} patterns triggered [CRITICAL if any]",
    ]
    log_lines.extend(metrics["piracy_hits"])
    log_lines.append(f"\nH1 headers: {len(metrics['h1s'])} [expect 1]")
    for h in metrics["h1s"]:
        log_lines.append(f"  {h[:100]}")
    log_lines.append(f"Orphaned H3 (no H2 parent): {len(metrics['orphan_h3'])}")
    log_lines.append(f"Icon/alt-text noise: {metrics['icon_n']}")
    log_lines.append(f"Near-duplicate para pairs: {len(metrics['dupes'])} [CRITICAL if >3]")
    for d in metrics["dupes"][:5]:
        log_lines.append(f"  Para {d[0]} vs {d[1]}: {d[2]}")
    log_lines.append(f"Repeated headers: {len(metrics['repeated_headers'])}")
    for k, v in list(metrics["repeated_headers"].items())[:5]:
        log_lines.append(f"  '{k[:70]}' x{v}")

    log_lines.append(f"\nCritical: {metrics['critical_issues']} | Major: {metrics['major_issues']}")
    log_lines.append(f"VERDICT: {metrics['verdict']}")

    log_path = os.path.join(out_dir, f"{prefix}_AUDIT_REPORT.md")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))

    mark_stage_complete(
        checkpoint,
        checkpoint_path,
        "1",
        output_file=os.path.basename(log_path),
        verdict=metrics["verdict"],
        critical_issues=metrics["critical_issues"],
        major_issues=metrics["major_issues"],
    )
    return metrics