#!/usr/bin/env python3
"""
clinical_lint.py -- clinical-safety and evidence-discipline lint for slide text.

Reads a .pptx (or plain text/markdown) and flags patterns that are dangerous or
non-compliant in *clinical* teaching material specifically. This is the layer a
generic slide-design tool does not have.

Every rule carries the authority it derives from, and the jurisdiction that
authority binds, so the operator can tell a hard requirement from a convention.

    python3 clinical_lint.py deck.pptx [--jurisdiction us|eu|none]
            [--accredited] [--stale-year 2021] [--json out.json]

Severity
    ERROR      medication-safety or accreditation violation
    WARN       likely violation, or safety-relevant ambiguity
    ADVISORY   evidence-communication weakness, not a rule breach
    INFO       reported for the operator's judgement

Exit 1 if any ERROR. Requires python-pptx only for .pptx input.
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict

# --------------------------------------------------------------------------- #
# RULE TABLE
#
# Each entry: (id, severity, compiled regex, message, authority, jurisdiction)
# Authority strings are deliberately verbose -- an operator reading a failure
# needs to know whether they are looking at a law, an accreditor rule, or taste.
# --------------------------------------------------------------------------- #

R = re.compile

ABBREV_RULES = [
    ("MED-U", "ERROR", R(r"(?<![A-Za-z])(\d+\s*)U(?![A-Za-z])"),
     "Dose written with 'U' for units. 'U' is read as 0, 4 or cc; write 'unit(s)' in full.",
     "ISMP List of Error-Prone Abbreviations, Symbols and Dose Designations (2024, T2, voluntary, no legal force). Also on The Joint Commission minimum 'Do Not Use' list (IM.02.02.01 EPs 2-3) -- but note TJC's own stated scope is 'all orders, preprinted forms, and medication-related documentation', which does NOT include teaching slides; TJC binds accredited ORGANISATIONS, not presenters", "us-origin/global-practice"),

    ("MED-IU", "ERROR", R(r"(?<![A-Za-z])IU(?![A-Za-z])"),
     "'IU' (international unit) is misread as IV or 10; write 'international unit(s)'.",
     "ISMP List of Error-Prone Abbreviations, Symbols and Dose Designations (2024, T2, voluntary, no legal force). Also on The Joint Commission minimum 'Do Not Use' list (IM.02.02.01 EPs 2-3) -- but note TJC's own stated scope is 'all orders, preprinted forms, and medication-related documentation', which does NOT include teaching slides; TJC binds accredited ORGANISATIONS, not presenters", "us-origin/global-practice"),

    ("MED-QD", "ERROR", R(r"(?<![A-Za-z])(q\.?\s?d|Q\.?D|q\.?o\.?d|Q\.?O\.?D|qod|QOD)(?![A-Za-z])"),
     "Latin dosing abbreviation (QD/QOD). The period after Q and the o are misread, "
     "swapping once-daily and every-other-day; write 'daily' / 'every other day'.",
     "ISMP List of Error-Prone Abbreviations, Symbols and Dose Designations (2024, T2, voluntary, no legal force). Also on The Joint Commission minimum 'Do Not Use' list (IM.02.02.01 EPs 2-3) -- but note TJC's own stated scope is 'all orders, preprinted forms, and medication-related documentation', which does NOT include teaching slides; TJC binds accredited ORGANISATIONS, not presenters", "us-origin/global-practice"),

    ("MED-MS", "ERROR", R(r"(?<![A-Za-z])(MS|MSO4|MgSO4)(?![A-Za-z0-9])"),
     "'MS'/'MSO4'/'MgSO4' confuse morphine sulfate with magnesium sulfate; "
     "write the drug name in full.",
     "ISMP List of Error-Prone Abbreviations, Symbols and Dose Designations (2024, T2, voluntary, no legal force). Also on The Joint Commission minimum 'Do Not Use' list (IM.02.02.01 EPs 2-3) -- but note TJC's own stated scope is 'all orders, preprinted forms, and medication-related documentation', which does NOT include teaching slides; TJC binds accredited ORGANISATIONS, not presenters", "us-origin/global-practice"),

    ("MED-MCG", "ERROR", R(r"[µμ]g"),
     "Greek mu (µg) is misread as 'mg' -- a 1000-fold error. Write 'mcg'.",
     "ISMP List of Error-Prone Abbreviations (2024, T2). NOT on The Joint Commission 'Do Not Use' list", "us-origin/global-practice"),

    ("MED-TRAILZERO", "ERROR", R(r"\b\d+\.0+\s*(?=(mg|mcg|g|kg|mL|ml|L|units?|unit)\b)"),
     "Trailing zero after a decimal point (e.g. '1.0 mg'). If the point is missed "
     "the dose is read 10-fold high. Write '1 mg'.",
     "ISMP List of Error-Prone Abbreviations, Symbols and Dose Designations (2024, T2, voluntary, no legal force). Also on The Joint Commission minimum 'Do Not Use' list (IM.02.02.01 EPs 2-3) -- but note TJC's own stated scope is 'all orders, preprinted forms, and medication-related documentation', which does NOT include teaching slides; TJC binds accredited ORGANISATIONS, not presenters", "us-origin/global-practice"),

    ("MED-NAKEDDEC", "ERROR", R(r"(?<![\d.])\.\d+\s*(mg|mcg|g|kg|mL|ml|L|units?)\b"),
     "Naked decimal without a leading zero (e.g. '.5 mg'). If the point is missed "
     "the dose is read 10-fold high. Write '0.5 mg'.",
     "ISMP List of Error-Prone Abbreviations, Symbols and Dose Designations (2024, T2, voluntary, no legal force). Also on The Joint Commission minimum 'Do Not Use' list (IM.02.02.01 EPs 2-3) -- but note TJC's own stated scope is 'all orders, preprinted forms, and medication-related documentation', which does NOT include teaching slides; TJC binds accredited ORGANISATIONS, not presenters", "us-origin/global-practice"),

    ("MED-CC", "WARN", R(r"(?<![A-Za-z])cc(?![A-Za-z])"),
     "'cc' is misread as 'u' or '00'; write 'mL'.",
     "ISMP List of Error-Prone Abbreviations (2024, T2). NOT on The Joint Commission 'Do Not Use' list", "us-origin/global-practice"),

    ("MED-AT", "ADVISORY", R(r"@\s*\d"),
     "'@' is misread as '2'; write 'at'. ISMP flags this with a dagger, i.e. "
     "relevant mostly to HANDWRITTEN communication -- on typeset slides the "
     "misread mechanism is much weaker, so this is advisory only.",
     "ISMP List of Error-Prone Abbreviations, Symbols and Dose Designations (2024, T2, voluntary, no legal force). Also on The Joint Commission minimum 'Do Not Use' list (IM.02.02.01 EPs 2-3) -- but note TJC's own stated scope is 'all orders, preprinted forms, and medication-related documentation', which does NOT include teaching slides; TJC binds accredited ORGANISATIONS, not presenters", "us-origin/global-practice"),

    ("MED-EYEEAR", "WARN",
     R(r"(?<![A-Za-z])(AD|AS|AU|OD|OS|OU)(?![A-Za-z])"),
     "Latin laterality abbreviation (AD/AS/AU, OD/OS/OU) confuses ear with eye; "
     "write 'right ear' / 'left eye' etc. Note OD also means 'once daily' and overdose.",
     "ISMP List of Error-Prone Abbreviations (2024, T2). NOT on The Joint Commission 'Do Not Use' list", "us-origin/global-practice"),

    ("MED-NOSPACE", "ADVISORY", R(r"\b\d+(mg|mcg|g|kg|mL|ml|units?)\b"),
     "No space between number and unit (e.g. '10mg'); the unit can merge with the "
     "digits. Insert a space.",
     "ISMP dose-designation guidance", "us-origin/global-practice"),
]

EVIDENCE_RULES = [
    ("EV-ABSOLUTE", "ERROR",
     R(r"\b(always|never|all patients|in every (?:case|patient)|"
       r"contraindicated in all|invariably|100% of patients)\b", re.I),
     "Absolute clinical claim. Accredited education must present a fair and balanced "
     "view of options; absolutes rarely survive the evidence and cannot be hedged by "
     "the speaker's tone once the slide is reused.",
     "ACCME Standard 1 (Ensure Content is Valid): recommendations 'must be based on "
     "current science, evidence, and clinical reasoning, while giving a fair and "
     "balanced view of diagnostic and therapeutic options'", "us (accredited CME)"),

    ("EV-RECNOSRC", "WARN",
     R(r"\b(first[- ]line|second[- ]line|drug of choice|treatment of choice|"
       r"recommended|should (?:be )?(?:give|given|start|started|receive|offered)|"
       r"gold standard)\b", re.I),
     "Patient-care recommendation on a slide with no citation marker detected. "
     "The recommendation needs its source pinned so a reader can check it.",
     "ACCME Standard 1: 'All scientific research referred to, reported, or used ... "
     "must conform to the generally accepted standards of experimental design, data "
     "collection, analysis, and interpretation'", "us (accredited CME)"),

    ("EV-RRONLY", "ADVISORY",
     R(r"\b(\d{1,3}(?:\.\d+)?\s*%\s*(?:relative\s+)?(?:risk\s+)?reduction|"
       r"\bRRR\b|reduced .{0,20}\bby\s+\d{1,3}\s*%)", re.I),
     "Relative effect quoted. Without the absolute risks or an NNT the audience "
     "systematically overestimates benefit. Show both.",
     "Evidence-communication convention (GRADE / EQUATOR reporting norms); "
     "ASSISTANT SYNTHESIS, not an accreditation rule", "none"),

    ("EV-SIGNIF", "ADVISORY",
     R(r"\b(?:statistically\s+)?significant(?:ly)?\b", re.I),
     "'Significant' used with no p-value, confidence interval or effect size nearby. "
     "State the estimate and its precision.",
     "Reporting convention (CONSORT/STROBE item on effect sizes and precision); "
     "ASSISTANT SYNTHESIS", "none"),

    ("EV-EMERGING", "WARN",
     R(r"\b(novel|emerging|promising|cutting[- ]edge|breakthrough|"
       r"paradigm[- ]shift(?:ing)?|game[- ]chang(?:er|ing))\b", re.I),
     "New/evolving-topic language. Permitted, but such areas must be explicitly "
     "labelled as new or evolving within the presentation rather than presented as "
     "settled practice.",
     "ACCME Standard 1: new and evolving topics 'need to be clearly identified as "
     "such within the program and individual presentations'", "us (accredited CME)"),
]

JURISDICTION_RULES = [
    ("JUR-FDA", "WARN",
     R(r"\b(FDA[- ]approved|FDA approval|not FDA[- ]approved|"
       r"EMA[- ]approved|MHRA[- ]approved)\b", re.I),
     "Regulatory approval status asserted. Approval is jurisdiction-specific: a drug "
     "approved by one regulator may be unapproved, differently indicated, or "
     "unavailable elsewhere. Name the regulator and date, and say which audience it "
     "applies to.",
     "Regulatory approval is granted per-jurisdiction by the relevant authority "
     "(FDA / EMA / national regulator)", "all"),

    ("JUR-OFFLABEL", "WARN",
     R(r"\boff[- ]label\b|\bunlicensed\b|\bunapproved use\b|\binvestigational\b", re.I),
     "Off-label / unlicensed use mentioned. Label status must be stated explicitly "
     "with the jurisdiction, not left implicit.",
     "FDA: use of an approved drug for an unapproved indication; label status is "
     "jurisdiction-specific", "all"),
]

CME_RULES = [
    ("CME-TRADENAME", "ERROR",
     R(r"\b(?:®|™)"),
     "Registered-trademark or trademark symbol found in slide text. Educational "
     "materials that are part of accredited education must not contain marketing, "
     "corporate or product logos, trade names, or product group messages.",
     "ACCME Standard 5.2.c: 'Educational materials that are part of accredited "
     "education (such as slides, abstracts, handouts, evaluation mechanisms, or "
     "disclosure information) must not contain any marketing produced by or for an "
     "ineligible company, including corporate or product logos, trade names, or "
     "product group messages.' EU is stricter: EACCME LEE criterion 20 makes display "
     "of brand names or company logos in scientific lectures grounds for automatic "
     "rejection, and criterion 18 permits generic names only.",
     "us + eu (accredited)"),
]

PHI_RULES = [
    ("PHI-AGE90", "ERROR",
     R(r"\b(9[0-9]|1[0-9]{2})[- ]?(?:year|yr)s?[- ]?old\b|\baged?\s+(9[0-9]|1[0-9]{2})\b", re.I),
     "Age 90 or above stated. Under the HIPAA Safe Harbor method all ages over 89 "
     "(and elements of dates indicating such age) must be removed or aggregated into "
     "a single '90 or older' category.",
     "45 CFR 164.514(b)(2)(i)(C) Safe Harbor (last amended 7 Jun 2013). Binds COVERED ENTITIES under US federal law only -- it does not bind a non-US presenter, who is instead subject to their own regime", "us"),

    ("PHI-DATE", "WARN",
     R(r"\b(0?[1-9]|1[0-2])[/-](0?[1-9]|[12][0-9]|3[01])[/-](19|20)\d{2}\b"),
     "Full calendar date in case material. Safe Harbor requires removal of all "
     "elements of dates (except year) directly related to an individual, including "
     "admission and discharge dates.",
     "45 CFR 164.514(b)(2)(i)(C). US covered entities only", "us"),

    ("PHI-MRN", "ERROR",
     R(r"\b(MRN|medical record (?:no|number)|hospital (?:no|number)|NHS number)\b[:\s#]*[\w-]{4,}", re.I),
     "Medical record or health-plan identifier present. Safe Harbor requires removal "
     "of medical record numbers and health-plan beneficiary numbers.",
     "45 CFR 164.514(b)(2)(i)(H) medical record numbers, (I) health plan beneficiary numbers. US covered entities only", "us"),

    ("PHI-INITIALS", "ADVISORY",
     R(r"\bpatient\s+(?:[A-Z]\.?\s?[A-Z]\.?|[A-Z]{2,3})\b"),
     "Patient referred to by initials. Initials are not on the Safe Harbor list but "
     "combined with dates, rare diagnoses or a small catchment they can re-identify. "
     "Prefer 'a woman in her 60s'.",
     "ASSISTANT SYNTHESIS extending 45 CFR 164.514(b)(2)(i)(R) 'any other unique "
     "identifying number, characteristic, or code'. Note the SEPARATE consent duty: "
     "ICMJE II.E requires WRITTEN informed consent and that the patient be shown the "
     "material, and states that 'masking the eye region in photographs of patients is "
     "inadequate protection of anonymity' -- de-identification does not substitute for consent",
     "us + journal norms"),
]

CITATION_MARKER = R(
    r"(\b(19|20)\d{2}\b|\bet al\b|10\.\d{4,9}/|\bdoi\b|\bPMID\b|"
    r"\[\d+\]|\bNEJM\b|\bJAMA\b|\bLancet\b|\bBMJ\b|\bCochrane\b)", re.I)

BOILERPLATE = {
    "accreditation_statement": R(r"is accredited by the Accreditation Council", re.I),
    "credit_designation": R(r"AMA PRA Category 1 Credit", re.I),
    "disclosure": R(r"\b(disclosure|financial relationship|conflict of interest)\b", re.I),
    "mitigation_statement": R(r"relevant financial relationships have been mitigated", re.I),
}


# --------------------------------------------------------------------------- #
def slide_texts(path):
    """Yield (slide_number, text). Accepts .pptx, .txt, .md."""
    if path.lower().endswith(".pptx"):
        from pptx import Presentation
        prs = Presentation(path)
        for i, s in enumerate(prs.slides, 1):
            chunks = []
            for shp in s.shapes:
                if getattr(shp, "has_text_frame", False):
                    chunks.append(shp.text_frame.text or "")
                if getattr(shp, "has_table", False):
                    for row in shp.table.rows:
                        for c in row.cells:
                            chunks.append(c.text or "")
            note = ""
            try:
                if s.has_notes_slide:
                    note = s.notes_slide.notes_text_frame.text or ""
            except Exception:
                pass
            yield i, "\n".join(chunks), note
    else:
        with open(path) as fh:
            yield 1, fh.read(), ""


def applies(rule_jur, target):
    if target == "none":
        return rule_jur in ("all", "none", "us-origin/global-practice")
    if rule_jur == "all":
        return True
    return target in rule_jur or rule_jur in ("us-origin/global-practice",)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path")
    ap.add_argument("--jurisdiction", default="us", choices=["us", "eu", "none"])
    ap.add_argument("--accredited", action="store_true",
                    help="deck is for accredited CME/CPD; enables accreditation gates")
    ap.add_argument("--stale-year", type=int, default=None,
                    help="flag guideline citations older than this year")
    ap.add_argument("--json")
    args = ap.parse_args()

    if not os.path.exists(args.path):
        print("FATAL: no such file: %s" % args.path, file=sys.stderr)
        return 2

    groups = [("medication-safety", ABBREV_RULES),
              ("evidence-discipline", EVIDENCE_RULES),
              ("jurisdiction", JURISDICTION_RULES),
              ("phi", PHI_RULES)]
    if args.accredited:
        groups.append(("cme-compliance", CME_RULES))

    findings = []
    all_text = []
    nslides = 0

    for n, text, note in slide_texts(args.path):
        nslides = max(nslides, n)
        all_text.append(text)
        haystack = text + "\n" + note
        has_cite = bool(CITATION_MARKER.search(haystack))

        for gname, rules in groups:
            for rid, sev, pat, msg, auth, jur in rules:
                if not applies(jur, args.jurisdiction):
                    continue
                for m in pat.finditer(text):
                    # EV-RECNOSRC only fires when the slide has no citation at all
                    if rid == "EV-RECNOSRC" and has_cite:
                        continue
                    if rid == "EV-SIGNIF" and re.search(
                            r"(p\s*[<=>]|\bCI\b|95%|\bHR\b|\bOR\b|\bRR\b)", haystack, re.I):
                        continue
                    findings.append({
                        "slide": n, "group": gname, "rule": rid,
                        "severity": sev, "match": m.group(0).strip()[:60],
                        "message": msg, "authority": auth, "jurisdiction": jur,
                    })
                    break        # one finding per rule per slide

        # stale guideline citations
        if args.stale_year:
            for m in re.finditer(
                    r"\b(guideline|guidance|recommendation|consensus|"
                    r"position statement)\b[^.]{0,80}?\b(19|20)(\d{2})\b", text, re.I):
                yr = int(m.group(2) + m.group(3))
                if yr < args.stale_year:
                    findings.append({
                        "slide": n, "group": "currency", "rule": "CUR-STALE",
                        "severity": "WARN", "match": m.group(0)[:60],
                        "message": "Guidance cited from %d, older than the %d "
                                   "currency threshold. Confirm it has not been "
                                   "superseded, and show the version/date on the slide."
                                   % (yr, args.stale_year),
                        "authority": "ASSISTANT SYNTHESIS; guideline bodies operate "
                                     "review cycles and empirical work finds a "
                                     "substantial share of guidance outdated within "
                                     "a few years",
                        "jurisdiction": "none",
                    })

    # deck-level boilerplate presence
    joined = "\n".join(all_text)
    if args.accredited:
        for key, pat in BOILERPLATE.items():
            if not pat.search(joined):
                sev = "ERROR" if key in ("accreditation_statement",
                                         "credit_designation", "disclosure") else "WARN"
                findings.append({
                    "slide": None, "group": "cme-compliance",
                    "rule": "CME-MISSING-" + key.upper().replace("_", "-"),
                    "severity": sev, "match": "(absent)",
                    "message": "Required accredited-CME element not found in deck "
                               "text: %s." % key.replace("_", " "),
                    "authority": {
                        "accreditation_statement":
                            "ACCME Accreditation Statement policy: the statement "
                            "'must appear on all CME activity materials'",
                        "credit_designation":
                            "AMA PRA: the credit designation statement 'must be "
                            "written without paraphrasing' and used in program "
                            "materials that reference CME credit",
                        "disclosure":
                            "ACCME Standard 3.5: learners must receive disclosure "
                            "(names, companies, nature of relationships) 'before "
                            "engaging with the accredited education'",
                        "mitigation_statement":
                            "ACCME Standard 3.5(d): disclosure must include 'a "
                            "statement that all relevant financial relationships "
                            "have been mitigated'",
                    }[key],
                    "jurisdiction": "us",
                })

    # ---------------- report ------------------------------------------------
    counts = defaultdict(int)
    for f in findings:
        counts[f["severity"]] += 1

    print("=" * 78)
    print("CLINICAL LINT  --  %s" % os.path.basename(args.path))
    print("jurisdiction=%s  accredited=%s  slides=%d"
          % (args.jurisdiction, args.accredited, nslides))
    print("=" * 78)

    for sev in ("ERROR", "WARN", "ADVISORY", "INFO"):
        rows = [f for f in findings if f["severity"] == sev]
        if not rows:
            continue
        print("\n### %s (%d)" % (sev, len(rows)))
        for f in rows:
            loc = "slide %s" % f["slide"] if f["slide"] else "deck"
            print("  - [%s] (%s) %r" % (loc, f["rule"], f["match"]))
            print("      %s" % f["message"])
            print("      AUTHORITY: %s" % f["authority"])
            print("      BINDS: %s" % f["jurisdiction"])

    print("\n" + "-" * 78)
    print("SUMMARY: " + "  ".join("%s=%d" % (k, counts.get(k, 0))
                                  for k in ("ERROR", "WARN", "ADVISORY", "INFO")))
    print("VERDICT: %s" % ("FAIL" if counts["ERROR"] else
                           "PASS-WITH-WARNINGS" if counts["WARN"] else "PASS"))
    print("-" * 78)
    print("NOTE: absence of findings is not a safety certificate. This lints "
          "surface patterns\nin slide text; it cannot judge clinical correctness, "
          "and no jurisdiction outside\nthose named above has been checked.")

    if args.json:
        with open(args.json, "w") as fh:
            json.dump({"file": args.path, "counts": dict(counts),
                       "findings": findings}, fh, indent=1)
        print("JSON written: %s" % args.json)

    return 1 if counts["ERROR"] else 0


if __name__ == "__main__":
    sys.exit(main())
