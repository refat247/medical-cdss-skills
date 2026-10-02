# Migration Notes — v2.2.0 → v2.2.1

v2.2.1 is a backward-compatible hardening patch. It does not rebuild the MI workflow or alter frozen clinical artifacts.

## Required state/order change
Projects using exhaustive guideline extraction should insert:

`evidence_lock → source_structure_census → source_recommendation_inventory → source_inventory_certification → decision_node_extraction → source_extraction_completeness → extraction_audit → reconciliation`

`SOURCE_INVENTORY_CERTIFICATION` is distinct from `SOURCE_EXTRACTION_COMPLETENESS`: the first proves the inventory matches an independently established source census; the second proves every inventory recommendation has exactly one extraction-accounting record.

## Footnote ledger
New projects should use one row per recommendation-footnote binding in `templates/footnote_binding_ledger.csv`. Legacy v2.2.0 ledgers remain readable by the validator but should be migrated.

## Repair authority
Clinical/source-factual changes require validated support from a currently approved locked source. User authority alone is insufficient. To add a new clinical source, expand and relock the evidence boundary before the repair is considered valid.

## Promotion
All non-independent required gates accept only PASS/CERTIFIED. Only independent visual QA can use an explicit waiver, and only when policy is `required_unless_explicit_user_waiver` with the waiver explicitly recorded.

## Packaging
`.pytest_cache/`, `__pycache__/`, `*.pyc`, and `*.pyo` are excluded automatically from manifests and ZIPs.
