# v2.1.0 Repair Report

## Repairs made

1. `independent_review_gate.py`
   - rejected simple PASS-marker reports;
   - required structured manifest fields;
   - required one slide-by-slide finding per slide;
   - enforced no clinical-change authority;
   - made required-policy waivers return `INDEPENDENT-QA-UNCERTIFIED`.

2. `render_qa_gate.py`
   - added render-set SHA-256;
   - added optional render manifest output;
   - added `--require-ledger`;
   - integrated domain-complete visual ledger validation.

3. `visual_review_ledger.py`
   - added `PASS_WITH_WARNINGS` and independent-QA uncertain status handling;
   - added required domain columns for projector/visual/UI review.

4. Documentation and prompt repairs
   - updated SKILL.md, README, CHANGELOG, activation smoke test and independent visual-QA handoff.

5. Regression fixtures/tests
   - added structured independent-review fixture;
   - added weak PASS-marker fixture;
   - added domain-complete visual-review ledger fixture;
   - added final-artifact visual-failure class fixture.
