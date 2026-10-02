# v2.2.1 Hardening Report

## Scope
Focused patch of released v2.2.0. No dyslipidemia deck was rebuilt or repaired. No frozen MI clinical artifact was modified.

## Exact repairs
1. **Semantic promotion waiver bug** — every non-independent required gate now accepts only `PASS`/`CERTIFIED`. `WAIVED` is rejected. Independent visual QA can be waived only when the policy is `required_unless_explicit_user_waiver` and an explicit waiver reason/flag is recorded.
2. **Fail-closed CRITICAL/HIGH defects** — every unresolved CRITICAL/HIGH defect blocks canonical promotion regardless of defect-family name. The prior blocking-family allowlist was removed.
3. **True source→inventory certification** — added `scripts/source_inventory_certification.py`, `templates/source_structure_census.csv`, and `schemas/source_structure_census.schema.json`. Census must be independent from the inventory-generation path or semantically adjudicated. `SOURCE_INVENTORY_CERTIFICATION` is a required, non-waivable promotion gate.
4. **Blank decision-node accounting** — `EXTRACTED` with blank `decision_node_id` fails. Explicit non-node dispositions require reason, reviewer, and semantic-review PASS. Unknown/blank accounting statuses fail.
5. **Footnote binding data model** — standard ledger is now one row per recommendation-footnote binding. Dynamic `footnote_marker__F1` columns are deprecated. Legacy v2.2.0 ledgers remain readable, but new template/schema/validator use explicit marker, source owner/scope, required-for-meaning, display location, and adjudication fields.
6. **Citation-number normalization** — bibliographic citation removal is allowed only for recognized citation syntax and only when non-citation text remains unchanged. Thresholds, doses, units, percentages, ages/durations, ranges, COR/LOE, operators, footnote markers, and negation remain protected.
7. **Clinical repair authority** — clinical/source factual mutations require verified support from a currently approved locked source. User authority alone is insufficient. New sources require formal boundary expansion/relock first.
8. **Release hygiene** — `.pytest_cache/`, `__pycache__/`, `*.pyc`, and `*.pyo` are excluded by package closure and manifest tooling.
9. **Project state order** — now explicitly: `evidence_lock → source_structure_census → source_recommendation_inventory → source_inventory_certification → decision_node_extraction → source_extraction_completeness → extraction_audit → cross_source_reconciliation → …`.

## Version
- version: `2.2.1`
- immediate predecessor: `2.2.0`
- breaking change: `false`
