# v2.2.1 Prose ↔ Code Enforcement Audit

| Capability | Code enforcement | Standard artifact | Promotion consequence |
|---|---|---|---|
| Source lock | deterministic validator | evidence lock/source register | non-waivable |
| Source→inventory completeness | deterministic counts when structure is enumerable; semantic/manual review otherwise | `source_structure_census.csv` + source inventory | required non-waivable gate |
| Inventory→extraction completeness | deterministic accounting + adjudicated non-node dispositions | `extraction_accounting.csv` | required non-waivable gate |
| Downstream coverage | deterministic | coverage ledger | required non-waivable gate |
| Recommendation boundaries | deterministic contamination patterns + semantic review | boundary ledger | required non-waivable gate |
| Footnote binding | deterministic owner/marker/scope checks + semantic display adjudication | one-row-per-binding ledger | required non-waivable gate |
| Source hierarchy | deterministic IDs/titles + semantic review where needed | source inventory/node ledger | required non-waivable gate |
| Prompt leakage/coherence | deterministic explicit predicates + semantic review for paraphrastic leakage | prompt semantic ledger | required non-waivable gate |
| Normalization fidelity | deterministic protected clinical tokens + conservative citation parser | normalization ledger | required non-waivable gate |
| Repair fidelity | deterministic authority/source checks + adjudication | repair ledger | required non-waivable gate |
| CRITICAL/HIGH semantic defects | fail-closed for all families | semantic defect register | `REPAIR_REQUIRED` |
| Independent visual QA | structured certifying review or explicit policy-governed waiver | independent review report | only waivable gate |
| Package hygiene | deterministic exclusion + ZIP verification | package manifest/ZIP | release blocker on contamination |

Result: documented v2.2.1 controls have matching executable validators/templates/tests. No capability in this patch is claimed solely because prose describes it.
