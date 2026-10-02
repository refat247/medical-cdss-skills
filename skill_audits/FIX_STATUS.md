# Fix Status (after second-sweep fixes + verification review)

Legend: **Fixed** = code changed and a regression test exists. **Partial** = narrowed but not eliminated. **Open** = not addressed.
Every Fixed item is covered by the suites listed at the bottom; none of this has been reviewed by a clinician.

## Fixed (with regression tests)
| Area | What changed |
|---|---|
| Davidson pipeline | Fail-open gates (4.5, 4.5b, 4.5c, 4.5d, 6) now fail closed on zero evidence; NFKC text corruption removed; stage shadowing/predecessor/stale-checkpoint logic; 4.6 verification method recorded; evidence-JSON failures are FAILED; PENDING_MANUAL exits 4; atomic checkpoints; line-ending-independent hashing (`.gitattributes`). |
| Kawsar/Habijabi | Shared tokenizer; whole-word + plural + brand matching; all matching rules shown; alert exits 1, NOT_EVALUATED exits 3, empty 2; negation wording flagged (not parsed); dead `--search` revived; federated is an honest bridge lookup. |
| Compiler | Benchmark is computed (same-topic chunks are not competitors), no hard-coded numbers, dry-run honoured, FAIL exits 1 unless `--allow-benchmark-fail`; generated router exposes `CDSSRouter`/`HarrisonCDSSRouter`; chunk divider heading stripped. |
| Packager | Unique router module names; per-book errors reported with exit 1; federated search exits 1 when no index exists; prune keeps trust evidence; `--dry-run`. |
| Bridge publisher | Anchor ambiguity, table rows as claims, unclassified sections fail, H1 title, no cross-table merging. |
| Mojibake guard | Extended maps; ISMP rules (trailing zero kept for lab denominators only); LaTeX powers/degree/beta; non-UTF-8 detection; dry-run. |
| Unified / preceptor / rag-orchestrator / organizer / preready / version-manager / harness | Exit-code propagation, `--allow-partial`, honest context packet (partial on federated rc 1), backups outside `ocr markdown/`, auditor fixes, atomic version writes, TEST_ASSERTION name restriction. |
| Harrison/Hurst/Kumar | Return-code propagation, hermetic stub-router contract tests. |

## Verification-review findings (Agents E and F)
Both reviewers found regressions introduced by the first round of fixes. Fixed with tests: dead `--search`, guard `/day` ISMP + LaTeX leaks, plural/brand matching, compiler same-topic benchmark / router class / chunk divider, organizer backup location, unified partial packet, federated empty-package exit, version-manager name over-match; and from Davidson review: **H1** (Stage 4.5 blocked every MCQ chapter), **H2** (ligature/soft-hyphen asymmetry in 4.5/4.5b/4.5d), **H3/M1** (structural watermark lines, weak triggers deleting clinical sentences), **M2** (numeric substring match), **M3/M4/L5** (4.5d tie alignment, quadratic runtime, punctuation, re-bulleted negation), **M5** (legacy checkpoint prefix), **M6/M7** (caption headings, publisher PDF URL), **L3/L4** (checkpoint mode, explanation/answer regex).
Still open from those reviews: M2 truncated-line suffix match (wrapped lines still allowed), L1 glued page numbers, L2 TOC-preamble lead-in lines, L6 drug-window cut at decimals, L7 chapter_repairs/releases rerun scripts un-trust frozen chapters, Stage 1 `PIRACY_PATS` not unified, no real-chapter validation (all review inputs synthetic).

## Partial
- Guard: LaTeX handling covers common patterns only (M6/M7 and cleanroom `$..$` remain).
- Kawsar rules match keywords, not meaning: negation is flagged in output but the alert still fires.
- Prescribing screen: 6 fixed rules; still not an interaction checker.

## Open
**Needs a decision or input (not mechanical)**
- Preready M18: cross-run figure overwrite in a shared `--out-dir` (not reproducible within one run; refuse or version the file name?).
- Davidson: edge over-inclusion is not flagged; retrieval "accuracy" is self-retrieval; 1.24 PDF image numbering can mis-name images (unconfirmed).
- Bridge: enhanced figure is looked up by basename (flat output folder); canned fallback.
- Davidson 30 skipped tests need the author's `D:\` corpus (T5).
- `claude-sonnet-5` (default verifier model id) is unverified; override with `CDSS_VERIFIER_MODEL`.
- Davidson F18/F22/F25/F29 and reviewer F13/F14/F20/F21: no individual definitions in the repo (F13/F14 partial under 1.19; F20/F21 sit under 1.30).

**Needs a clinician (all clinical-content concerns)**
- Dengue-shock SBA; MR mutation rationale; gout hard stop; SSRI washout; thalassaemia leaflet.
- Dengue calculator adult weight cap.
- Ch05 `false_positive` adjudication calls (the script is now scoped to the documented chunks, but the calls are clinical).

## Fixed since second sweep (code change plus regression test)
- **Compiler**: M20 (`eGFR` as primary entry), M21 (digits inside terms), M22 (duplicate acronyms), M25 (BM25 weights), M26 (path filter tokens).
- **Bridge** (and packager `enhance_figures.py`): M28 (asterisks, `<br>`), M29 (numbered lists restart), M30 (16-bit greyscale), M31 (refresh enhanced copy), M32 (chapter regex, ambiguous book names).
- **Preready**: M17 (empty header delimiter), M19 (computed completeness, `PARTIAL`, exit 3).
- **Davidson**: 1.20/F10 (marker-hash recheck), 1.24 (table-safe, LaTeX-safe figure tags), 1.26 (adjudication scope, gate evidence not hard-coded), 1.27 (whole-word keywords, body-only, `low_evidence`), 1.28 (batched verifier, `max_tokens` rejected, dict replies), 1.30 mechanical items (Stage 4 report duplicates, newest-checkpoint trust record, Stage 3 short documents, Ch05 backup collision; auto-chain CLI test asserts exit 3). Direct tests now exist for 4.5b, Stage 7 and `chunks_checked==0`. F4-F6 and the anion-gap wording were already fixed.
- **Kumar**: D-26 whole-word, ambiguity-aware drug match.
- **Trigger collisions (3.17)**: descriptions scoped, guarded by `qa/test_trigger_scope.py`.

## Behaviour changes to expect
- Stricter Davidson gates (4.5/6) may fail chapters previously marked trusted; rebuild any chapter produced with the old NFKC step.
- Compiler exits 1 when its own benchmark misses targets (use `--allow-benchmark-fail`).
- Unified `--json` only with `--query`; prescribing screen exit code changed (alert 1).

## Test evidence
Davidson 618 passed/30 skipped; bridge 35; packager 23; guard 50; preceptor ~12; preready 52; Harrison 10; Hurst 11; Kawsar 47; Kumar 13 (7 skipped); organizer 13; unified 27; compiler 25; rag-orchestrator 16; version-manager 17; harness 3; `qa/check_all.py` green; suite verify 0 drift.

## Environment note
If `test_fixture_files_match_manifest_hashes` and `test_real_ch05_manifest_validates_against_fresh_stage_4_5d_run` fail on a fresh clone, the fixtures were checked out as LF although `.gitattributes` pins them to CRLF (the attribute only applies when git writes the files). Fix, with no tracked change: `rm -rf davidson-rag-pipeline-antigravity/tests/fixtures && git checkout -- davidson-rag-pipeline-antigravity/tests/fixtures`. Davidson then runs 589 passed / 30 skipped.
