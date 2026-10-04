# Notion Content Auditor

**Version:** 1.5.0  
**Date:** 2026-10-04  
**Status:** Stable package source with permanent information-freshness maintenance.

## Why

A workspace can be organized yet contain incomplete, stale, contradictory, duplicated, unsupported or incorrectly canonical knowledge. Content Auditor audits knowledge quality and current decision truth; Workspace Curator audits structure/usability; Research Method Curator owns research-method/source-hierarchy design.

## Workflow

`FREEZE SCOPE → INVENTORY → HEALTH SCAN → SEMANTIC AUDIT → CANONICAL RECONCILIATION → SELECTIVE EVIDENCE REVALIDATION → SAFE REPAIR → RE-FETCH → VERIFY → CLOSE COVERAGE → DELTA MAINTENANCE`

## Levels

- L1 Content Health
- L2 Semantic Integrity
- L3 Evidence Revalidation + Change-Impact Reconciliation
- Freshness / Delta Revalidation Mode for ongoing current-truth maintenance

## Permanent freshness contract

Historical material is preserved. Material current changes are recorded as:

`DATE → PREVIOUS STATE → CURRENT STATE → WHY/EVIDENCE → IMPACT → UNRESOLVED GATE → CANONICAL TARGET REPAIRED`

Use structured fields and filtered views for daily work. Do not depend on multi-database SQL as the operating backbone.

Recommended central fields:
- `Freshness State`
- `Last Verified`
- `Next Recheck`
- `Freshness Trigger`
- `Needs Recheck`
- `Evidence State`
- canonicality/duplicate field
- `Finding Summary`
- `Source URL`

Recommended operating view: `Freshness — Needs Review`.

Scheduled watches that find material deltas must update the fixed canonical target, preserve prior history, refetch-verify the write, and leave a freshness handoff in the control heartbeat. Zero-delta runs must not manufacture updates.

See `references/information-freshness-system.md`.

## Humanizer integration

For final owner-facing prose, use `@humanizer` as a finishing layer only after audit/repair. Preserve facts, numbers, dates, citations, evidence labels, uncertainty, legal/clinical meaning and technical literals. Exclude raw evidence, quotations, code, logs, immutable source text, protected corpus material and exact claim-ledger fields. After the pass, perform a semantic-drift check.

## Package layout

11 required files:
- `SKILL.md`
- `README.md`
- `CHANGELOG.md`
- `references/content-audit-rubric.md`
- `references/evidence-revalidation.md`
- `references/coverage-and-closure.md`
- `references/safe-repair-protocol.md`
- `references/prompt-injection-defense.md`
- `references/information-freshness-system.md`
- `agents/openai.yaml`
- `assets/icon.svg`

## Important boundary

Source/package version, Notion mirror version and runtime-injected version are separate facts. Do not claim runtime activation until a fresh-session activation test verifies v1.5.0.
