---
name: research-method-curator
description: Create, audit, repair, and structure high-integrity research outputs for Notion and project decision-making. Use for deep research prompts, source-provenance repair, claim verification, research methodology design, Notion-ready research pages, model-selection evidence, CDSS/RAG research, timestamped discovery archives, and anti-hallucination research workflows.
metadata:
  version: "1.1.2"
  status: "stable"
---

# Research Method Curator

Use this skill to turn research into decision-grade knowledge without hiding uncertainty. Preserve raw source material, separate evidence from interpretation, and make the output usable in Notion.

## Core Rule

Do not treat a written answer, AI output, citation list, vendor claim, benchmark score, or social report as verified evidence until the exact claim has been checked against an appropriate source.

Every important claim must answer:

- What is the claim?
- What source supports it?
- How strong is that source?
- How fresh is it?
- Does it apply to the user's real context?
- What remains unverified?
- Is this ready for action, or only research?

## Source Hierarchy

Use the strongest available source first.

| Level | Source Type | Use |
|---|---|---|
| A | Official documentation, law, regulator, primary product page, original paper, source repository | Default authority for factual, legal, pricing, eligibility, and technical claims |
| B | Peer-reviewed academic or accepted preprint with methods | Medical, scientific, benchmark, validation, and safety claims |
| C | Independent benchmark or reproducible evaluation | Model and system comparison, with limitations stated |
| D | GitHub issues, code, commits, reproducible logs, public datasets | Implementation reality, bugs, failure modes, reproducibility |
| E | Community consensus from Reddit, HN, forums, YouTube comments, X | Discovery and user-experience evidence only; never final authority alone |
| F | Single anecdote, vendor marketing, AI-generated summary, unsupported claim | Lead only; mark unverified |

Resolve conflicts by source level, recency, reproducibility, jurisdiction, and directness. Preserve meaningful contradictions instead of forcing a false conclusion.

## Evidence Labels

| Label | Meaning |
|---|---|
| `VERIFIED FACT` | Exact claim is supported by retrieved source text |
| `OFFICIAL CLAIM` | Vendor/organization says it, but independent confirmation may be absent |
| `RESEARCH FINDING` | Supported by study/benchmark with methods and limitations |
| `COMMUNITY REPORT` | Reported by users; useful for leads/failure modes |
| `OBSERVED` | Directly observed in a fetched page, tool output, UI screenshot, log, or user-supplied artifact |
| `INFERENCE` | Reasoned conclusion from evidence; not directly stated by a source |
| `HYPOTHESIS` | Plausible but not verified |
| `UNVERIFIED` | Source not checked or does not directly support the claim |
| `CONFLICTING EVIDENCE` | Sources disagree; do not simplify prematurely |
| `INSUFFICIENT PUBLIC EVIDENCE` | Not enough reliable public evidence to decide |

## Claim Ledger

For deep research, high-risk topics, volatile current-state checks, or decision-support pages, create or update a claim ledger.

Required fields: Claim ID, Claim, Source URL/file, Source title, Publisher/authority, Publication date, Access/review date, Source type, Evidence tier, Exact support, Corroboration, Jurisdiction, Freshness risk, Confidence, Notes.

## Timestamped Discovery Evidence Archive Protocol

Use this protocol for any research update involving new external discoveries, model changes, tool changes, clinical evidence, pricing, provider behavior, benchmark results, source-dependent claims, or other volatile decision inputs.

For the standalone reusable protocol, read [references/timestamped-discovery-evidence-archive.md](references/timestamped-discovery-evidence-archive.md).

### Trigger
Apply this protocol when any of the following is true:

- The user asks for a current update, latest discovery, status check, benchmark update, tool/model/provider update, or external evidence check.
- The answer uses official documentation, papers, GitHub, forums, social reports, benchmark websites, support threads, or other source-dependent evidence.
- The update may change a Notion decision, routing policy, model shortlist, benchmark design, clinical/RAG/CDSS gate, risk label, or next action.

### Mandatory output structure
Do not record only a narrative summary. Preserve the evidence trail.

1. Update or create the canonical synthesis/status page.
2. Create or update a timestamped evidence archive under the canonical parent or the most appropriate research hub.
3. Create one child source card per material source or discovery cluster.
4. Link the evidence archive from the canonical synthesis/status page.
5. Link each child source card back to the synthesis/status page when the tool surface allows it.
6. Re-fetch or otherwise verify the canonical page after writes.
7. Report the exact state as: DISCOVERED → ANALYZED → WRITTEN → EXECUTED → RE-FETCHED/VERIFIED, with any failed stage named.

### Required fields for each source card
Each child evidence card must include:

| Field | Requirement |
|---|---|
| Discovery ID | Stable ID, e.g. `SRC-YYYY-MM-DD-01` |
| Checked timestamp | Local timestamp with timezone, e.g. `2026-09-01T23:27+06:00` |
| Source URL / DOI / repo / file | Exact source pointer |
| Source title | Human-readable title |
| Source channel | Official / developer docs / academic paper / benchmark / GitHub / support / social / vendor / AI output / uploaded file |
| Source date or version | Published, updated, release, commit, model, or `unknown` |
| Claim supported | One or more atomic claims actually supported by the source |
| Evidence strength | VERIFIED / OFFICIAL CLAIM / OBSERVED / RESEARCH FINDING / COMMUNITY REPORT / INFERENCE / UNKNOWN |
| Decision impact | What this changes, strengthens, weakens, or does not change |
| Canonical status | RECORDED / PROVISIONAL / SUPERSEDES / REJECTED / NEEDS RECHECK / BLOCKED |
| Limits | What the source does not prove |
| Next trigger | When to recheck or escalate |

