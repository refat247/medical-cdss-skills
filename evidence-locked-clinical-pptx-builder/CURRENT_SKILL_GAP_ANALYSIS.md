# v2.1.1 Gap Analysis Against Dyslipidemia Regression

Baseline audited: `evidence-locked-clinical-pptx-builder v2.1.1` implementation, not only `SKILL.md`.

| Capability | v2.1.1 state | Evidence from implementation | v2.2.0 action |
|---|---|---|---|
| Source-inventory completeness | MISSING | `decision_node_coverage.py` and `case_coverage_audit.py` start from already-extracted nodes; neither enumerates source recommendation rows | Added `source_inventory_completeness.py` and source-recommendation inventory/accounting templates |
| Source-boundary integrity | MISSING | No validator for headers/DOIs/neighbour headings/unrelated source objects | Added `recommendation_boundary_validator.py` with mandatory semantic boundary review |
| Footnote/marker binding | MISSING | No marker-owner/scope validator | Added `footnote_binding_validator.py` and binding ledger |
| Source-section correctness | DOCUMENTED_ONLY | Provenance utilities validate source IDs/locators, not source-native hierarchy | Added `source_section_validator.py` keyed to source-recommendation inventory |
| Prompt-answer leakage | MISSING | No CASE/DECIDE predicate check | Added `prompt_semantics_validator.py` |
| Prompt coherence | MISSING | No fragment/orphan semantic gate | Added deterministic coherence checks + mandatory semantic status |
| Repair fidelity | DOCUMENTED_ONLY | Repair workflow exists in prose but no authority/content-change validator | Added `repair_fidelity_validator.py` and repair ledger |
| Normalization fidelity | MISSING | No explicit text-handling enum/protected-token comparison | Added `normalization_fidelity_validator.py` and normalization schema |
| Semantic defect severity blocking | MISSING | Promotion uses coarse clinical/mechanical/render/visual states | Added severity-aware semantic defect register + `semantic_promotion_gate.py` |
| Canonical promotion blocking for semantic defects | PARTIAL / INSUFFICIENT | Existing independent visual-QA gate cannot represent dyslipidemia semantic defect families | Added mandatory semantic gates; visual PASS cannot override CRITICAL/HIGH semantic defects |

Root cause: v2.1.1 could prove coverage of what had already been extracted and could strongly certify visual/mechanical quality, but it lacked a source-native completeness layer and semantic assembly/fidelity controls. That allowed a deck to preserve much recommendation wording/COR/LOE while still assembling content incorrectly and still reaching a canonical label.
