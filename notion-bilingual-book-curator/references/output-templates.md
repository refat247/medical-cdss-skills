# Output Templates

## Source Audit

**Verdict:** PASS / PASS WITH TARGETED REPAIR / FAIL

**Material defects:** concise evidence-backed findings.

**Preserve:** what must not change.

**Next action:** one bounded step.

## Book Audit

**Verdict:** PASS / PASS WITH TARGETED REPAIR / FAIL

Then assess:
- content integrity;
- bilingual consistency;
- jargon accessibility;
- readability;
- navigation;
- production defects;
- regression/diff result when a previous artifact is available.

Separate blocking defects from optional polish.

## Jargon Coverage Audit

**Verdict:** COMPLETE / PARTIAL / MATERIAL GLOSSARY GAP

Report:
- local glossary coverage;
- reader-critical missing grouped headwords;
- terms that should remain external-glossary only;
- terms excluded as proper names/products/models;
- exact locked expansion count if a patch is recommended.

## Repair Prompt

Return one copy/paste-ready prompt with:
- repair-only title;
- protected-content rules;
- numbered exact repairs;
- final exported-artifact QA;
- regression recheck;
- required repair report.

## Freeze Audit

PASS — FREEZE READY

or

FAIL — FREEZE REPAIR REQUIRED

If FAIL:
- blocker;
- evidence/location;
- smallest patch.

Do not accept builder claims as verification when the artifact is available.
