# Changelog

## 1.5.0 — 2026-10-04

### Added
- Permanent **Freshness / Delta Revalidation Mode** for ongoing Notion current-truth maintenance.
- Explicit current-vs-historical preservation contract: never silently rewrite dated historical truth when current evidence changes.
- Standard material-delta record: `DATE → PREVIOUS STATE → CURRENT STATE → WHY/EVIDENCE → IMPACT → UNRESOLVED GATE → CANONICAL TARGET REPAIRED`.
- Structured freshness-field contract: Freshness State, Last Verified, Next Recheck, Freshness Trigger, Needs Recheck, Evidence State, canonicality, finding summary and source route.
- Scheduled-watch freshness handoff and propagation contract.
- Operating-view rule: maintain a compact `Freshness — Needs Review` queue rather than using multi-database SQL as the daily backbone.
- Freshness closure criteria and no-false-completeness boundary.
- `references/information-freshness-system.md`.

### Reconciled
- Promotes the NIQS-aware v1.4.0 semantics previously mirrored in KOS into the canonical Git package source.
- Resolves the prior source split where GitHub main exposed v1.2.1 while KOS metadata/mirrors referred to v1.4.0.
- Clarifies specialist ownership: Content Auditor = semantic freshness; Workspace Curator = routing/views; Research Method Curator = research method/source hierarchy.

## 1.4.0 — 2026-09-25

### Added
- Shared Notion Information Quality Standard (NIQS) v1.0 semantic enforcement.
- Evidence-state, claim-type, contradiction, current-vs-historical truth, freshness, canonicality and evidence-debt governance.

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
