"""Stage 3 (reaudit) verdict/decision logic, extracted out of SKILL.md's
inline code block so CP-02's "must not checkpoint COMPLETED on a failing
verdict" fix is testable without hand-pasting a script into a live session.

SKILL.md's Stage 3 block becomes a thin caller: read the two files, call
compute_reaudit(), then branch mark_stage_complete/mark_stage_blocked on
result["verdict"] using decide_checkpoint_action(). The regex/ratio logic
below is unchanged from the original inline block — this is an extraction,
not a rewrite.
"""
import re
import difflib


def compute_reaudit(orig_text, rep_text):
    """Same logic as the original SKILL.md Stage 3 inline block. Returns a
    dict: {preservation_percent, h1_count, issues, verdict}."""
    orig_s = re.sub(r'<!--[\s\S]*?-->\n?', '', orig_text)
    orig_s = re.sub(r'!\[img-\d+\.jpeg\]\(img-\d+\.jpeg\)\n?', '', orig_s)
    orig_s = re.sub(r'^\d{1,3}\s*\n', '', orig_s, flags=re.MULTILINE)
    orig_s = re.sub(r'^[0-9]+ [·•] [A-Z\s\-]+\n?', '', orig_s, flags=re.MULTILINE)
    first_h2 = re.search(r'^##\s', orig_s, re.MULTILINE)
    if first_h2:
        toc_block = orig_s[:first_h2.start()]
        cleaned_toc = re.sub(r'^.+\d{1,3}\s*$\n?', '', toc_block, flags=re.MULTILINE)
        orig_s = cleaned_toc + orig_s[first_h2.start():]
    orig_s = re.sub(r'\n{3,}', '\n\n', orig_s)

    rep_s = re.sub(r'<!--[\s\S]*?-->\n?', '', rep_text)
    rep_s = re.sub(r'\n{3,}', '\n\n', rep_s)

    ratio = difflib.SequenceMatcher(None, orig_s.splitlines(), rep_s.splitlines()).ratio()
    issues = []
    if ratio < 0.95:
        issues.append(f"Low preservation: {ratio*100:.1f}%")
    if re.findall(r'^\{[0-9]+\}-+', rep_text, re.MULTILINE):
        issues.append("Page-break artifacts remain")
    if re.findall(r'!\[img-\d+\.jpeg\]\(img-\d+\.jpeg\)', rep_text):
        issues.append("Raw OCR image placeholders remain")
    if re.findall(r'\[tbl-\d+\.md\]\(tbl-\d+\.md\)', rep_text):
        issues.append("Dead tbl links [CRITICAL]")
    rep_lines = rep_text.splitlines()
    from pipeline.stages.stage_2_repair import _protected_paragraph_indices, is_clinical
    protected = _protected_paragraph_indices(rep_lines)
    unprotected_piracy = [
        l for i, l in enumerate(rep_lines)
        if i not in protected and (re.search(r'[ঀ-৿]{5,}', l) or not is_clinical(l) and re.search(r'[ঀ-৿]{2,}', l))
    ]
    if any(re.search(p, rep_text) for p in [r't\.me/', r'apps?\.apple\.com']) or bool(unprotected_piracy):
        issues.append("Piracy content still present [CRITICAL]")
    h1s = [l for l in rep_text.splitlines() if re.match(r'^# [^#]', l)]
    if len(h1s) > 1:
        issues.append(f"{len(h1s)} H1 headers (expect 1)")

    verdict = "PASSED" if not issues else "ISSUES - fix before Stage 4"
    return {
        "preservation_percent": round(ratio * 100, 1),
        "h1_count": len(h1s),
        "issues": issues,
        "verdict": verdict,
    }


def decide_checkpoint_action(result):
    """CP-02: PASSED -> complete; anything else -> blocked. Returns
    ("complete" | "blocked", stage_metadata_dict) — the caller (SKILL.md's
    thin wrapper) picks mark_stage_complete/mark_stage_blocked accordingly.
    Never returns "complete" for a non-PASSED verdict."""
    metadata = {
        "preservation_percent": result["preservation_percent"],
        "verdict": result["verdict"],
        "issues_found": len(result["issues"]),
    }
    if result["verdict"] == "PASSED":
        return "complete", metadata
    metadata["issues"] = result["issues"]
    return "blocked", metadata
