# Changelog

## 1.2.1 — 2026-09-23

### Added
- Humanizer finishing-pass delegation for newly written or materially rewritten human-facing prose.
- Preservation boundary: no Humanizer rewrite of raw evidence, quotations, code, logs, immutable/canonical source text, protected corpus material, or exact claim-ledger fields.
- Post-Humanizer semantic drift check for added, dropped, softened or strengthened claims.
- Fallback rule: when `@humanizer` is unavailable, apply only a preservation-safe local prose cleanup and never claim the skill ran.

### Reconciled
- `agents/openai.yaml` version metadata is aligned with the canonical skill version.

## 1.2.0 — 2026-08-31

### Added
- Mandatory technical-language accessibility gate for owner-facing and operational technical pages.
- Dynamic jargon detection for current and future terminology.
- Preserve-first companion-explanation model.
- Bidirectional glossary navigation where useful.
- Raw research, code, logs, quoted evidence and immutable/canonical source material remain protected from accessibility rewrites.

## 1.1.0 — 2026-08-30

### Added
- Temporal T0 → T1 change-impact reconciliation.
- Current operational content must be substantively corrected when feasible rather than merely tagged `Needs Revalidation`.
- Historical-provenance preservation.

## 1.0.0 — 2026-08-30

Initial canonical package.