### Evidence archive parent page standard
The parent evidence archive must include:

- Scope and date range checked.
- Search/browse method summary.
- List of child source cards.
- Summary of which discoveries are new, strengthened, unchanged, contradicted, or blocked.
- Canonical decision impact.
- Remaining unknowns.
- Explicit statement that external source evidence can shortlist or update policy, but cannot replace local benchmarks, clinical review, or artifact-level verification when those gates are required.

### Anti-failure rule
If a research update contains only a synthesis paragraph and no source ledger or child evidence cards, mark it incomplete as `EVIDENCE ARCHIVE MISSING` unless the user explicitly requested a lightweight answer with no Notion persistence.

### RAG/CDSS-specific application
For RAG, retrieval, model-selection, or medical CDSS updates, external discoveries must remain separate from local validation.

Do not treat official model docs, community reports, GitHub examples, or public benchmarks as proof that the user's local corpus retrieval works. A local PASS still requires the relevant corpus manifest, chunk IDs, source spans, qrels or equivalent evaluation set, retrieval traces, metrics, failure cases, and human clinical review when clinical decisions are affected.

## Research Workflow

1. **Source lock** — identify the source set before synthesis; preserve raw AI outputs, uploaded files, screenshots, transcripts, and source pages.
2. **Source register** — list all sources used with URL/file name, date checked, authority, source type, and role.
3. **Claim extraction** — break important claims into atomic statements.
4. **Verification** — check exact support; mark unsupported, partial, stale, or conflicting claims.
5. **Minimal repair** — repair only what is wrong; preserve uncertainty and contradictions.
6. **Decision routing** — classify ready, blocked, needs live recheck, needs benchmark, needs legal review, or needs human clinical review.
7. **Evidence archive** — for current-source discovery updates, create timestamped child source cards and link them from the synthesis page.
8. **Re-audit** — after repair, recheck affected claims and record audit date, reviewer, scope, and limits.

## Output Readiness Labels

READY / NEEDS REPAIR / RESEARCH ONLY / DO NOT USE FOR DECISION / BLOCKED.

## Notion Research Page Standard

Durable research pages must include title, status, audit status, audit date, writer, reviewer, source register, criteria, methodology, limitations, update frequency, last checked, Bangladesh/medical/RAG/cost relevance as applicable, decision readiness, and next action.

Use a short summary at top, then evidence, then decision/action sections. Keep raw archive separate from synthesis and decision layers.

## AI Model Research Rules

Never recommend a universal best model from leaderboards alone. Separate benchmark score, methodology, update frequency, provider availability, cost, latency, context length, tools, RAG performance, medical safety relevance, Bangladesh availability/payment risk, workflow fit, local benchmark result, and human review status.

Leaderboards and public benchmarks can shortlist models. They cannot validate clinical performance or replace local task testing.

## Medical, RAG, and CDSS Rules

Do not invent qrels, answer keys, chapter mappings, guideline cutoffs, licensing terms, legal obligations, or clinical recommendations. Do not substitute generic medical benchmarks for local CDSS validation.

For Davidson CDSS or textbook-grounded RAG:

- Use only confirmed source chapters and inspected `L2-*` chunks.
- Preserve chunk IDs and source provenance.
- Mark draft qrels as `NOT_FROZEN` until review is complete.
- Report status separately: Designed, Code written, Executed, Tests passed, Benchmark passed, Human clinical review completed.
- External discoveries must be archived as source cards and may only change the candidate list or test plan until local benchmark evidence exists.

## Humanizer finishing pass

Apply `@humanizer` only to the **final human-facing narrative layer**, after source locking, claim verification, evidence labeling, decision routing, and any required evidence archive are complete.

- Preserve every supported claim, number, date, citation, URL/DOI/repository pointer, evidence label, readiness label, limitation, jurisdiction, uncertainty statement, and decision implication.
- Do **not** humanize raw source material, direct quotations, exact-support excerpts, claim-ledger/source-card fields whose wording is evidentiary, code, logs, benchmark metrics, qrels, chunk IDs, provenance identifiers, legal/clinical source wording, or protected corpus text.
- Humanizer may remove AI-writing tells such as staged openers, repetitive closers, forced triads/symmetry, inflated wording, canned transitions, excessive formatting, and robotic rhythm. It may reorganize prose only when no evidence relationship is lost.
- When `@humanizer` is unavailable, apply only a preservation-safe local prose cleanup and do not claim the Humanizer skill ran.
- After the pass, compare the result against the pre-Humanizer draft. Added or dropped facts, changed evidence strength, altered uncertainty, or changed readiness/decision meaning are failures and must be repaired.

## Final Response Pattern

For audits or research updates, lead with findings, then show what was checked, source register, criteria, evidence table, claim ledger or high-risk claims, limitations, relevance, unsupported claims, needed rechecks, readiness label, and next actions.

## Version Note

v1.1.2 adds a preservation-safe Humanizer finishing layer without changing the evidence, verification, archive, benchmark, or decision-readiness workflow. It is a manual-upload candidate until installed and smoke-tested.
