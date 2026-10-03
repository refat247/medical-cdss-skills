# 09 · medical-cdss-unified-orchestrator (v1.4.0) — Independent Audit

**Tier:** Critical path (run-time federation) · **Code:** 417 LOC (+13-line `unified_navigator.py` shim) · **Tests:** 13 pass / 0 fail `[M]`

| Goal fit | Safety | Tests | Docs accuracy | Portability | **Overall** |
|:-:|:-:|:-:|:-:|:-:|:-:|
| B+ | C- | B- | C | C | **C+** |

## What it does well
- The only real federation: queries Davidson through `cdss_federated_search.py` and each book's router, with `--query / --vignette / --validate-therapy / --diff / --outline / --json` `[C]`.
- A 1,500-word output ceiling with an explicit `[TRUNCATED …]` marker and a pointer to query one book `[C]`.
- Warns on stderr when it falls back to an unpackaged router `[C]`.

## Findings
| ID | Sev | Ev | Finding | Fix |
|---|---|---|---|---|
| U1 | **Critical** | C | **"Zero-hallucination drug therapy safety verification" is concatenation.** `run_therapy_validation` runs each book's router `--validate-therapy` and prints the text. The return value is `max(exit codes)`. There is no cross-book comparison, no disagreement flag, no per-claim citation check. | Define a JSON answer envelope; extract dose/route/contraindication fields per book; flag disagreement; return non-zero when any book contradicts another or cites nothing. |
| U2 | High | C | **Partial results exit 0.** `_finish` returns 1 only if *no* source ran; if one of four books answered, the exit code is that book's. A missing Kumar router (no fallback) or missing Davidson script is a printed note. | Report `books_requested / books_responded`; exit non-zero (or a distinct code) unless all requested books responded; add `--require-all`. |
| U3 | High | C | **Latency floor.** Each query spawns one Python process per book (`subprocess.run`). "Sub-millisecond" cannot hold for this path; no benchmark exists. | Offer an in-process or long-lived server mode; benchmark both; qualify the claim. |
| U4 | Medium | C | Truncation at 1,500 words can drop contraindication or dose sections that appear late. | Truncate by section priority (contraindications, doses first) and flag `truncated: true` in JSON. |
| U5 | Medium | C | Inconsistent fallbacks: Harrison/Hurst may use unverified build routers (warn); Kumar has none. `cdss_encoding_guard` import failure is swallowed (`except ImportError: pass`). | Strict mode that refuses unverified routers; report encoding-guard status in output. |
| U6 | Medium | C | Default `D:\01_Medical_Study\…` for the package and two build-router fallbacks; env overrides exist but docs show Windows paths (10 doc lines). | Single config module. |
| U7 | Low | C | `unified_navigator.py` is a 13-line alias for the same code. | Document or remove. |

## Verdict
Right architecture, but it is a fan-out printer, not a verifier. Its name and description promise more than it checks.

**Top 3 actions:** (1) cross-book reconciliation and answer envelope, (2) non-zero on partial results, (3) in-process mode + benchmark.
