# Changelog

## [0.5.0] — 2026-09-25

### Added
- Shared **Notion Information Quality Standard (NIQS) v1.0** in `references/notion-information-quality-standard.md`.
- Formal Page Role, Audience/Language Mode, Fast/Working/Evidence reading depths, evidence/claim state, freshness, verification metadata, decision readiness, confidence×consequence, source-authority, update-impact, supersession, current-vs-historical truth, information-density, staleness, evidence-debt, maintenance-cost, decision-value, change-delta, monitoring, AI-handoff, contradiction and uncertainty rules.
- Explicit anti-mass-rewrite rollout rule: upgrade active governed/control/decision surfaces first; dormant archives only when reactivated.
- Cross-skill boundary: structural, semantic and research-method PASS states remain independent.

### State boundary
- **Git/package source:** release authored 25 Sep 2026.
- **Notion mirror:** to be synchronized and re-fetched in the same release workflow.
- **Runtime installation/activation:** NOT VERIFIED by this source update; requires user-controlled install/update and fresh-session activation test.


## [0.4.4] — 2026-09-23

### Added
- Preservation-safe `@humanizer` finishing-pass delegation for newly written or materially rewritten human-facing prose.
- Explicit exclusions for raw/source evidence, quotations, code, logs, exact configuration, immutable source text, archived originals, evidence-bearing database values and protected corpus material.
- Mandatory post-Humanizer semantic-drift check for status, decisions, warnings, facts, routes and constraints.
- Fallback rule when `@humanizer` is unavailable: local prose cleanup only, with no claim that the skill ran.

### State boundary
- **Runtime:** v0.4.4 fresh-session manual-install verification passed on 23 Sep 2026.
- **Git:** canonical v0.4.4 package synchronized on 23 Sep 2026 at commit `42139ed980ff5c19c4a07624a09731a70176e914`.
- Historical v0.4.3 Git/device records remain provenance and do not override the current release.

## [0.4.3] — 2026-09-04

### Finalized
- Promoted `0.4.3-rc.2` to final `0.4.3` after the user confirmed that the required real-phone Mobile Access Layer checks passed.
- Preserved the reconciled reciprocal technical-glossary linking, evidence-archive routing, Mobile Access Layer, audit-ledger, native-formatting, safe-editing and prompt-injection-defense rules unchanged.
- Aligned the final release identity across `SKILL.md`, `README.md`, `CHANGELOG.md` and `agents/openai.yaml`.

### Validation boundary
- User-confirmed coverage: direct/widget opening; Capture to Universal Inbox; Today / Needs Action; Active Projects; Review; Search / Reference; tap/scroll usability; loading; Share Sheet/attachments; offline/degraded behavior.
- Exact quantitative timings and tap counts were not supplied and are not claimed.

## [0.4.3-rc.2] — 2026-09-04

### Reconciled
- Consolidated two divergent packages that were both labelled `0.4.3-rc.1`.
- Preserved the full reciprocal technical-glossary linking protocol and the evidence-archive placement/linking responsibility in one package.
- Restored the complete Mobile Access Layer, audit-ledger, native-formatting, safe-editing and prompt-injection defenses from the fuller package.

### Fixed
- Replaced the validator-invalid top-level `version` key with `metadata.version` in `SKILL.md`.
- Aligned the release identity across `SKILL.md`, `README.md`, `CHANGELOG.md` and `agents/openai.yaml`.
- Added `references/evidence-archive-routing.md` alongside `references/notion-ux-patterns.md`.

### Status
- **Installable release candidate.** Runtime/package identity can be smoke-tested after repository synchronization.
- **Pending:** real-device mobile validation; this release does not promote the Mobile Access Layer to final verified status.

## [0.4.3-rc.1] — 2026-09-01

### Added
- New-page reciprocal-link protocol for technical jargon navigation.
- Independent classification and linking requirement for relevant child pages and descendants.
- Bidirectional source-page ↔ glossary-category verification after every write.
- Ledger reconciliation requirement using `EXPECTED = VERIFIED BIDIRECTIONALLY LINKED + UNRESOLVED`.
- Canonical-index update rule when a new page changes a project, decision, architecture, evidence state or control surface.

### Preserved
- Raw, archive-only, log, duplicate-wrapper and non-substantive page exclusions unless a page becomes canonical navigation/control material.

## [0.4.2-rc.1] — 2026-08-30

### Added
- Evidence-backed **Mobile Access Layer** rule.
- Intent-first Mobile Home pattern: Capture, Today / Needs Action, Active Projects, Review, Search / Reference.
- Universal Inbox/staging guidance with **capture now, classify later** semantics.
- One-canonical-source/multiple-access rule for mobile: linked views/direct links instead of duplicate mobile databases.
- Mobile database-view guidance: compact lists/tables, roughly 3–5 decision-relevant properties, hide heavy relations/rollups/formulas/audit metadata from first view.
- Device-entry hierarchy: native Notion widgets/shortcuts/Share Sheet first; API/Telegram/external frontends only when justified.
- Explicit desktop-first boundary for schema, relations, formulas, mass triage and structural curation.
- Real-device validation gate separating Notion-side smoke-test success from actual mobile usability.

### Preserved
- v0.4.1 two-callout mobile first-screen rule for applicable parent/hub/control/navigation pages.
- Coverage equation and bounded-audit closure rules.
- Source-truth, provenance, duplicate-control, full research-output child-page, native formatting and safe-editing rules.

### Status
- **Installable release candidate.** Notion-side Mobile Access Layer Phase 1 has been implemented and smoke-tested.
- **Pending:** real-device load/tap/scroll/widget/shortcut/Share Sheet/attachment/offline validation.

## [0.4.1] — 2026-08-30

- Added mobile-first first-screen compression for parent/hub/control surfaces.
- Standardized one concise CURRENT STATE callout plus one START HERE/navigation callout before deeper history/governance detail.
- Defined inapplicable surfaces so leaf reports, task instruments, standalone evidence pages and database-only surfaces are not mechanically rewritten.
- Retained persistent audit checkpoints, deterministic cursor/state transitions and delta-audit/token-economy rules.

## [0.4.0] — 2026-08-29

- Strengthened workspace-wide audit coverage and canonical-state discipline.
- Added persistent audit ledger/checkpoint expectations and delta/re-audit closure behavior.

## [0.3.7] — 2026-08-28

- Earlier Git-synced baseline prior to Notion working-rule upgrades.