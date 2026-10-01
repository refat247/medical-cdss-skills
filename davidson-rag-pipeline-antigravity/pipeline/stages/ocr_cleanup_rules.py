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


# ---------------------------------------------------------------------------------------------------------
# Piracy / watermark sweep (second-sweep 1.17). One trigger list shared by Stages 1, 2 and 3.
# Old behaviour: the trigger line itself was "protected" by clinical keywords ("free treatment notes" survived and
# Stage 3 called it PASSED), a -10/+15 line window deleted ordinary clinical sentences with no keyword, and Stage 3
# only knew two of the trigger patterns.
# ---------------------------------------------------------------------------------------------------------
# STRONG triggers are unambiguous watermark text; they delete the line even when it looks like a bullet/heading.
_STRONG_TRIGGERS = [
    r"Medical Higher Study", r"apps?\.apple\.com", r"play\.google\.com",
    r"Join.*[Tt]elegram", r"t\.me/", r"bit\.ly/", r"[\u0980-\u09ff]{5,}",
]
# WEAK triggers can occur in legitimate digital-health prose ("... from the App Store ..."), so they only count on
# a SHORT line (a watermark is a banner, not a sentence).
_WEAK_TRIGGERS = [r"HIGHER STUDY", r"App Store", r"Google Play", r"(?:Free|free)\s+(?:Download|download)"]
_WEAK_MAX_WORDS = 8
PIRACY_TRIGGERS = _STRONG_TRIGGERS + _WEAK_TRIGGERS
_PROMO_WORDS = re.compile(r"\b(?:join|follow|subscribe|download|telegram|whatsapp|facebook|youtube|instagram|channel|group|"
                          r"link|pdf|notes|free|visit|click|www|http|medical|higher study)\b", re.I)
_STRUCTURAL = [
    re.compile(r"^<!--\s*(?:page|pdf_page):"), re.compile(r"^#{1,4}\s"), re.compile(r"^\|"),
    re.compile(r"^-?\s*[A-E][\.\)]\s"), re.compile(r"^(Answer|Q\d)"), re.compile(r"^\d+(?:\.\d+)*\.\s"), re.compile(r"^[-*\u2022]\s"),
]


def is_structural(line):
    """Markdown/MCQ structure that a watermark sweep must never delete (a clinical KEYWORD is not structure)."""
    l = line.strip()
    return bool(l) and any(rx.match(l) for rx in _STRUCTURAL)


def has_strong_trigger(line):
    return any(re.search(p, line) for p in _STRONG_TRIGGERS)


def has_piracy_trigger(line):
    if has_strong_trigger(line):
        return True
    return len(line.split()) <= _WEAK_MAX_WORDS and any(re.search(p, line) for p in _WEAK_TRIGGERS)


def _junk_like(line):
    s = line.strip()
    if not s:
        return True
    if is_structural(s) or re.search(r"\d", s):          # a dose / threshold fragment is never "junk"
        return False
    return len(s.split()) <= 2 or bool(_PROMO_WORDS.search(s)) or has_piracy_trigger(s)


def sweep_piracy(lines, window=3):
    """Returns (kept_lines, removed_count). Deletes (a) every non-structural trigger line and (b) the blank-bounded
    paragraphs within `window` paragraphs of a trigger ONLY when every line of such a paragraph is junk-like
    (short, promo wording, URL, trigger). Clinical prose paragraphs next to a watermark are always kept."""
    # paragraphs as (start, end) index ranges of non-blank runs
    paras, start = [], None
    for i, l in enumerate(list(lines) + [""]):
        if l.strip():
            if start is None:
                start = i
        elif start is not None:
            paras.append((start, i))
            start = None
    drop = set()
    trig_paras = [k for k, (a, b) in enumerate(paras) if any(has_piracy_trigger(lines[i]) for i in range(a, b))]
    for k in trig_paras:
        a, b = paras[k]
        for i in range(a, b):
            if has_strong_trigger(lines[i]) or (has_piracy_trigger(lines[i]) and not is_structural(lines[i])):
                drop.add(i)
        for step in (-1, 1):
            j, seen = k + step, 0
            while 0 <= j < len(paras) and seen < window:
                pa, pb = paras[j]
                if all(_junk_like(lines[i]) for i in range(pa, pb)):
                    drop.update(range(pa, pb))
                    j += step
                    seen += 1
                else:
                    break
    kept = [l for i, l in enumerate(lines) if i not in drop]
    return kept, len(drop)
