# Changelog

## 1.1.2 — 2026-09-23

### Added
- Preservation-safe `@humanizer` finishing-pass delegation for final human-facing research prose.
- Explicit protection for raw sources, quotations, exact-support excerpts, claim/source evidence fields, code/logs, metrics, qrels, chunk IDs, provenance identifiers, and exact clinical/legal wording.
- Mandatory post-Humanizer comparison against the verified pre-Humanizer draft to detect added/dropped claims or changed evidence/readiness meaning.
- Fallback rule when `@humanizer` is unavailable: local prose cleanup only, with no claim that the skill ran.

### State boundary
- Manual-upload candidate; fresh-session verification remains pending.

## 1.1.1 — 2026-09-04

### Added
- Complete human-facing package guide and layout inventory.
- Package maintenance, semantic-versioning, release, and read-only smoke-test protocol.
- Stable status, trigger examples, required-file inventory, and explicit default prompt in Work Mode metadata.

### Changed
- Normalized Work Mode display metadata, string quoting, and icon paths.
- Recorded v1.1.0 as the preserved functional baseline.

## 1.1.0 — 2026-09-01

- Added mandatory Timestamped Discovery Evidence Archive Protocol.
- Added source-card required fields.
- Added anti-failure rule for summary-only research updates.
- Added RAG/CDSS-specific separation of external discovery from local validation.
