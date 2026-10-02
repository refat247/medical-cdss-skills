# Research Method Curator

**Version:** 1.1.2  
**Date:** 2026-09-23  
**Status:** Manual-upload candidate.

Research Method Curator turns research drafts and evidence collections into decision-grade outputs with explicit provenance, claim verification, timestamped evidence archives, uncertainty, reproducibility, and readiness labels.

## Use it for

- source and claim audits;
- research-method design;
- provenance repair for multi-AI outputs;
- timestamped current-source research updates;
- Notion-ready research pages and source cards;
- model-selection evidence;
- medical, RAG, and CDSS research controls;
- benchmark reproducibility and leakage checks.

## Humanizer integration

For final human-facing research prose, apply `@humanizer` only after evidence verification and decision routing. Preserve all claims, numbers, dates, citations, evidence/readiness labels, uncertainty and clinical/legal meaning.

Exclude raw source text, quotations, exact-support excerpts, claim-ledger/source-card evidence fields, code/logs, metrics, qrels, chunk IDs and provenance identifiers.

Recheck the final prose against the pre-Humanizer draft for semantic drift.

## Package layout

- `SKILL.md`
- `README.md`
- `CHANGELOG.md`
- `references/timestamped-discovery-evidence-archive.md`
- `references/package-maintenance.md`
- `agents/openai.yaml`
- `assets/icon.svg`

## Important boundary

This ZIP is suitable for manual upload/update. Installation is not proven until a fresh-session version and read-only smoke test succeeds.
