# Release audit — offline-study-guide v1.2.1

Date: 2026-10-01

## Scope

Governance-only PATCH over v1.2.0. Functional code remains byte-identical to the proven v1.2.0 baseline. No parser, reader-shell, source-preservation, PDF-gate, calculator, reference-contract, eval, or trigger behavior was changed.

## Proven predecessor

- release: `offline-study-guide v1.2.0`
- ZIP SHA-256: `3e674bdf1efd93251c254466bb026694281c5381b449b34142dfe2663d4018c1`
- regression baseline: 59/59 PASS

## v1.2.1 governance gates

- `SKILL.md metadata.version` is canonical: PASS (`1.2.1`)
- visible SKILL version agrees: PASS
- `VERSION` agrees: PASS
- `README.md` agrees: PASS
- `agents/openai.yaml` agrees: PASS
- `MANUAL_ACTIVATION.md` agrees: PASS
- `ACTIVATION_SMOKE_TEST.md` agrees: PASS
- current release is recorded in `CHANGELOG.md`: PASS
- default agent prompt explicitly names `$offline-study-guide`: PASS
- required governance files exist and are non-empty: PASS
- release verifier executes successfully before packaging: PASS
- compiled Python release residue is rejected by the verifier: VERIFIED (carried-over `__pycache__` was detected and removed)
- functional files versus v1.2.0 baseline: BYTE-IDENTICAL
- unchanged functional regression suite: 59/59 PASS

## Archive contract

Final install ZIP must:

- place `SKILL.md` at archive root;
- contain no extra `offline-study-guide/` wrapper directory;
- contain no duplicate paths;
- contain no `__pycache__`/`.pyc` residue;
- match `PACKAGE_MANIFEST.json` file sizes and SHA-256 values.

The final gate is performed after creating the exact ZIP by extracting it into a clean directory and rerunning release verification plus the unchanged 59-check regression suite.

## External state

- Git sync: NOT PERFORMED
- Notion mirror/registry update: NOT PERFORMED
- ChatGPT installation/discoverability: NOT VERIFIED
- Native runtime activation: NOT VERIFIED

Package correctness does not imply any of those external states.
