# v2 Candidate Repair Report

During adversarial review of the first v2 candidate, the following release-blocking or material gaps were repaired:

1. **Render certification could have been inferred from image-count alone.** Added a per-slide visual review ledger and a gate requiring one final PASS record per slide.
2. **Independent visual review could have been treated as clinical authority.** Added explicit reviewer scope and evidence-isolation rules.
3. **Correction/erratum precedence lacked a deterministic validator.** Added correction/supersession validator and explicit scope requirement.
4. **Derivative reuse lacked a clinical mutation check.** Added stable clinical fingerprint comparison.
5. **v1 preflight could miss many projector defects.** Expanded preflight to ZIP integrity, aspect ratio, out-of-bounds shapes, text-text overlap warnings, role-aware font checks, placeholder text, image DPI/cropping, title and notes checks, with explicit warning that visual fit still requires rendering.
6. **Case occurrence indexing was MI-ID specific.** Added configurable case-ID regex.
7. **Notes presence could be mistaken for notes fidelity.** Added source-map/clinical-lint requirement and documentation separating XML coverage from semantic audit.
8. **Mode/lifecycle ambiguity.** Separated operating mode from project pipeline/lifecycle state.

No MI clinical artifact was edited during these repairs.
