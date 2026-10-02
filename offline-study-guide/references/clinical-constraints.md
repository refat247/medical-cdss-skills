---
description: "Clinical and content rules for medical study-guide HTML. Read before editing doses, cases, or the calculator."
connections: [reader-contract]
---

# Clinical constraints

These guides are study files, not a prescribing system.

- Do not silently rewrite doses, formulas, case conclusions, or guideline claims.
- Report suspected clinical errors with file and location. Status: requires clinical/source review.
- Investigation: Widal case certainty is an open clinical finding. Do not "correct" it without a cited source.
- Medicine calculator: keep IV iron, low-dose dopamine, norepinephrine, and amino acids disabled in the dropdown until a source-backed review. Also reject weights outside 0.5–300 kg. The script gate stays. The calculator stays in Medicine only.
- Reject non-positive and non-finite weights. Do not treat a successful arithmetic string as clinical validation.
- Do not remove repeated passages or isolated numbers unless the user supplies the source page and approves the deletion.
- Do not invent missing figures. Caption unrendered Mermaid as diagram source.
- Correction banners and filenames do not prove clinical approval.
- Bookmark and theme data are per file on `file://`. Tell the user to export bookmarks before moving a copy.
