# Audit Rubric

Severity:
- BLOCKER — likely data corruption, wrong semantics, duplicate source of truth, or unusable primary workflow.
- HIGH — repeated mobile friction or error risk affecting routine work.
- MEDIUM — meaningful but non-blocking inefficiency or clarity defect.
- LOW — optional polish.

For each finding record:
`Dimension | Severity | Evidence | Mobile impact | Smallest safe repair | Verification`

Required dimensions:
PRIMARY ACTION / TAB ORDER; VIEWPORT; CONTEXT; ENTRY FRICTION; SOURCE OF TRUTH; VALIDATION; COMPLETENESS; STATUS/SCHEDULE; VISUAL SEMANTICS; NAVIGATION; MOBILE DASHBOARD; PERFORMANCE; PROTECTION; CONVERSION/NATIVE STATE; REGRESSION.

Native conversion findings should explicitly consider timezone, merged ranges, freeze, protection, stale conditional formatting, navigation behavior, and whether repaired state was re-read after mutation.