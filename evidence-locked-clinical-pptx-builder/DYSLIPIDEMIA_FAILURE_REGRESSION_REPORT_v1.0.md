# Dyslipidemia Failure Regression Report — v2.2.0

## Evidence set

- Source A SHA-256: `038a50fc4ad48297b2932a15800174f37126e3dfca3187c8876063a756a943d5`
- Source B correction SHA-256: `eb8689b77b482c7b03592fc37f6ffee59a32f209d4aa91fc4edba3f768a31502`
- v0.9 pre-canonical SHA-256: `3ee656da8a5a2040fc343d64ae78123e24864bce8fa8f529d757da1bebc90f75`
- Claude v0.9.1 repair SHA-256: `6a0c21495010838fdec8c7b97a44c587d3501c415fa63c613098dcbace1c28b6` (regression evidence only, not clinical authority)
- v1.0 canonical SHA-256: `d90ade0c69593939cd5a860ca1d441d05f07ad13a08bd44258edf59fa8cb38a0`

Direct PPTX inspection of v1.0 found 300 slides and 130 unique `CASE-###` IDs. Source A contains an additional recommendation in §4.2.8.6, Adults With Heart Failure: adults with HFrEF without clinical ASCVD or another LLT indication should not have LLT initiated to reduce clinical events or mortality (COR 3: No Benefit, LOE A). This is the 131st source recommendation class that the former downstream-only coverage model could miss.

## Would v2.2.0 have blocked defective v1.0?

| Failure | v2.2.0 answer |
|---|---|
| 130/131 source recommendation completeness | YES — deterministically |
| Wrong section/chapter labels | YES — deterministically against source-native inventory |
| Unrelated source text under recommendation | YES — deterministically for known contamination/unbound objects; otherwise mandatory semantic adjudication, fail closed |
| Wrong footnote binding | YES — deterministically |
| Missing required footnote definition | YES — deterministically |
| Answer-visible CASE/DECIDE prompts | YES — deterministically for action predicates; synonym/paraphrase leakage requires mandatory semantic adjudication, fail closed |
| Fragment prompts | YES — deterministically plus mandatory semantic review |
| Clinically meaningful `≥` → `>` or unit mutation | YES — deterministically |
| Unsupported repairs (tier, footnote reassignment, source-object relocation, clinical wording) | YES — deterministically from repair-fidelity ledger |
| Promotion with unresolved CRITICAL/HIGH defects | YES — deterministically blocked |

## Concrete observed regression examples

- v1.0 retains only 130 case IDs, so source inventory completeness would fail before downstream case coverage could certify the corpus.
- v1.0 CASE-072 remains under `05 Severe hypercholesterolemia & FH` although it is a diabetes recommendation; source-section attribution would fail.
- v1.0 CASE-057 DECIDE includes `is recommended...`; prompt predicate leakage would fail.
- v1.0 CASE-072 DECIDE includes `it may be reasonable...`; prompt predicate leakage would fail.
- v1.0 CASE-060 displays the inclisiran `‡`-linked definition separately while the dyslipidemia dossier documents incorrect/missing marker-definition treatment elsewhere; binding records must now prove the association before display or notes relocation.
- v0.9 contains explicit header/DOI/table contamination and unrelated table content; the v2.2.0 boundary fixture reproduces these classes without packaging the complete deck.

Conclusion: the defective v1.0 artifact cannot reach `FULLY_CERTIFIED_CANONICAL` under the v2.2.0 gates. Any open CRITICAL/HIGH semantic defect returns `REPAIR_REQUIRED` regardless of render or independent visual-QA success.
