# 06 · cdss-retrieval-packager (v1.4.0) — Independent Audit

**Tier:** Critical path (package/federate) · **Code:** 907 LOC · **Tests:** 9 pass `[M]` (needs Pillow; without it the suite errors at collection)

| Goal fit | Safety | Tests | Docs accuracy | Portability | **Overall** |
|:-:|:-:|:-:|:-:|:-:|:-:|
| A- | B- | B- | C+ | C | **B-** |

## What it does well
- Protects trust anchors, checksums and chapter figures from pruning; never prunes `.jpeg/.png` in `assets/figures/` `[C]`.
- Generated federated search returns a per-book `{"error": …}` entry when a book fails, so a failure is visible in the result rather than swallowed `[C]`.
- `compress_excerpt` keeps whole sentences so qualifiers ("unless…", "contraindicated if…") are not cut mid-clause `[C]`.

## Findings
| ID | Sev | Ev | Finding | Fix |
|---|---|---|---|---|
| K1 | High | C | **"Sub-millisecond health verification" is one query.** `verify_package` runs a single query (`"heart failure"`, `top_k=1`) per book and marks PASS if anything is returned. There is no timing and no relevance check. | Use a fixed query set with expected chunk IDs, time each call, assert thresholds from config, report p50/p95. |
| K2 | Medium | C | `patch_paths` **rewrites third-party router source with regexes** (`DEFAULT_DB_PATH = Path(r"D:\\…")`, `INDEX_DIR`, `BASE_DIR`) and has an `except Exception: pass`. If the router template changes, patching silently no-ops and the package keeps pointing at `D:\`. | After patching, re-scan for `[A-Z]:\\` literals and fail if any remain. |
| K3 | Medium | C | `prune` deletes by glob (`*_backup_*.json`, QA scorecards, zips) with no `--dry-run`. | Add `--dry-run`; print a deletion list and bytes freed. |
| K4 | Medium | M | Pillow is imported by `enhance_figures.py` but not declared for this skill (only the bridge publisher has a `pyproject.toml`). | Add `requirements.txt`; skip the figure step with a warning if absent. |
| K5 | Low | C | `enhance_figures.py` is duplicated "byte-identical" with the bridge publisher. | Shared module or a hash-equality test. |
| K6 | Low | C | 4 hard-coded `D:\` code lines (inside patch regexes and templates) and 5 in docs. | Env-based. |

## Verdict
Does its packaging job; the "verifies sub-millisecond retrieval health" claim is not supported by what the code checks.

**Top 3 actions:** (1) real timed verification with expected answers, (2) post-patch path scan, (3) dry-run for prune.
