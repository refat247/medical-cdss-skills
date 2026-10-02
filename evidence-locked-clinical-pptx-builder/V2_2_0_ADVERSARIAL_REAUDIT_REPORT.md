# v2.2.0 Adversarial Re-Audit

Adversarial cases exercised after initial implementation:

- source recommendation count off by one;
- duplicated source-row accounting;
- one node mapped to two source rows;
- one node mapped to no source row;
- correct page with wrong source section/chapter;
- footnote text with wrong marker;
- footnote moved to unrelated recommendation;
- prompt with explicit action predicate;
- prompt with semantically leaking synonym requiring adjudication;
- coherent-looking but semantically failed prompt;
- meaningless fragment prompt;
- `≥` changed to `>`;
- `mg` changed to `g`;
- source-native typo silently changed under exact policy;
- audience tier changed without authority;
- table relocated without source link;
- visual/independent-QA PASS while semantic CRITICAL/HIGH remains.

One defect was discovered during the adversarial pass: the first implementation did not explicitly reject a decision node with a blank `source_recommendation_id`. It was repaired in `source_inventory_completeness.py`; `extraction_orphan_node.csv` and a new regression test were added. Full suite then reran successfully.

Final adversarial result: PASS.
