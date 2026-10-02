# Deterministic vs Semantic Enforcement Matrix — v2.2.1

| Control | Enforcement |
|---|---|
| source census exact table/row counts when structurally enumerable | DETERMINISTICALLY_ENFORCED |
| source census when deterministic enumeration is unreliable | SEMANTIC_REVIEW_REQUIRED; fail closed |
| census independence from inventory-generation pathway | DETERMINISTICALLY_ENFORCED attestation + reviewer |
| source inventory count vs certified census | DETERMINISTICALLY_ENFORCED |
| source inventory → extraction accounting | DETERMINISTICALLY_ENFORCED |
| explicit non-node disposition | SEMANTIC_REVIEW_REQUIRED; fail closed |
| running header/DOI/page contamination | DETERMINISTICALLY_ENFORCED where pattern-detectable |
| subtle recommendation boundary ambiguity | SEMANTIC_REVIEW_REQUIRED; fail closed |
| recommendation-scoped footnote marker/owner | DETERMINISTICALLY_ENFORCED |
| broader table/section footnote semantic applicability | SEMANTIC_REVIEW_REQUIRED when not source-structurally explicit |
| source section/table ID mismatch | DETERMINISTICALLY_ENFORCED |
| prompt explicit action leakage/fragments | DETERMINISTICALLY_ENFORCED |
| synonym/paraphrastic answer leakage | SEMANTIC_REVIEW_REQUIRED; fail closed |
| clinical threshold/dose/unit/%/age/duration/operator mutation | DETERMINISTICALLY_ENFORCED |
| bibliographic citation-number removal | DETERMINISTICALLY_ENFORCED conservatively |
| clinical repair authority | DETERMINISTICALLY_ENFORCED source approval/lock checks |
| all unresolved CRITICAL/HIGH defects | DETERMINISTICALLY_BLOCK_PROMOTION |
| non-independent required gate WAIVED | DETERMINISTICALLY_BLOCK_PROMOTION |
| independent visual QA waiver | POLICY-GOVERNED explicit waiver only |
| release cache/bytecode hygiene | DETERMINISTICALLY_ENFORCED |
