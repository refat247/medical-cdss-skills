r"""v2.6.4 — canonical Stage 2 repair logic (Corpus-Scale Gate Closure, MUST-FIX #1).

Before this module existed, Stage 2's `is_clinical()` guard and repair
sequence lived ONLY as an inline code block inside `SKILL.md` -- copy-pasted
fresh into each chapter-processing session rather than imported from a
single, shared, testable implementation. That meant a bug found in one
chapter's run (Chapter 05's MCQ-stem sweep, see below) could not be fixed
"once" -- every future chapter would re-run whatever code happened to get
pasted into that session, with no guarantee it included the fix.

## The Chapter 05 finding this module fixes

Chapter 05's real checkpoint (`05/..._CHECKPOINT.json`, stage "2" manual_edits)
records: a piracy-removal sweep triggered by a Bengali-text/"Medical Higher
Study" watermark block deleted MCQ 5.1's stem and its five answer options
along with the watermark junk, because `is_clinical()` did not recognize
either of the two line shapes MCQ content took in that chapter:

  - decimal-numbered stems: "5.1. Example question stem"
  - dash-prefixed options: "- A. Example option"

The OLD guard only protected a BARE numbered item ("1. text", via
`^\d+\.\s`) and a BARE lettered option ("A. text" / "A) text", via
`^[A-E][\.\)]\s`) -- neither pattern matches a stem with a second decimal
level before the trailing period, nor an option preceded by a markdown
bullet dash. Chapter 02's own MCQ section uses exactly the dash-prefixed
option shape ("- A. Gliclazide") and was saved only by chapter-layout luck
(its piracy trigger happened to fully resolve one line before the MCQ
section's own heading began) -- confirmed during the post-Chapter-02
generalization audit (`GENERALIZATION_VALIDATION_REPORT.md` #1, "Assumptions
that only held for Chapter 05").
"""
import re

from pipeline.stages.ocr_cleanup_rules import (PIRACY_TRIGGERS, RUNNING_HEADER_RE, normalize_bare_page_lines,
                                               strip_toc_preamble, sweep_piracy)

ICON_PATS = [
    r"^Information icon:.*$\n?", r"^Information icon\s*$\n?",
    r"^Section header icon:.*$\n?",
    r"^Medical\s*$\n?", r"^HIGHER STUDY\s*$\n?",
]


def is_clinical(line):
    r"""Allow-list guard for the piracy-removal sweep (Stage 2, Fix 6):
    protects MCQ options, headers, table rows, numbered items/stems, answer lines,
    and clinical sentences (with drug dosages, units, or clinical terms) from
    being swept away as watermark/piracy junk.

    CRITICAL: never use len > 120 as the sole guard -- it removes MCQ
    answer options (Rule A, SKILL.md).
    """
    l = line.strip()
    if not l:
        return False
    if (
        re.match(r'^<!--\s*(?:page|pdf_page):', l) or
        re.match(r'^#{1,4}\s', l) or
        l.startswith('|') or
        re.match(r'^-?\s*[A-E][\.\)]\s', l) or   # MCQ options: A. A) - A. - A)
        re.match(r'^(Answer|Q\d)', l) or          # answer lines / question stems
        re.match(r'^\d+(?:\.\d+)*\.\s', l) or     # numbered items incl. multi-level decimal stems: 1. / 5.1. / 5.1.2.
        re.match(r'^[-*•]\s', l) or               # bullet list items
        len(l) > 200                               # long prose lines
    ):
        return True

    # CDSS Clinical Safety Guard: Protect short dosage, route, or clinical action lines (<200 chars)
    clinical_keywords = (
        r'\b\d+(?:\.\d+)?\s*(?:mg|mcg|g|mL|units?|IU|mmol/L|mg/dL|%|mg/kg|mcg/kg/min|mL/min|mg/m2|kPa|mmHg)\b|'
        r'\b(?:stat|IV|oral|intramuscular|subcutaneous|infusion|loading dose|maintenance dose|contraindicated|indicated|first-line|second-line|treatment|therapy|diagnosis|management|administer|prescribe|resuscitate|immediately|caution|warning)\b'
    )
    return bool(re.search(clinical_keywords, l, re.IGNORECASE))


def _protected_paragraph_indices(lines_list):
    """v2.6.4 -- second half of the MCQ-preservation fix, found while writing
    this module's own regression test for the historical Chapter 05 shape:
    widening is_clinical()'s regex alone is not sufficient, because a
    multi-line MCQ stem's WRAPPED continuation lines ("prescribed a new
    antibiotic for a urinary tract infection...") are themselves ordinary
    prose -- indistinguishable from any other paragraph -- and is_clinical()
    can only ever recognize the FIRST line of the stem (the one starting
    "5.1. "). Checking each line of the piracy-sweep window in isolation
    therefore still swept a protected stem's own continuation lines even
    after the regex fix.

    Fix: extend protection to the whole PARAGRAPH (a maximal run of
    contiguous non-blank lines) that contains at least one is_clinical()
    line, not just that single line. This is still conservative -- it does
    not protect unrelated paragraphs, and a paragraph with no is_clinical()
    trigger line anywhere in it (e.g. a promotional numbered list embedded
    in the piracy block itself) remains fully removable, exactly as before.

    Returns the set of 0-indexed line numbers that must never be swept.
    """
    protected = set()
    para_start = None
    para_has_trigger = False
    for i, line in enumerate(lines_list):
        if line.strip() == "":
            if para_start is not None and para_has_trigger:
                protected.update(range(para_start, i))
            para_start = None
            para_has_trigger = False
            continue
        if para_start is None:
            para_start = i
        if is_clinical(line):
            para_has_trigger = True
    if para_start is not None and para_has_trigger:
        protected.update(range(para_start, len(lines_list)))
    return protected


