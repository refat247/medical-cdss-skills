# 08 · medical-rag-orchestrator (v1.4.0) — Independent Audit

**Tier:** Critical path (build orchestration) · **Code:** 500 LOC · **Tests:** 11 pass / 0 fail `[M]`

| Goal fit | Safety | Tests | Docs accuracy | Portability | **Overall** |
|:-:|:-:|:-:|:-:|:-:|:-:|
| A | A- | B | B | C+ | **B+** |

## What it does well
- **Trust-first.** It does not infer "ready" from files; it calls the pipeline's own `build_chapter_trust_record` and treats `CORPUS_OUTPUT_PROTECTED.json` as a mutation-safety marker only, not evidence of trust `[C]`.
- **Fails safe:** if the classifier cannot be loaded it reports `RAG TRUST UNKNOWN`, never READY `[C]`. It removes the pipeline folder from `sys.path` after import to avoid shadowing `scripts` `[C]`.
- Ignores side copies (backup/audit/bundle) when choosing the live output; picks the canonical `rag_pipeline_output`.
- Env-overridable roots (`CDSS_SKILLS_ROOT`, `CDSS_DOWNLOADS_DIR`).

## Findings
| ID | Sev | Ev | Finding | Fix |
|---|---|---|---|---|
| R1 | High | C | Imports a **private** function `pipeline.stages.trust_ledger.build_chapter_trust_record`. An upstream refactor breaks it (safely, as UNKNOWN, but it blocks all runs). | Publish a stable `pipeline.public_api.classify_chapter()` and import only that. |
| R2 | High | C | `verify-versions` is a separate subcommand; `auto` does not run it, and there are **no declared sibling-version constraints**. | Run a compatibility check first in `auto`; read `requires:` from each SKILL.md (see 19). |
| R3 | Medium | C | Stages are chained by `subprocess.run` and judged by **exit code only**; no structured result/manifest per stage. | Have each stage emit a JSON result (status, outputs, hash) the orchestrator records. |
| R4 | Medium | C | Hard-coded Windows examples and some defaults in docstring/CLI help (7 code lines, 23 doc lines). | Placeholders; env-based. |
| R5 | Low | C | `_is_side_copy` excludes any sub-path containing `backup`, `audit` or `bundle`, so a legitimately named folder with those words would be skipped. | Match whole path segments. |
| R6 | Low | I | No end-to-end test (only unit tests of helpers and status logic). | Add the e2e fixture proposed in the master report (F7). |

## Verdict
Well-built and honest about uncertainty. Its main exposure is coupling to a private pipeline API and lack of any version contract.

**Top 3 actions:** (1) public trust API, (2) version check in `auto`, (3) per-stage JSON results.
