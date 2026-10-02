# Dyslipidemia Failure Regression Report v1.1 — v2.2.1

Clinical truth remains Source A + official Source B correction. The dyslipidemia deck and Claude repair are regression evidence only; no deck was modified in this patch.

## Key regression result
The prior v2.2.0 gap is closed: source-inventory certification is now separate from extraction completeness.

Generic dyslipidemia-style fixture:
- 38 recommendation-table census rows
- 131 expected recommendation rows
- 131 inventory rows → **PASS**
- deliberately truncated 130 inventory rows → **FAIL**, even though those 130 could all be accounted for downstream

## Failure classes
- missing source recommendation before inventory: **blocked by SOURCE_INVENTORY_CERTIFICATION**
- missing/blank decision node after inventory: **blocked by SOURCE_EXTRACTION_COMPLETENESS**
- unrelated table/header/neighbor text: **boundary validator / mandatory semantic review**
- wrong source section: **source-section validator**
- wrong marker/footnote ownership or required definition dropped: **footnote-binding validator**
- answer-visible or incoherent DECIDE prompt: **prompt semantic validator**
- clinically meaningful numeric/operator/unit mutation: **normalization validator**
- unsupported clinical repair: **repair-fidelity validator**
- any unresolved CRITICAL/HIGH defect, including a new family: **canonical promotion blocked**
- non-independent required gate marked WAIVED: **canonical promotion blocked**

Conclusion: the defective dyslipidemia v1.0 pattern cannot receive fully certified canonical status under the v2.2.1 gates represented by this regression suite.