def repair_stage2(text):
    """Runs the full Stage 2 autonomous-repair sequence (Fixes 1-9 from
    SKILL.md) against `text` (the raw markdown_inlined.md content) and
    returns `(repaired_text, report_lines, stats)`.

    `stats` is a dict with the same counters SKILL.md's Stage 2 block has
    always logged to Corrections_Log.md: page_break_artifacts_removed,
    image_tags_removed, bare_page_numbers_removed, running_headers_removed,
    icon_noise_removed, piracy_lines_removed, toc_preamble_lines_removed,
    spurious_h1_demoted.

    Pure function -- no file I/O, no checkpoint calls. SKILL.md's Stage 2
    code block is a thin caller: read source, call this, write REPAIRED_S2.md
    + Corrections_Log.md, then the existing checkpoint/manual-boundary-review
    steps proceed exactly as before. This split is what makes a fix here
    apply to every future chapter automatically, rather than needing to be
    remembered and re-pasted per session.
    """
    orig_lines = len(text.splitlines())
    R = []

    n = len(re.findall(r'^\{([0-9]+)\}-+', text, re.MULTILINE))
    text = re.sub(r'^\{([0-9]+)\}-+\n?', r'<!-- page: \1 -->\n', text, flags=re.MULTILINE)
    R.append(f"Normalized {n} page-break artifacts to page markers")
    page_break_artifacts_removed = n

    # v2.23.0 fix: Only strip raw un-decoupled OCR artifacts (img-*.jpeg), PRESERVE decoupled assets/figures/ tags
    n = len(re.findall(r'!\[img-\d+\.jpeg\]\(img-\d+\.jpeg\)\n?', text))
    text = re.sub(r'!\[img-\d+\.jpeg\]\(img-\d+\.jpeg\)\n?', '', text)
    R.append(f"Removed {n} raw OCR image tag lines")
    image_tags_removed = n

    text, n = normalize_bare_page_lines(text)
    R.append(f"Normalized {n} bare page number lines to page markers")
    bare_page_numbers_removed = n

    n = len(RUNNING_HEADER_RE.findall(text))
    text = RUNNING_HEADER_RE.sub(lambda m: f"<!-- page: {m.group(1)} -->\n", text)
    R.append(f"Normalized {n} running chapter headers to page markers")
    running_headers_removed = n

    total_icons = 0
    for pat in ICON_PATS:
        c = len(re.findall(pat, text, re.MULTILINE))
        text = re.sub(pat, '', text, flags=re.MULTILINE)
        total_icons += c
    R.append(f"Removed {total_icons} icon/alt-text noise lines")

    lines_list = text.split('\n')
    clean, _removed = sweep_piracy(lines_list)
    n_rem = len(lines_list) - len(clean)
    text = '\n'.join(clean)
    R.append(f"Removed {n_rem} piracy/watermark lines")
    if n_rem:
        R.append("  WARNING: manually verify boundary lines in REPAIRED_S2.md")

    toc_preamble_lines_removed = 0
    if re.search(r'^##\s', text, re.MULTILINE):
        text, n = strip_toc_preamble(text)
        R.append(f"Removed {n} TOC preamble lines")
        toc_preamble_lines_removed = n

    h1_matches = list(re.finditer(r'^# [^#]', text, re.MULTILINE))
    demoted = 0
    if len(h1_matches) > 1:
        demote = {m.start() for m in h1_matches[1:]}
        new_lines, cp = [], 0
        for line in text.split('\n'):
            if re.match(r'^# [^#]', line) and cp in demote:
                new_lines.append('#' + line)
                demoted += 1
            else:
                new_lines.append(line)
            cp += len(line) + 1
        text = '\n'.join(new_lines)
        R.append(f"Demoted {demoted} spurious H1 -> H2")

    text = re.sub(r'\n{3,}', '\n\n', text)
    R.append("Collapsed excess blank lines")

    stats = {
        "lines_before": orig_lines,
        "lines_after": len(text.splitlines()),
        "page_break_artifacts_removed": page_break_artifacts_removed,
        "image_tags_removed": image_tags_removed,
        "bare_page_numbers_removed": bare_page_numbers_removed,
        "running_headers_removed": running_headers_removed,
        "icon_noise_removed": total_icons,
        "piracy_lines_removed": n_rem,
        "toc_preamble_lines_removed": toc_preamble_lines_removed,
        "spurious_h1_demoted": demoted,
    }
    return text, R, stats
