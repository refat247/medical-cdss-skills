# Regression Corpus

`tests/fixtures/good.pptx` should produce no hard preflight errors.

`tests/fixtures/overflow.pptx` must produce at least one hard geometry or overflow finding.

`tests/fixtures/contrast.pptx` must produce a contrast finding.

`tests/fixtures/clinical_bad.pptx` must produce at least one clinical lint error.

`tests/fixtures/missing_font.pptx` must produce a font-substitution error when the selected font is unavailable.

`tests/fixtures/dense_citations.pptx` must produce a density or citation-related warning/advisory without being mislabeled as a hard clinical error.

The corpus is intentionally synthetic. It checks detector behavior and does not replace visual review or clinician review.
