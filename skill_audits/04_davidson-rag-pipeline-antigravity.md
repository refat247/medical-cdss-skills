# 04 · davidson-rag-pipeline-antigravity (v2.25.1) — Independent Audit

**Tier:** Critical path (core) · **Code:** 11,863 LOC pipeline · **Tests:** 463 pass / **3 fail** / 30 skipped `[M]` (8,162 test LOC; 48 test files)

| Goal fit | Safety | Tests | Docs accuracy | Portability | **Overall** |
|:-:|:-:|:-:|:-:|:-:|:-:|
| A | A- | A- | B | D | **B+** (strongest skill) |

## What it does well
- Real trust machinery: trust ledger, mutation guard, fail-closed finalization, atomicity tests (v2.6.9/2.6.10), adjudication manifests, Stage 4.5c source-span coverage gate, Stage 4.5d clinical-fidelity gate, Stage 6 hard-fail validation.
- Regression fixtures for two real chapters (ch02, ch05) and CLI guardrail tests.
- The orchestrator and compiler use its trust classifier as the single source of truth.

## Findings
| ID | Sev | Ev | Finding | Fix |
|---|---|---|---|---|
| D1 | High | M | **Two regression tests fail on any LF checkout.** `fixture_manifest.json` hashes were recorded with CRLF line endings: re-hashing the fixtures with `\n→\r\n` reproduces the recorded SHA-256 exactly `[M]`. The repo has no `.gitattributes`. CI on Linux/macOS or a different git autocrlf setting breaks the drift guard. | Add `.gitattributes` (`tests/fixtures/** -text` or `eol=crlf`) and re-record hashes on binary-safe bytes; or hash after newline normalisation. |
| D2 | Medium | M | `test_derive_chapter_info_guideline_archetype` fails off Windows: a `D:\…` path yields prefix `D_guidelines_DM_ADA_2026_DM_guideline` instead of `ADA_2026_DM_guideline`. Real code path, not just a test issue. | Parse with `PureWindowsPath` when the string looks like a drive path. |
| D3 | High | C | **Stage 4.6 uses an external LLM as a verifier**, via two vendor-specific modules (`stage_4_6_gemini_verification.py` with `GEMINI_MODEL`/default alias, and `stage_4_6_sonnet_verification.py` using `anthropic`), plus a manual path. A non-deterministic, vendor-dependent step sits inside a "trusted" chain. | Record model id, version, prompt hash and raw response in the ledger for every 4.6 decision; pin the model; make 4.6 advisory unless a human adjudicates (the 4.5d adjudication manifest pattern). |
| D4 | Medium | C | One-off chapter repair and release scripts (`chapter_repairs/*ch05*`, `*ch11_ch15*`, `releases/v2_6_8`) ship inside the skill with hard-coded `D:\davidson_25_full_pipeline\NN` paths (17 hard-coded path lines in pipeline/scripts). | Move to an `archive/` outside the skill, or take paths from args. |
| D5 | Medium | C | **Stale provenance names:** Stage 4.7 and `run_source_lines_precision.py` write `skill_name: "davidson-rag-pipeline-hyperagent"`; docstrings say `davidson-rag-pipeline-cc`. | Use `checkpoint_utils.SKILL_NAME` everywhere. |
| D6 | Low | C | Description is tied to "Google Gemini 3.7 Flash High" and "local Windows sessions". | Describe capabilities, not the host model. |
| D7 | Low | I | 30 tests are skipped; I did not review why. | List skip reasons in CI output; fail if skips exceed a budget. |
| D8 | **High** | M | **Five scripts crash on start with `NameError: name 'os' is not defined`** (found with pyflakes, reproduced by running one): `scripts/maintenance/checkpoint_migrate_v2_6_0.py`, `checkpoint_migrate_v2_6_4.py`, `scripts/chapter_repairs/apply_ch05_adjudication.py`, `regenerate_rag_optimised_ch05.py`, `migrate_ch05_schema_v2.py`. They call `os.path…` in `sys.path.insert` but never `import os`. The first two are the checkpoint-migration CLIs that `checkpoint_utils.py` tells users to run ("`checkpoint_migrate_v2_6_0.py --apply`"), so a checkpoint upgrade path is broken as shipped. No test imports them. | Add `import os`; add a smoke test that runs `--help` on every script under `scripts/`; run pyflakes in CI. |

## Verdict
This is the model the other skills should be held to. Its remaining problems are portability (D1, D2) and the non-deterministic verifier (D3).

**Top 3 actions:** (1) `.gitattributes` + re-hash fixtures, (2) log/pin the Stage 4.6 verifier, (3) archive one-off repair scripts.
