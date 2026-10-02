# Final MI Artifact Regression Report v1.0

## Artifact identification

- Uploaded file: `LOW_RESOURCE_MI_CASE_BASED_DERIVATIVE_v1.8_ECG_IMAGE_PRACTICE_REVIEW_GGOGLE_SLIDE (1)(1).pptx`
- SHA-256: `8f1ae8122184048113bda81d954118a321353ee6290d59b0aeaa26a82e2abfad`
- Physical PPTX slides: **65**
- Numbered teaching slides visible in deck: **61**
- Product type: **later low-resource/district-hospital derivative**, not one of the seven canonical products used in the original v2.0.0 regression.
- Deck identity from the artifact: case-based ACS/MI; district-hospital decisions and ward/discharge continuity; no on-site PCI; fibrinolysis may be unavailable or not routinely delivered; 2023 ESC ACS management and 2026 Fifth UDMI diagnosis; local capability is a scenario constraint, not guideline evidence.

## Relationship to v2.0.0 regression

The v2.0.0 regression mapped the earlier canonical family: Master Core, Live 70, 60-min, 45-min, 30-min, Advanced/Consultant and Reference/Backup products. This uploaded deck is a later derivative and was therefore **absent** from that regression. The previous regression is valid for the product family it tested but incomplete for the actual final low-resource artifact.

## 100% visual regression

- Rendered pages inspected: **65/65**
- Visual-review ledger rows: **65/65**
- Render QA gate: **PASS**
- Rendered slide-set SHA-256: `ee1a2839d3c9107f7777d835e715c22bc23983b81cf0342a751885e3b6742846`
- Automated PPTX preflight: **not clean PASS** because it intentionally flags small source/footer labels and heuristic overlaps.
- Preflight issue count: **1**
- Preflight warning count: **4**
- Minimum detected font: **6.0 pt**

## Visual findings

The final deck achieves the key teaching pattern: `CASE/DECIDE -> audience commitment -> SOURCE REVEAL -> guideline/source rationale`. It visibly separates guideline evidence from local operational constraints. ECG practice images are large enough for visual discussion, and image slides preserve user-supplied-asset cautions.

Residual adjudicated warning class: source/footer/provenance labels are frequently small. The deck mitigates this with detailed speaker notes, but the skill should continue to flag this class and require explicit adjudication rather than silently passing it.

## Regression conclusion

The artifact does not require MI clinical-content changes. It does require the reusable skill to enforce stronger independent visual QA, structured review manifests and domain-complete per-slide visual ledgers.
