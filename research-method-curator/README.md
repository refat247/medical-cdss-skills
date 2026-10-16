# Research Method Curator

Version: **1.2.0**

Status: **Stable package source release; runtime v1.2.0 activation pending fresh-session verification**

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

The skill does not treat AI output, a citation list, a vendor claim, a social report, or a benchmark score as verified evidence by itself. Medical or clinical decision support remains subject to source-bound evidence, task-specific evaluation, physician review, and any applicable legal or privacy review.

## Invocation

Invoke `$research-method-curator` explicitly, or describe a research audit, provenance repair, evidence-verification, current-source update, or research-method task. Implicit invocation is enabled.

## Humanizer integration

For final human-facing research prose, apply `@humanizer` only after evidence verification and decision routing. Preserve all claims, numbers, dates, citations, evidence/readiness labels, uncertainty and clinical/legal meaning. Exclude raw source text, quotations, exact-support excerpts, claim-ledger/source-card evidence fields, code/logs, metrics, qrels, chunk IDs and provenance identifiers. Recheck the final prose against the pre-Humanizer draft for semantic drift.

## Package layout

| Path | Purpose |
|---|---|
| `SKILL.md` | Canonical executable instructions and version |
| `README.md` | Human-facing package guide |
| `CHANGELOG.md` | Release history and known limitations |
| `references/timestamped-discovery-evidence-archive.md` | Detailed current-source evidence archive protocol |
| `references/package-maintenance.md` | Versioning, release, and smoke-test protocol |
| `agents/openai.yaml` | Work Mode interface, invocation, and package metadata |
| `assets/icon.svg` | Package icon |

## Maintenance

The canonical version is declared in both `SKILL.md` and `agents/openai.yaml`; the two values must match. Every release must update `CHANGELOG.md`, pass the Skill Creator validator, complete the smoke test in `references/package-maintenance.md`, and be committed without including unrelated working-tree changes.

Version 1.1.0 introduced the Timestamped Discovery Evidence Archive Protocol. Version 1.1.1 is a packaging repair that makes that existing release verifiable and maintainable.


## NIQS v1.0

This release adopts the shared `references/notion-information-quality-standard.md` contract. Research Method Curator owns source authority, claim-to-source support, research freshness, evidence archives/source cards, research readiness, uncertainty and research-to-monitoring transitions. Structural and semantic PASS states remain separate.
