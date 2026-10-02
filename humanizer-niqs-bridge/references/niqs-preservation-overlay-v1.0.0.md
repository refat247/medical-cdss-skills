# NIQS Preservation Overlay v1.0.0

## Precedence

Evidence and governance correctness outrank stylistic cleanup.

When Humanizer and NIQS conflict, preserve the evidence-bearing wording or value.

## Protected material

Do not cosmetically rewrite:
- raw evidence and quoted evidence;
- canonical or immutable source text;
- protected corpus material;
- clinical and legal meaning;
- safety warnings and uncertainty statements;
- evidence, audit, canonical, workflow, rule, review, and decision states;
- exact claim/source-card fields;
- provenance that changes trust or reproducibility;
- benchmark, qrel, chunk, case, model, version, and hash identifiers;
- code, commands, paths, YAML/JSON, formulas, URLs, and exact technical literals;
- dates, numbers, measurements, rankings, and citations;
- frozen or dated artifacts whose original wording is part of provenance.

## Pattern 25 rule

Keep process/sourcing narration when it changes evidence interpretation, provenance, verification, reproducibility, auditability, or permitted conclusions.

## Pattern 26 rule

Compress known context in replies and handoffs. Preserve sufficient context on standalone pages so they remain intelligible outside the originating conversation.

## Fail-safe

If an edit could change evidence meaning and the change cannot be proven safe, leave the source wording unchanged.
