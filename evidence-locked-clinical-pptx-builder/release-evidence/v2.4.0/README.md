# Release Evidence — evidence-locked-clinical-pptx-builder v2.4.0

This directory is the durable audit/reconstruction archive for **v2.4.0**. It is separate from runtime source so evidence cannot be mistaken for executable instructions.

## Release identity
- Skill: `evidence-locked-clinical-pptx-builder`
- Version: `2.4.0`
- Original package base: `9a164223f6f6e04ff2982d4823d4dd08dce3e989`
- v2.4.0 source merge: `281c1553e341860c3f69ca829dc671b72e7246bb`
- Original release PR: `#4`
- Tests: **110 passed**
- Canonical source after merge: **248/248 files present**

## Embedded in Git history
- complete 248-file source ZIP
- 31-file delta ZIP and original patch
- changed-file ledger and original commit handoff
- 193-slide polished reference deck
- extracted machine-readable test reports and visual-review ledger
- SHA-256 integrity ledger

## Large aggregate archives not embedded
Two reconstructed aggregate ZIPs were byte-verified but could not be attached by the available GitHub connector because it has no local-file/release-asset upload primitive:
- `delivery/ALL_DELIVERABLES.zip` — SHA-256 `97c95cf7f9389a39a43b031b251347ac62581cb2de9cde34349658c40a6b4da9`
- `test-evidence/test-run-evidence.zip` — SHA-256 `0d63d5b5bda046e76d5e8780d27efccfcf592cf1621f8870b12c74d32d8a3ace`

Their contents are represented by the individually embedded source package, patch/delta, polished deck, reports/ledger, and the integrity ledger. See `UNEMBEDDED_LARGE_ARTIFACTS.md` for the exact recovery boundary.

## Certification boundary
The preserved test run remains `RENDER-UNCERTIFIED / POWERPOINT-RENDER-PENDING`; the per-slide visual-review ledger was blank. Archival presence does not upgrade certification.

## Rule
Active skill files are canonical executable source. `release-evidence/` is immutable historical evidence and must not be used as runtime instructions. Future releases add a new version directory rather than overwriting this one.
