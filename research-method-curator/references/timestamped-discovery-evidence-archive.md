# Timestamped Discovery Evidence Archive Protocol

Use this protocol for any research update involving new external discoveries, model changes, tool changes, clinical evidence, pricing, provider behavior, benchmark results, source-dependent claims, or other volatile decision inputs.

## Trigger

Apply this protocol when any of the following is true:
- The user asks for a current update, latest discovery, status check, benchmark update, tool/model/provider update, or external evidence check.
- The answer uses official documentation, papers, GitHub, forums, social reports, benchmark websites, support threads, or other source-dependent evidence.
- The update may change a Notion decision, routing policy, model shortlist, benchmark design, clinical/RAG/CDSS gate, risk label, or next action.

## Mandatory output structure

1. Update or create the canonical synthesis/status page.
2. Create or update a timestamped evidence archive under the canonical parent or most appropriate research hub.
3. Create one child source card per material source or discovery cluster.
4. Link the evidence archive from the canonical synthesis/status page.
5. Link each child source card back to the synthesis/status page when the tool surface allows it.
6. Re-fetch or otherwise verify the canonical page after writes.
7. Report the exact state as: DISCOVERED → ANALYZED → WRITTEN → EXECUTED → RE-FETCHED/VERIFIED.

## Required fields for each source card

| Field | Requirement |
|---|---|
| Discovery ID | Stable ID, e.g. `SRC-YYYY-MM-DD-01` |
| Checked timestamp | Local timestamp with timezone |
| Source URL / DOI / repo / file | Exact source pointer |
| Source title | Human-readable title |
| Source channel | Official / developer docs / academic paper / benchmark / GitHub / support / social / vendor / AI output / uploaded file |
| Source date or version | Published, updated, release, commit, model, or `unknown` |
| Claim supported | One or more atomic claims actually supported |
| Evidence strength | VERIFIED / OFFICIAL CLAIM / OBSERVED / RESEARCH FINDING / COMMUNITY REPORT / INFERENCE / UNKNOWN |
| Decision impact | What this changes, strengthens, weakens, or does not change |
| Canonical status | RECORDED / PROVISIONAL / SUPERSEDES / REJECTED / NEEDS RECHECK / BLOCKED |
| Limits | What the source does not prove |
| Next trigger | When to recheck or escalate |

## Evidence archive parent page standard

Include:
- scope and date range checked;
- search/browse method summary;
- child source cards;
- summary of new/strengthened/unchanged/contradicted/blocked discoveries;
- canonical decision impact;
- remaining unknowns;
- explicit statement that external evidence cannot replace local benchmarks, clinical review, or artifact-level verification when those gates are required.

## Anti-failure rule

If a research update contains only a synthesis paragraph and no source ledger or child evidence cards, mark it incomplete as `EVIDENCE ARCHIVE MISSING` unless the user explicitly requested a lightweight answer with no Notion persistence.

## RAG/CDSS-specific application

Do not treat official model docs, community reports, GitHub examples, or public benchmarks as proof that the user's local corpus retrieval works. A local PASS still requires the relevant corpus manifest, chunk IDs, source spans, qrels or equivalent evaluation set, retrieval traces, metrics, failure cases, and human clinical review when clinical decisions are affected.
