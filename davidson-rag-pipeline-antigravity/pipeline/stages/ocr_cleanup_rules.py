"""Shared OCR-cleanup rules for Stages 1, 2 and 3 (one definition so the audit, the repair and the
re-audit can never disagree about what is "noise").

Second-sweep fixes (skill_audits/SECOND_SWEEP.md 1.5-1.7):
  * running header: anchored per line, so it can no longer swallow the next paragraph
    ("5 • HYPERTENSION\\n\\nACE inhibitors" used to lose "ACE", "3 • NaCl 0.9%" became "aCl 0.9%")
  * bare page numbers: only a number alone on its own paragraph (blank lines around it) is a page
    marker; a "300" inside running text or a table cell is content (a dose) and is left alone
  * TOC preamble: never deletes a markdown heading (it used to delete "# Vitamin B12")
"""
import re

RUNNING_HEADER_RE = re.compile(r"^([0-9]+)[ \t]+[·•][ \t]+[A-Z \-]+[ \t]*$\n?", re.MULTILINE)
_BARE_RE = re.compile(r"\d{1,3}[ \t]*")


def _bare_page_indices(lines):
    out = []
    for i, line in enumerate(lines):
        if not _BARE_RE.fullmatch(line):
            continue
        prev_blank = i == 0 or lines[i - 1].strip() == ""
        next_blank = i == len(lines) - 1 or lines[i + 1].strip() == ""
        if prev_blank and next_blank:
            out.append(i)
    return out


def count_bare_page_lines(text):
    return len(_bare_page_indices(text.split("\n")))


def normalize_bare_page_lines(text, marker=True):
    """Replace isolated 1-3 digit lines with a page marker (marker=True) or drop them (marker=False).
    Returns (new_text, count)."""
    lines = text.split("\n")
    idx = set(_bare_page_indices(lines))
    if not idx:
        return text, 0
    out = []
    for i, line in enumerate(lines):
        if i in idx:
            if marker:
                out.append(f"<!-- page: {line.strip()} -->")
            continue
        out.append(line)
    return "\n".join(out), len(idx)


def strip_toc_preamble(text):
    """Remove TOC-looking lines (ending in a 1-3 digit page number) before the first '## ' heading,
    except markdown headings. Returns (new_text, removed_count)."""
    first_h2 = re.search(r"^##\s", text, re.MULTILINE)
    if not first_h2:
        return text, 0
    block = text[:first_h2.start()]
    kept, removed = [], 0
    for line in block.split("\n"):
        if re.search(r"\d{1,3}\s*$", line) and line.strip() and not line.lstrip().startswith("#"):
            removed += 1
            continue
        kept.append(line)
    return "\n".join(kept) + text[first_h2.start():], removed
