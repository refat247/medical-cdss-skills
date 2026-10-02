# Changelog

## 1.0.0 — 2026-09-28

### Added
- Initial `humanizer-niqs-bridge` package.
- Upstream dependency fixed to `blader/humanizer` v3.1.0 for this release.
- NIQS Preservation Overlay v1.0.0.
- Explicit precedence rule: evidence/governance preservation overrides prose cleanup.
- Pattern 25 override for provenance, verification, reproducibility, and audit meaning.
- Pattern 26 override for standalone Notion pages that require local context.
- Mandatory semantic-drift check.
- Manual-fallback wording that does not falsely claim native Humanizer activation.
- Activation smoke test and package manifest.

### Packaging
- `SKILL.md` and `agents/openai.yaml` both declare package version 1.0.0.
- Upstream Humanizer remains an external dependency; this package does not fork or relabel it.
