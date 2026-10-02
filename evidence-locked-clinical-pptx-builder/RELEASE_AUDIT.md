# Release Audit — v2.2.1

## Candidate clean-extraction verification
- candidate ZIP created from the patched tree with runtime/cache exclusion enabled
- ZIP entries: 230
- duplicate entries: 0
- ZIP CRC: PASS
- cache/bytecode entries: 0
- packaged `PACKAGE_MANIFEST.md`: 229 listed files, self excluded, all hashes/sizes verified
- clean extraction test suite: 84/84 PASS
- packaged manifest reverified after clean-extraction test run: PASS (runtime pytest caches ignored by manifest policy)

## Metadata
- version: `2.2.1`
- immediate predecessor: `2.2.0`
- breaking change: `false`
- lineage origin: `1.0.0`
- major predecessor: `2.0.0`

## Clinical/project isolation
- no dyslipidemia PPTX modified
- no frozen MI project artifact modified
- packaged MI regression/reference files listed in `MI_REGRESSION_PRESERVATION_v2.2.1.md` remain byte-identical to v2.2.0

## Final packaging rule
The final archive is rebuilt after this report is inserted, then CRC/duplicates/cache/manifest/tests are rechecked from a clean extraction. The final archive SHA-256 is reported in the external release handoff because embedding a ZIP's own digest inside itself would change that digest.
