# Notion Content Auditor

**Version:** 1.2.1  
**Date:** 2026-09-23  
**Status:** Manual-upload candidate built from the canonical Notion working patch.

## Why

A workspace can be organized yet contain incomplete, stale, contradictory, duplicated, unsupported or incorrectly canonical knowledge. Content Auditor audits knowledge quality; Workspace Curator audits structure/usability.

## Workflow

`FREEZE SCOPE → INVENTORY → HEALTH SCAN → SEMANTIC AUDIT → CANONICAL RECONCILIATION → SELECTIVE EVIDENCE REVALIDATION → SAFE REPAIR → RE-FETCH → VERIFY → CLOSE COVERAGE`

## Levels

- L1 Content Health
- L2 Semantic Integrity
- L3 Evidence Revalidation + Change-Impact Reconciliation

## Humanizer integration

For final owner-facing prose, use `@humanizer` as a finishing layer only after audit/repair. Preserve facts, numbers, dates, citations, evidence labels, uncertainty, legal/clinical meaning and technical literals.

Exclude raw evidence, quotations, code, logs, immutable source text, protected corpus material and exact claim-ledger fields.

After the pass, perform a semantic-drift check. Added, dropped, softened or strengthened claims are failures and must be repaired.

If the skill is unavailable, use a preservation-safe local prose cleanup and do not claim Humanizer ran.

## Package layout

10 required files:
- `SKILL.md`
- `README.md`
- `CHANGELOG.md`
- `references/content-audit-rubric.md`
- `references/evidence-revalidation.md`
- `references/coverage-and-closure.md`
- `references/safe-repair-protocol.md`
- `references/prompt-injection-defense.md`
- `agents/openai.yaml`
- `assets/icon.svg`

## Important boundary

This ZIP is suitable for manual upload/update. Installation is not proven until the skill is loaded in a fresh session and reports v1.2.1.
