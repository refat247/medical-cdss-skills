# Offline Study Guide

**Version:** 1.2.1  
**Status:** stable  
**Lifecycle:** active

`offline-study-guide` builds or repairs a self-contained offline HTML study reader while preserving the supplied source. It supports structured Markdown and DOCX directly and uses guarded structure gates for PDFs, including a narrowly activated layout-aware path for corroborated multi-column textbook PDFs.

## What this release changes

v1.2.1 is a **governance-only PATCH** over v1.2.0. It does not change the parser, reader shell, source-preservation rules, or clinical constraints. It adds package metadata, release verification, activation documentation, and a root-correct install ZIP.

## Canonical version

The canonical version is `metadata.version` in `SKILL.md`. The same release must be mirrored in:

- the visible `Version` line in `SKILL.md`;
- `VERSION`;
- this README;
- `agents/openai.yaml`;
- `CHANGELOG.md`;
- `MANUAL_ACTIVATION.md`;
- `ACTIVATION_SMOKE_TEST.md`;
- `PACKAGE_MANIFEST.json`.

Run `python3 scripts/verify_release.py` before packaging. Run it again with `--archive PATH.zip` after packaging.

## Package entry points

- `SKILL.md` — canonical operating contract and version.
- `references/input-contract.md` — accepted source structure and PDF parse-quality gates.
- `references/reader-contract.md` — reader navigation, bookmarks, viewport, and print contract.
- `references/clinical-constraints.md` — medical-text/calculator safety constraints.
- `scripts/build_guide.py` — builder.
- `scripts/check_guide.py` — generated-artifact checker.
- `scripts/run_regression.py` — 59-check functional regression suite.
- `scripts/verify_release.py` — release/version-drift verifier.
- `TEST_REPORT.md` — functional verification record.
- `RELEASE_AUDIT.md` — v1.2.1 governance release evidence.

## Manual use

When native skill activation is unavailable, follow `MANUAL_ACTIVATION.md`. Manual loading is not proof of native runtime activation.

## Install ZIP shape

The install ZIP must expose `SKILL.md` at the archive root. Do not wrap the package in an extra `offline-study-guide/` directory.

## Functional baseline retained from v1.2.0

The v1.2.0 capability baseline remains unchanged: 59/59 automated regression checks, including the guarded layout-aware PDF path. The Davidson 12-page integration case remains the real-source acceptance reference documented in `TEST_REPORT.md`.

## Known limitations

- Scanned PDFs still require OCR.
- Layout-aware textbook parsing activates only under a strong title/contents/body-heading corroboration gate.
- Complex figures or boxes can remain visual-only with source-page fallbacks rather than guessed semantic reconstruction.
- The static checker does not substitute for an actual mobile browser/HTTP viewport test.
