# v2.0.0 Prose-vs-Code Enforcement Audit v1.0

## Scope

Audited v2.0.0 implementation against the actual final MI artifact requirement, focusing on:

- `scripts/independent_review_gate.py`
- `scripts/render_qa_gate.py`
- `scripts/visual_review_ledger.py`
- `scripts/pptx_preflight.py`

## Findings

| Domain | v2.0.0 prose | v2.0.0 code behavior | Defect | v2.1.0 repair |
|---|---|---|---|---|
| Independent QA | Strongly preferred / handoff available | could accept simple PASS marker; waiver could pass | Too permissive for final high-stakes clinical release | structured manifest required; required-policy waiver cannot certify |
| Render QA | 100% render required | render count checked; ledger optional unless supplied | could pass without per-slide visual ledger | `--require-ledger`; render set hash and manifest |
| Visual ledger | per-slide review needed | minimal columns/statuses | insufficient domain evidence for projector/UI/UX review | required visual-domain columns |
| PPTX preflight | structural/mechanical checks | sensitive to font/source-label, overlap, DPI, crop/title | useful but cannot certify visual quality | retained as structural gate; paired with render ledger and independent QA |

## Conclusion

v2.0.0 prose captured the concept but code enforcement was incomplete. v2.1.0 repairs the key fail-open pathways.
