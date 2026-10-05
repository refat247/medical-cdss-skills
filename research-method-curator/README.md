# Research Method Curator

> **Distribution status notice — 2026-10-05:** this public v1.1.2 package is a **lagging distribution**, not the current writable canonical source. The canonical package is `refat247/Private_repo/skills/research-method-curator/` v1.2.0. Preserve this copy for public history/provenance until an explicit public-promotion decision; do not treat recency of the monorepo as authority.

**Version:** 1.1.2  
**Date:** 2026-09-23  
**Status:** Lagging public distribution; not the current writable canonical source.

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

Do not install this v1.1.2 public copy as the current source. Use the canonical `Private_repo` v1.2.0 package. Runtime installation is not proven until a fresh-session version and read-only smoke test succeeds.
