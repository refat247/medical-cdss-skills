# Changelog

## 1.2.0 — 2026-09-25

### Added
- Shared **Notion Information Quality Standard (NIQS) v1.0** reference.
- Research ownership for source authority, claim/evidence verification, freshness/recheck triggers, evidence debt, contradiction handling, uncertainty budgets, and research-to-monitoring transitions.
- Explicit boundary that readable/synthesis-ready content is not automatically evidence-method complete.

### State boundary
- **Git/package source:** release authored 25 Sep 2026.
- **Notion mirror:** to be synchronized and re-fetched in the same release workflow.
- **Runtime installation/activation:** NOT VERIFIED by this source update; requires user-controlled install/update and fresh-session activation test.


All notable changes to Research Method Curator are documented here.

## 1.1.2 — 2026-09-23

### Added

- Preservation-safe `@humanizer` finishing-pass delegation for final human-facing research prose.
- Explicit protection for raw sources, quotations, exact-support excerpts, claim/source evidence fields, code/logs, metrics, qrels, chunk IDs, provenance identifiers, and exact clinical/legal wording.
- Mandatory post-Humanizer comparison against the verified pre-Humanizer draft to detect added/dropped claims or changed evidence/readiness meaning.
- Fallback rule when `@humanizer` is unavailable: local prose cleanup only, with no claim that the skill ran.

### State boundary

- **Runtime:** v1.1.2 fresh-session manual-install verification passed on 23 Sep 2026.
- **Git:** canonical v1.1.2 package synchronized on 23 Sep 2026 at commit `5cec4d6b8b16f47752b0ffa1e9efe10208e79065`.
- Historical v1.1.1 managed-package/Git verification remains provenance.

## 1.1.1 — 2026-09-04

### Added

- Complete human-facing package guide and layout inventory.
- Package maintenance, semantic-versioning, release, and read-only smoke-test protocol.
- Stable status, trigger examples, required-file inventory, and explicit default prompt in Work Mode metadata.

### Changed

- Normalized Work Mode display metadata, string quoting, and icon paths.
- Recorded v1.1.0 as the preserved functional baseline; this patch does not change its research workflow.

### Verified

- Confirmed package discovery, YAML parsing, version agreement, required-file coverage, default prompt routing, and Skill Creator validation.

### Known limitations

- The skill provides research-governance instructions; it does not independently supply source access, clinical approval, legal review, benchmark data, or Notion connectivity.

## 1.1.0 — 2026-09-01

- Added mandatory Timestamped Discovery Evidence Archive Protocol.
- Added source-card required fields.
- Added anti-failure rule for summary-only research updates.
- Added RAG/CDSS-specific separation of external discovery from local validation.
