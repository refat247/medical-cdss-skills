# Clinical PPTX Builder

Reusable Codex skill for creating, editing, merging, and auditing clinical or academic PowerPoint decks. It is designed for CME, teaching, grand rounds, journal clubs, and evidence-based medical communication—not marketing presentations.

## Current release

- Version: **0.2.1**
- Status: **PROVISIONAL / operational**
- Reliability baseline commit: `68fe558`
- Canonical instructions: [`SKILL.md`](SKILL.md)

The skill is provisional because automated checks improve reliability but cannot certify clinical correctness, regulatory status, local labeling, or final appearance in every PowerPoint renderer.

## What it provides

- Geometry-first slide construction and repair.
- Source-traceable content through `deck.spec.yaml`.
- Explicit evidence classes: `VERIFIED`, `OBSERVED`, `INFERRED`, and `UNKNOWN`.
- Structural preflight for geometry, readability, contrast, fonts, density, and package integrity.
- Clinical surface lint for unsafe or overclaiming language.
- Render-and-inspect guidance with a clear renderer/font limitation.
- User-stated typography thresholds and requested coverage items as explicit QA gates.
- Reproducible regression fixtures for known failures.
- Safe deck combining by extracting content into a specification and rebuilding.

## Use

1. Read `SKILL.md` and the relevant reference file.
2. Create or update a source-of-truth `deck.spec.yaml`.
3. Build or patch the deck with the installed presentation runtime.
4. Run structural preflight and clinical lint.
5. Render every slide and inspect the contact sheet plus risk slides.
6. Reconcile the request coverage ledger.
7. Repair, rerun all gates, and persist the final artifact with a clear status.

Typical commands from this directory:

```bash
python3 scripts/pptx_preflight.py path/to/deck.pptx
python3 scripts/clinical_lint.py path/to/deck.pptx
python3 scripts/run_regression.py
```

The regression suite should report `Regression suite passed`. Expected failures in intentionally defective fixtures are part of the test contract.

## Package layout

| Path | Purpose |
|---|---|
| `SKILL.md` | Executable Codex instructions |
| `deck.spec.yaml` | Example source-of-truth slide specification |
| `scripts/` | Reusable preflight, lint, fixture, and regression helpers |
| `references/` | QA, merge, schema, and regression guidance |
| `tests/fixtures/` | Good and defective decks used for regression |
| `agents/openai.yaml` | Invocation metadata |
| `assets/icon.svg` | Package identification icon |
| `CHANGELOG.md` | Human-readable release history |
| `VERSION` | Current semantic version |
| `VERSION_LOG.md` | Release and verification record |

## Maintenance rules

- Keep `SKILL.md` concise and route detailed procedures to `references/`.
- Change the version and changelog for behavior or package changes.
- Run `quick_validate.py`, `python3 scripts/run_regression.py`, and a clean Git status check before release.
- Treat `ERROR` findings and unrun required gates as delivery blockers.
- Preserve uncertainty; an unresolved local label or renderer limitation must remain `UNKNOWN` or `UNCERTIFIED`.
- `MANIFEST.sha256` is generated at packaging time and excludes itself.

## Safety boundary

This package supports presentation production and quality assurance. It is not a clinical decision tool, regulatory database, or substitute for clinician review and current jurisdiction-specific labeling.
