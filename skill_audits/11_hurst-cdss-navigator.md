# 11 · hurst-cdss-navigator (v1.0.2) — Independent Audit

**Tier:** Critical path (single-book run-time) · **Book:** Fuster & Hurst's The Heart 15th Ed (5,258 chunks claimed) · **Tests:** 6 pass / 3 skipped on this machine `[M]`

| Goal fit | Safety | Tests | Docs accuracy | Portability | **Overall** |
|:-:|:-:|:-:|:-:|:-:|:-:|
| B | C | C+ | C | C | **C+** |

## What it does
A thin wrapper (~100–200 LOC) that locates a prebuilt `cdss_qa_router.py` under `$CDSS_PACKAGE_DIR` and runs it with `subprocess.run` for `--query`, `--vignette`, `--outline`, `--diff`, `--validate-therapy`. All retrieval, ranking and drug-matrix logic lives in the router, which is **not in this repo**.

## Findings
| ID | Sev | Ev | Finding | Fix |
|---|---|---|---|---|
| N1 | Medium | C | **"Zero-Hallucination & Provenance Guarantee" in SKILL.md is not something this code can guarantee.** It forwards router output; the guarantee depends wholly on an unseen artefact. | Reword to "returns router output with its chunk IDs"; add a test that every returned chunk carries an ID. |
| N2 | Low | M | Tests that need the real corpus **skip** when it is absent (3 skipped), so the suite is green here but proves nothing about retrieval without the author's disk. This is better than Harrison/Kumar, which fail. | Run the same tests against a tiny fixture package so they execute everywhere. |
| N3 | Medium | C | `subprocess.run(..., errors="ignore")` **silently drops undecodable bytes** from router output. In a pipeline built around mojibake detection, this hides encoding corruption instead of surfacing it. | Use `errors="strict"` (or `replace` plus a visible warning count). |
| N4 | Medium | C | The README says "sub-millisecond", which can only describe the router's in-process index lookup; each CLI call spawns a new Python process, so end-to-end latency is process-start dominated. The wrapper measures nothing. | Report wall-clock in the wrapper; separate "index lookup" from "CLI call" in the docs. |
| N5 | Low | C | Fallback to an unpackaged build router (Harrison/Hurst) vs none (Kumar): inconsistent trust behaviour across the three navigators. | One shared behaviour (warn+strict flag). |
| N6 | Low | C | **Triplicated code:** the three navigators are near-copies (diff of the Hurst script against Harrison's template is ~50 lines). Any fix must be made three times. | One parametrised `book-navigator` module with per-book config; keep three thin SKILL.md entry points if triggers matter. |

## Verdict
Fine as a launcher, over-described as a guarantee, and not independently testable without the author's disk.

**Top 3 actions:** (1) fixture-based tests, (2) stop ignoring decode errors, (3) merge the three scripts.
