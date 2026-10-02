# v2.2.1 Adversarial Re-audit

Adversarial cases executed after repair:

- `source_lock=WAIVED` with all other gates passing: **does not certify**.
- every non-independent required gate set to `WAIVED`: **does not certify**.
- unknown/new HIGH defect family OPEN: **REPAIR_REQUIRED**.
- unknown/new CRITICAL defect family OPEN: **REPAIR_REQUIRED**.
- 38-table census totaling 131 expected recommendations vs 130-row inventory: **SOURCE_INVENTORY_CERTIFICATION FAIL**.
- same census vs 131-row inventory: **PASS**.
- census not independent from inventory generation: **FAIL**.
- `EXTRACTED` with blank decision node: **SOURCE_EXTRACTION_COMPLETENESS FAIL**.
- explicit adjudicated `EXPLANATORY_ONLY` disposition: **PASS**.
- valid recommendation marker→footnote binding using standard template: **PASS**.
- wrong marker / wrong recommendation owner / required definition dropped: **FAIL**.
- correctly declared table-scoped footnote: **PASS**.
- citation `1,2` removal and superscript citation removal: **PASS**.
- `LDL-C ≥190`→`≥120`, `180 mg`→`80 mg`, and `7.5%`→`5%`: **FAIL**.
- user-authority-only clinical threshold change: **FAIL**.
- verified newly approved/relocked source support: **can PASS**.
- package closure with pytest/bytecode artifacts present in the source tree: **artifacts excluded**.

No new fail-open defect was found in this adversarial pass.
