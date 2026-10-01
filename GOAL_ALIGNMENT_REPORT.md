# CDSS Skills — Goal Alignment & Architecture Audit

Repo: `refat247/medical-cdss-skills` @ `b0d0189` (19 skills, 283 files). Audit date: 2026-10-01.

**Method.** I read SKILL.md frontmatter for all 19 skills and the orchestrator/navigator source. I grepped for cross-skill version constraints, hardcoded paths and performance claims. I ran `version-manager --suite . --verify`, `clean-my-ai-harness/scripts/check_skill_overlaps.py`, and the pytest suites for 11 skills. **Not done:** I could not run anything against the real corpora (`D:\01_Medical_Study\...`, `D:\HABIJABI_FULL`), so retrieval latency, retrieval accuracy and clinical correctness are *unmeasured here*, not shown to be bad. The Davidson pipeline (47 scripts, 48 tests) was sampled, not audited stage by stage.

**Evidence tags:** `[M]` = measured by running something; `[C]` = read directly in code; `[I]` = inferred, not verified.

---

## 1. Executive summary

The 19 skills are not one system. They are **three loosely coupled systems plus an infrastructure layer**:

1. a **build-time manufacturing line** (skills 1–7, chained by `medical-rag-orchestrator`);
2. a **run-time retrieval layer** (3 single-book navigators, `medical-cdss-unified-orchestrator`, and the Habijabi pair);
3. **infrastructure/meta skills** (15–19), which are orthogonal to the clinical goal.

The build side is the most mature part. It has a real trust ledger, fail-closed finalization, a clinical-fidelity gate (Stage 4.5d), 48 pipeline tests, and an orchestrator that consults the pipeline's own trust classifier instead of re-deriving trust `[C]`. The goal statement is weakest on the **run-time side**, where the headline claims ("zero-hallucination", "sub-millisecond", "federated 4-textbook") are mostly assertions in prose and are in places **contradicted by the code**:

- `kawsar-habijabi-cdss-navigator --federated` prints hard-coded boilerplate for Harrison, Hurst and Kumar & Clark and never queries them `[C]`.
- Its prescribing-safety and SBA features are four-to-six hand-typed Python dict entries, and "no match" returns `PERMITTED_WITH_ROUTINE_MONITORING` `[C]`.
- The index compiler's `BENCHMARK_SCORECARD.md` writes **hard-coded** "78.4% / 6.54 ms / PASS" figures. No evaluation is executed `[C]`.
- `version-manager --suite --verify` reports "19/19, 0 drift" `[M]` while `davidson-ocr-preready` stamps `skill_version: "1.6.0"` into every output though the skill is 1.7.5 `[C]`.

Because nothing validates the *final* CDSS answer, and no skill owns end-to-end verification, a wrong or hallucinated answer has no clear owner. The highest-value work is not more features. It is to (a) remove or quarantine the code paths that fabricate evidence, (b) add one run-time grounding gate that every answer path must pass, (c) add one hermetic end-to-end fixture test, and (d) turn version governance into a real cross-skill contract.

---

## 2. Direct answers to the seven questions

### 2.1 Goal alignment

| Tier | Skills | Contribution to goal |
|---|---|---|
| **Critical path** | 1 mojibake-guard, 2 book-split-organizer, 3 ocr-preready, 4 rag-pipeline, 5 index-compiler, 6 retrieval-packager, 8 rag-orchestrator, 9 unified-orchestrator, 10–12 navigators | Direct: corpus → verified chunks → retrievable CDSS |
| **Goal-adjacent (documentation leg)** | 7 bridge-note-publisher | Delivers the "journal-grade clinical documentation" half of the goal; the only skill with a claim-level grounding verifier |
| **Separate product** | 13 kawsar-habijabi, 14 clinical-preceptor | Serves a *different corpus* (Habijabi bedside series) and an *educational* use case. It does not feed or consume the textbook pipeline except via a bridge CSV |
| **Orthogonal / support** | 15 antigravity-protocol, 16 ultimate-protocol, 17 clean-my-ai-harness, 18 token-audit, 19 version-manager | Agent-behaviour and repo hygiene. No clinical contribution. Only 19 is invoked by the pipeline (`verify-versions`) |

**Measurable contribution:** only the build stages have measurable outputs (trust classification, Stage 6 pass/fail, 26-asset suite). Skills 9–14 have no stated, testable acceptance criterion tied to the goal (see F1–F3, F6).

### 2.2 Architectural coherence

- **Data contract between stages** exists in prose for 3→4 (`davidson-ocr-preready/references/ocr_handover_contract.md`: `markdown_inlined.md` + `assets/figures/`) and is *machine-checked* for 4→5 and 4→8 through the trust ledger (the orchestrator and `compiler.py` both import `build_chapter_trust_record`) `[C]`. The 5→6 and 6→9/10–12 handoffs are **implicit file-layout conventions** (`02_Harrison_22/Index/cdss_qa_router.py` etc.) with no schema or version stamp `[C]`.
- **Handoffs are all synchronous and file-based.** The orchestrator uses `subprocess.run`; the unified orchestrator spawns one Python subprocess per book per query `[C]`. There is no async path and no message contract.
- **Isolation is poor.**
  - The orchestrator imports a private function, `pipeline.stages.trust_ledger.build_chapter_trust_record` (also `compiler.py`).
  - `cdss-retrieval-packager/scripts/enhance_figures.py` and the copy in `cdss-bridge-note-publisher` are "kept byte-identical" by hand `[C]`.
  - `clinical-preceptor` subprocess-calls `kawsar-habijabi`'s script at a hard-coded `C:\Users\User\.gemini\...` path, falling back to a workspace copy `[C]`.
  - Every runtime skill hard-codes `D:\01_Medical_Study\CDSS_Retrieval_Package` or `D:\HABIJABI_FULL` as its default `[C]`.

### 2.3 Redundancy & overlap

- **`medical-rag-orchestrator` vs `medical-cdss-unified-orchestrator`: complementary, not redundant.** One is build-time, one is query-time. The names ("orchestrator") are misleading, but the only shared file is `CDSS_Retrieval_Package`. No change needed beyond naming and a one-line pointer in each SKILL.md.
- **`kawsar-habijabi` "4-textbook federation" vs `unified-orchestrator`: duplicate in name, not in function. This is the dangerous case.** The unified orchestrator really federates (it calls `cdss_federated_search.py` and the three routers). Kawsar's `--federated` does not (F1). It reimplements the idea with stub text instead of calling the unified orchestrator.
- **`clinical-preceptor` vs `kawsar-habijabi`: real overlap, with a half-finished split.**
  - Preceptor modalities 1–6 (Socratic, SBA, prescribing safety, federated, tropical calc, bilingual search) are *forwarded by subprocess* to Kawsar's script. Preceptor implements 7–13 itself.
  - Both SKILL.md files claim "SBA generation" and "prescribing safety". Only one implementation exists, in Kawsar, so the preceptor's "13 modalities" is really 7 + a pass-through.
  - Preceptor's `--never-events` reads a CSV matrix (`never_events_toxic_drug_matrix.csv`), while Kawsar's `--prescribing-safety` uses hand-typed rules. Two prescribing-safety sources of truth, with different grounding quality.
- **`clean-my-ai-harness/check_skill_overlaps.py` does not detect any of this.** It is a hard-coded name/keyword check on three navigators and the two protocols `[M]`. It reports "All boundaries verified" for a repo with the overlaps above.

### 2.4 Version & dependency governance

- **No declared cross-skill constraints exist anywhere** (grep for requires/min-version/compat across SKILL.md and orchestrators returned nothing) `[M]`. The orchestrator hard-codes sibling paths (`SKILLS_ROOT/...`) and never checks sibling versions.
- **Nobody enforces alignment.** `version-manager --suite --verify` checks each skill *against itself* (declarations in SKILL.md, `__init__`, tests, etc.). It cannot detect `rag-orchestrator 1.4.0` running against an incompatible `rag-pipeline`. Its "19/19 · 0 drift" output is true but easy to over-read `[M]`.
- **It also misses real drift:** `davidson-ocr-preready/preready/auditor.py` has `SKILL_VERSION = "1.6.0"` (skill is 1.7.5) and writes it into output provenance `[C]`.
- **Stale provenance names:** Stage 4.7 emits `skill_name: "davidson-rag-pipeline-hyperagent"` and several docstrings say `davidson-rag-pipeline-cc` `[C]`.

### 2.5 Configuration & rules conflicts

- **Antigravity vs Ultimate.** The conflict is declared in both SKILL.md files, but enforced by nothing but the model reading the notice. It is a prose rule only.
- **Other conflicts found:**
  1. **Encoding.** The mojibake guard is a pre-flight step in the orchestrator, but the unified orchestrator imports `cdss_encoding_guard` inside `try/except ImportError: pass` (silent degradation) `[C]`.
  2. **Path model.** Windows `D:\` / `C:\Users\User` defaults vs. the `CDSS_SKILLS_ROOT` / `CDSS_PACKAGE_DIR` env vars that only some skills honour.
  3. **Trust model.** The unified orchestrator falls back to *UNPACKAGED, not trust-verified* build routers for Harrison/Hurst (with a stderr warning), while the pipeline treats trust as fail-closed `[C]`. Kumar has no fallback. The behaviour is inconsistent across books.
  4. **Chunking/index formats** are consistent by construction only because one pipeline builds all books. I found no conflicting declarations but also no schema that would catch one.
- **What `clean-my-ai-harness` finds:** `[M]` all-pass, because its checks are narrow. It is also unrelated to the clinical goal.

### 2.4/2.6 Coverage gaps

| Gap | State |
|---|---|
| **End-to-end validation** (PDF → chunks → CDSS answer) | **Missing.** `medical-rag-orchestrator status/auto` reports per-chapter trust, not an end-to-end answer check. No fixture-to-answer test exists. |
| **Regression across skill boundaries** | **Missing.** Tests are per-skill. Davidson has strong regression fixtures (ch02, ch05). Nothing tests "pipeline output still loads in compiler/packager/navigator". |
| **Hermetic tests** | `[M]` Kumar 7 failed / 5 passed and Harrison 1 failed / 6 passed here because the tests need `D:\...\CDSS_Retrieval_Package`. `cdss-retrieval-packager` errored at collection and `cdss-bridge-note-publisher` had 1 failure, both because of missing Pillow (an undeclared dependency in those environments). The orchestrator, unified-orchestrator, guard, compiler, ocr-preready and version-manager suites passed (22, 11, 13, 11, 19, 8). |
| **Clinical fidelity of final output** | Build-time: Stage 4.5d (chunk vs source). Document-time: `verify_grounding.py` (bridge notes only). **Run-time answers: nothing.** |
| **Untested skills** | `kawsar-habijabi` (0 tests, no README/CHANGELOG), `clinical-preceptor` (1 version test; 894-line `generate_extended_modalities.py` untested), `clean-my-ai-harness` (0 tests, 6 scripts). |

### 2.7 Performance claims & ownership

- "Sub-millisecond" appears in unified, packager, kawsar, hurst README, index-compiler README (as "P50 under 10 ms", which is not sub-ms) and preceptor. Harrison claims `<0.2 ms` and Kumar `<2 ms` for the *early-exit index lookup*.
- The unified CLI path spawns a fresh Python process per book per query `[C]`; process start alone is tens of ms. "Sub-millisecond" can be true only for an already-loaded in-process lookup, and no benchmark in the repo measures even that. The only measurement code (`run_retrieval_accuracy.py` in the Davidson pipeline) is Davidson-only.
- The packager's "sub-millisecond smoke test" checks for FAIL strings in router output; I found no timing assertion.
- **Ownership model:** none. A slow query could be the router, the federated script, the subprocess spawn, the budget truncation or the corpus size, and no doc assigns that. A hallucinated claim could originate from the build (4.x gates), the retrieval, the `enforce_token_budget` 1,500-word truncation (which silently cuts evidence), or hand-typed content in Kawsar.

---

## 3. Findings

Severity reflects patient-safety/trust impact first, then goal impact. All fix steps are actionable. For the Critical and High findings I give the full multi-step fix. For Medium/Low I compress to the essential steps.

### F1 — Kawsar `--federated` presents canned text as 4-book grounding
- **Category:** Alignment Gap · **Severity:** Critical · **Skills:** 13 (and 14, which forwards to it)
- **Current:** `run_federated()` finds one bridge-CSV row by substring match and **falls back to `bridge_rows[0]`** (an unrelated topic) if nothing matches. It then prints the Davidson fields from the CSV and, for Harrison, Hurst and Kumar & Clark, **fixed sentences** (e.g. "Hemodynamic pressure-volume loops, non-invasive imaging…") that are identical for every topic. Even a non-cardiology topic gets the Hurst blurb `[C]`.
- **Expected:** a topic-specific query to each book via the existing federated search, returning chunk IDs and citations, with "no evidence found" when nothing matches.
- **Impact if unfixed:** a clinician or exam candidate sees a "4-textbook consensus" that was never retrieved. This is exactly the failure mode the goal statement promises not to have.
- **Fix:**
  1. Delete the three canned book blocks and the `bridge_rows[0]` fallback immediately; return "NO BRIDGE MATCH" instead.
  2. Replace them with a call into `medical-cdss-unified-orchestrator` (`run_federated_query` / `--query <topic> --book all --json`) so there is a single federation implementation.
  3. Make the output structure `{book, chunk_id, section, text_span}` per book, and print "no retrieved evidence" per empty book.
  4. Resolve the unified package location through `CDSS_PACKAGE_DIR`, not a literal path.
  5. Fail closed with a non-zero exit if fewer books respond than were requested.
  6. Add tests with a tiny fixture corpus covering: match, no-match, one book missing.
  7. Until the above ships, edit both SKILL.md descriptions to say "bridge-anchored Habijabi→Davidson lookup" rather than "4-textbook federation".
  8. Add a CHANGELOG entry and bump to 1.1.0 via `version-manager`.
  9. Make the preceptor's `--federated` modality inherit the fix by delegating, not duplicating.
  10. Add a check to `check_skill_overlaps.py` that fails if two skills both claim "federation" and only one imports the federation code.

### F2 — Hard-coded clinical content and a permissive safety default
- **Category:** Alignment Gap (safety) · **Severity:** Critical · **Skills:** 13, 14
- **Current:** `run_exam_sba` picks from a **4-item in-code bank** (HABIJABI-001/003/005/012) although the README and SKILL.md present it as an engine over 137 records. `run_prescribing_safety` has **six hand-written rules** keyed on substrings (e.g. "gout" + "allopurinol"). When none matches it prints `INTERCEPT STATUS: [PERMITTED_WITH_ROUTINE_MONITORING]` and "No hard-stop contraindications… detected" `[C]`. Citations like `Davidson 25th Ed, Ch 25` are literal strings, not looked up from chunks.
- **Expected:** SBA items generated from, or validated against, source records; a safety check that returns *UNKNOWN / NOT CHECKED* when it has no rule, and that is driven by data (like the preceptor's CSV matrix) with chunk-verified citations.
- **Impact if unfixed:** "no match" is read as "safe." A drug not in the six rules, misspelt, or phrased differently passes as permitted. This is the single most dangerous behaviour in the repo.
- **Fix:**
  1. Change the default verdict to `NOT_EVALUATED — no matching rule; this is NOT a safety clearance` and exit non-zero.
  2. Remove the "Verify renal and hepatic dosing…" reassurance text from the default branch.
  3. Move the six rules into a data file (`rules.csv/json`) with fields: id, trigger terms, severity, source_chunk_id, source_book, page.
  4. Unify with preceptor's `never_events_toxic_drug_matrix.csv` so there is one pharmacovigilance source of truth.
  5. Add a validator that every `citation` resolves to a real chunk in the packaged corpus, run in CI.
  6. Normalise input (case, brand/generic synonyms, plural) and test with misspelling and synonym cases.
  7. Load the SBA bank from the 137 verified records, or label the four items "demo items".
  8. Require each SBA item to carry the source record id and a verified key rationale chunk.
  9. Add unit tests that a drug with no rule yields `NOT_EVALUATED`, never `PERMITTED`.
  10. Have a clinician review the six rules and record sign-off in the CHANGELOG.

### F3 — No run-time grounding/fidelity gate for CDSS answers
- **Category:** Alignment Gap · **Severity:** Critical · **Skills:** 9–14 (owner: none)
- **Current:** Grounding is enforced at build time (Stage 4.5d, trust ledger) and at *document* time (`verify_grounding.py` inside bridge-note publishing). The run-time paths (navigators, unified `--validate-therapy`, `--vignette`, Kawsar, preceptor) print retrieved text. `run_therapy_validation` calls each book's router in turn and returns `max(exit codes)`, so there is **no reconciliation, conflict detection or "books disagree" signal**. `enforce_token_budget` silently truncates at 1,500 words `[C]`.
- **Expected:** every answer path passes through one verifier ("No chunk, no result") and surfaces disagreement between books.
- **Impact if unfixed:** the goal's "zero-hallucination" has no enforcement where clinicians actually use the system, and conflicting dosing across books is invisible.
- **Fix:**
  1. Extract `verify_grounding.py`'s claim→chunk check into a shared module (e.g. `cdss-grounding-core`) or into the unified orchestrator.
  2. Define a single answer envelope: `{answer, claims:[{text, chunk_ids, book}], unmatched_claims, books_queried, books_responded, truncated}`.
  3. Make every runtime skill emit that envelope with `--json`.
  4. Add a "disagreement" step in therapy validation that compares extracted dose/route/contraindication fields across books and flags differences instead of concatenating text.
  5. Make truncation explicit in the envelope (`truncated: true`, words dropped), and never drop contraindication or dose sections first.
  6. Treat "0 books responded" and "1 of 4 responded" as distinct statuses.
  7. Add a gold set of 30–50 clinician-verified Q→chunk pairs per book as a regression suite.
  8. Run the gold set in CI and publish pass rates in a scorecard that is *computed* (see F4).
  9. Name the unified orchestrator as the owner of "answer correctness" in its SKILL.md.
  10. Add a periodic clinician spot-audit step recorded in a ledger like the existing trust ledger.

### F4 — Fabricated benchmark scorecard
- **Category:** Performance Gap / Documentation Gap · **Severity:** Critical · **Skill:** 5 `medical-index-rag-compiler`
- **Current:** `phase_5_benchmark_retrieval()` generates triplets (query = the chunk's own topic, negative = chunk at index+50) and then **writes a literal markdown table**: Hit@1 78.4% PASS, Hit@3 89.1%, MRR 0.824, P50 6.54 ms, token savings 95.8%. No retrieval is run and no timing is taken. Every book gets identical numbers `[C]`.
- **Expected:** metrics computed from a real run, with the script failing the build if a threshold is missed.
- **Impact if unfixed:** the artifact that anyone reading will treat as evidence of quality is invented. It undermines every other trustworthy gate in the system.
- **Fix:**
  1. Remove the hard-coded table right away, and write "NOT EVALUATED" in its place.
  2. Implement the harness: load the generated router, run each triplet's query, record rank of gold, rank of negative, and `time.perf_counter_ns()` per query.
  3. Compute Hit@1, Hit@3, MRR, hard-negative discrimination, and p50/p95/p99 latency from those records.
  4. Use queries that are *not* the chunk's own topic string (e.g. paraphrases or index-entry terms), because self-topic queries inflate Hit@1 trivially.
  5. Choose negatives by lexical similarity, not `index+50`.
  6. Compare each metric to its target and exit non-zero on failure.
  7. Record chunk count, hardware and timestamp in the scorecard.
  8. Persist raw per-query results as JSON next to the scorecard.
  9. Add a test that fails if the scorecard contains numbers with no raw-results file.
  10. Re-generate scorecards for all existing books and replace the published ones.

### F5 — Version governance gives false assurance; no cross-skill contract
- **Category:** Version Risk · **Severity:** High · **Skills:** 19, 8, 3, 4
- **Current:** see 2.4. `--suite --verify` is intra-skill only, misses `SKILL_VERSION="1.6.0"` in ocr-preready's auditor `[M][C]`, and nothing declares or checks `skill A requires skill B ≥ x`.
- **Expected:** a manifest-level compatibility matrix verified by the orchestrator at start-up.
- **Impact if unfixed:** upgrading the Davidson pipeline (2.25.x → 2.26) can break the orchestrator's private-API import or the compiler silently. The orchestrator would degrade to "RAG TRUST UNKNOWN", which is safe but blocks all work.
- **Fix:**
  1. Add a `requires:` block to each SKILL.md frontmatter (e.g. `medical-rag-orchestrator 1.4.x: davidson-rag-pipeline-antigravity >=2.25,<3; medical-index-rag-compiler >=1.2,<2`).
  2. Teach `version-manager --suite --verify` to read `requires:` and fail on violations, and to resolve it against actual sibling versions.
  3. Extend the declaration scanner to catch `SKILL_VERSION`, `VERSION` and `skill_version:` constants (this would have caught the 1.6.0 stamp).
  4. Fix `auditor.py` to import the skill's `__version__` instead of duplicating it.
  5. Replace the hard-coded `skill_name: "davidson-rag-pipeline-hyperagent"` and `-cc` docstrings.
  6. Have `medical-rag-orchestrator` run the compatibility check as step 0 of `auto`, not only on request via `verify-versions`.
  7. Expose a public, versioned function (`trust_ledger.public_api`) and stop importing `pipeline.stages.*` internals.
  8. Add a test that imports that public API from the orchestrator and compiler.
  9. Add a CI job that runs `--suite --verify` on every PR.
  10. Document the compatibility policy in `version-manager/references/`.

### F6 — Sub-millisecond / zero-hallucination claims are unbenchmarked and inconsistent
- **Category:** Performance Gap · **Severity:** High · **Skills:** 6, 9–14
- **Current:** see 2.7. Claims range from `<0.2 ms` to `<10 ms` to unqualified "sub-millisecond"; the CLI path spawns subprocesses.
- **Expected:** each claim tied to a named metric, a measurement method, and an owner.
- **Impact if unfixed:** users trust latency/accuracy numbers that cannot be reproduced, and there is nobody to ask when queries are slow.
- **Fix:**
  1. Define "retrieval latency" as in-process lookup time on a warm index, and "query latency" as CLI wall-clock.
  2. Add `cdss_bench.py` in the packager that measures both over a fixed query set (e.g. 200 queries) and reports p50/p95/p99.
  3. Make the packager's "health check" assert thresholds from a config file.
  4. Replace unqualified "sub-millisecond" in all descriptions with the measured, qualified figure.
  5. Add a long-lived server or in-process mode to the unified orchestrator so the per-book subprocess spawn is optional.
  6. Record the results in a computed scorecard (reusing F4's harness).
  7. Add an ownership table to the unified SKILL.md: router = index lookup, federated script = fan-out, orchestrator = budget/format.
  8. Add per-stage timing fields to the answer envelope (F3).
  9. Remove "zero-token" claims unless token counts are measured.
  10. Re-run on the actual corpora before release.

### F7 — No end-to-end test; many tests are non-hermetic
- **Category:** Missing Dependency / Coverage · **Severity:** High · **Skills:** 8 and all runtime skills
- **Current:** `[M]` described in 2.6. Navigator tests depend on a Windows corpus path; some skills have undeclared Pillow dependencies; Kawsar and preceptor are essentially untested.
- **Expected:** a repository-level test that takes a 2-page synthetic "book" through all stages and queries it.
- **Impact if unfixed:** a break in the hand-off between skills is only found when a real chapter fails.
- **Fix:**
  1. Create `tests/e2e/` at repo root with a ~3-chunk synthetic corpus (fake book, fake drug) so no copyrighted text is needed.
  2. Run: organizer → preready → pipeline deterministic stages → index compiler → packager → unified query, asserting the final answer contains the expected chunk ID.
  3. Make navigator/unified tests set `CDSS_PACKAGE_DIR` to the fixture package.
  4. Declare dependencies (Pillow, etc.) in `pyproject.toml`/`requirements.txt` per skill, and add a root `requirements-dev.txt`.
  5. Mark corpus-dependent tests with a marker, skipped when the corpus is absent, so the suite is green on CI.
  6. Add tests for Kawsar (F1/F2 behaviours) and a smoke test for each of the 7 preceptor modalities.
  7. Add a cross-skill contract test per boundary (packager output ⇒ navigator input).
  8. Add GitHub Actions to run pytest per skill plus the e2e.
  9. Add the Davidson ch02/ch05 fixtures to the e2e as the "real-shape" case.
  10. Publish coverage per skill.

### F8 — Hard-coded Windows paths and a non-portable skill layout
- **Category:** Missing Dependency · **Severity:** High (portability/operability) · **Skills:** nearly all
- **Current:** `D:\01_Medical_Study\...`, `C:\Users\User\.gemini\config\skills\...` and `D:\HABIJABI_FULL` appear as defaults in code and docs `[C]`. Some skills honour `CDSS_*` env vars; Kawsar and preceptor do not.
- **Impact if unfixed:** the repo cannot run in CI, on another machine, or in this cloud session; failures look like "router not found".
- **Fix:**
  1. Define one config module (e.g. `cdss_paths.py`) reading `CDSS_SKILLS_ROOT`, `CDSS_PACKAGE_DIR`, `CDSS_HABIJABI_ROOT`, with `Path.home()`-based fallbacks.
  2. Replace all literals in code with that module.
  3. In SKILL.md examples, use `$CDSS_SKILLS_ROOT/<skill>/scripts/...` placeholders.
  4. Make Preceptor locate Kawsar via `CDSS_SKILLS_ROOT`, not a literal path.
  5. Fail with an explicit "set CDSS_PACKAGE_DIR" error rather than a hard-coded path.
  6. Add a test that greps the code for `[A-Z]:\\` literals outside docs.

### F9 — Preceptor/Kawsar split is half-done; unclear module boundary
- **Category:** Redundancy · **Severity:** Medium · **Skills:** 13, 14
- **Current:** see 2.3. Preceptor forwards modalities 1–6 to Kawsar by subprocess and implements 7–13 itself; both describe SBA and prescribing safety.
- **Fix:** Make the preceptor the engine and Kawsar a *data profile* (corpus + persona + rule files), or merge them. Move all runtime logic into the preceptor, keep Kawsar as configuration, and have a single SKILL.md per behaviour. Add the missing README/CHANGELOG/tests for Kawsar if it stays. Update descriptions so triggers do not collide. Add a routing note: textbook questions → unified; Habijabi bedside → preceptor.

### F10 — Silent degradation paths
- **Category:** Alignment Gap · **Severity:** Medium · **Skills:** 9, 6
- **Current:** `cdss_encoding_guard` import failure is swallowed (`except ImportError: pass`); Harrison/Hurst fall back to unverified build routers with only a stderr warning; Kumar has no fallback; missing-Davidson prints "not available" and continues `[C]`.
- **Fix:** Expose `books_queried`/`books_responded` and `trust_verified` per book in output; add a `--strict` default for clinical use that refuses unverified fallbacks; log the encoding-guard status in the envelope; make Davidson-unavailable a visible partial-result status.

### F11 — `check_skill_overlaps.py` is too narrow to be called an overlap audit
- **Category:** Documentation Gap · **Severity:** Medium · **Skill:** 17
- **Current:** `[M]` hard-coded names and one keyword test; reports success on a repo with F1, F9 overlaps.
- **Fix:** Compute trigger-phrase overlap between descriptions (n-gram/Jaccard), flag duplicate capability claims ("federat*", "SBA", "prescribing safety") across skills, validate `requires:` (F5), and detect conflicting mutual-exclusion declarations. Add tests, since the skill has none.

### F12 — Task-scope blur: infrastructure skills inside the clinical suite
- **Category:** Alignment Gap · **Severity:** Low · **Skills:** 15, 16, 18 (and 17)
- **Current:** `antigravity-protocol` is triggered "ALWAYS whenever the user asks to write code"; it governs general agent behaviour, not clinical output.
- **Fix:** Document these as "platform" skills in the README and split the table; keep the mutual-exclusion rule and add an executable check; ensure the clinical skills do not depend on them being active (e.g. ultimate-protocol's JSON-only mode would break human-readable clinical output if left on).

### F13 — Duplicated code maintained by hand
- **Category:** Redundancy · **Severity:** Low · **Skills:** 6, 7
- **Current:** `enhance_figures.py` in packager and bridge-publisher is "byte-identical by convention".
- **Fix:** Move to one shared module or add a test asserting the SHA-256 of both files match.

### F14 — Orchestrator naming collision and doc drift
- **Category:** Documentation Gap · **Severity:** Low · **Skills:** 8, 9, 14
- **Current:** three things named "orchestrator" with different roles; Davidson says "18-stage", the orchestrator describes a "7-stage line"; the index-compiler README says "P50 under 10 ms" while others say sub-ms.
- **Fix:** Add a one-page `ARCHITECTURE.md` with the diagram below; rename in prose to "build orchestrator", "query orchestrator", "preceptor engine"; reconcile stage counts ("7 skills, 18 pipeline stages inside skill 4").

---

## 4. Dependency & data-flow diagram

```
                 BUILD TIME  (synchronous, file-based, subprocess)
 ┌─────────────────────────────────────────────────────────────────────────┐
 │  medical-rag-orchestrator (8)  — chains + trust check via trust_ledger   │
 │                                                                         │
 │  PDF ─► [1 mojibake-guard] ◄───────────────────────────── (pre-flight) │
 │   │                                                                     │
 │   ▼                                                                     │
 │  [2 book-split-organizer] ─► OCR dirs (pages/page-*/tbl-*.md, img-*)    │
 │   │            contract: layout_specification.md (prose)                │
 │   ▼                                                                     │
 │  [3 ocr-preready] ─► markdown_inlined.md + assets/figures/              │
 │   │            contract: ocr_handover_contract.md (prose)               │
 │   ▼                                                                     │
 │  [4 rag-pipeline  (18 internal stages, trust ledger, 4.5d fidelity)]    │
 │   │            ► REPAIRED_S2, *_chunks.md, *_RAG_Optimised.md           │
 │   │            ► checkpoint + CORPUS_TRUST  (machine-checked ✔)         │
 │   ▼  (imports private pipeline.stages.trust_ledger  ⚠)                  │
 │  [5 index-compiler] ─► 26-asset index suite, cdss_qa_router.py          │
 │   │            ✖ BENCHMARK_SCORECARD.md is hard-coded (F4)              │
 │   ▼                                                                     │
 │  [6 retrieval-packager] ─► CDSS_Retrieval_Package/{01_Davidson,         │
 │   │            02_Harrison_22, 03_Hurst_15, 04_Kumar_Clark_11}/Index/   │
 │   │            + cdss_federated_search.py     (layout = implicit ⚠)     │
 │   ▼                                                                     │
 │  [7 bridge-note-publisher] ─► .docx   (only skill with grounding gate ✔)│
 └───────────────┬─────────────────────────────────────────────────────────┘
                 │  CDSS_Retrieval_Package (path convention, no version stamp ⚠)
 ┌───────────────▼─────────────────────────────────────────────────────────┐
 │                 RUN TIME  (subprocess per book per query)               │
 │                                                                         │
 │  [10 Harrison] [11 Hurst] [12 Kumar]   single-book navigators           │
 │        ▲            ▲         ▲                                         │
 │        └────────────┴─────────┴───── [9 unified-orchestrator]           │
 │                                        + cdss_federated_search (Davidson)│
 │                                        ⚠ no grounding gate (F3)         │
 │                                        ⚠ concatenates, no reconciliation│
 │                                                                         │
 │   Habijabi corpus (D:\HABIJABI_FULL)  — separate corpus                 │
 │        [14 preceptor] ──subprocess──► [13 kawsar-habijabi]              │
 │        modalities 7–13 own code        modalities 1–6                   │
 │                                        ✖ --federated does NOT call 9    │
 │                                        ✖ hard-coded SBA/safety (F1,F2)  │
 └─────────────────────────────────────────────────────────────────────────┘

 PLATFORM / META (no clinical data flow)
   [19 version-manager]  ◄── called by [8] verify-versions (intra-skill only, F5)
   [17 clean-my-ai-harness] [18 token-audit] [15 antigravity] [16 ultimate]
        (15 ⟂ 16 mutual exclusion — prose only)

 Legend: ✔ enforced in code   ⚠ implicit/fragile   ✖ contradicts stated goal
```

---

## 5. Risk rank — misalignments with the highest impact if unfixed

| Rank | Finding | Why it ranks here |
|---|---|---|
| 1 | **F2** — "no match ⇒ PERMITTED" safety default + hard-coded rules | Direct patient-harm path; fastest and cheapest to fix |
| 2 | **F1** — Kawsar `--federated` fabricates 4-book consensus | Violates the core "zero-hallucination" promise in a user-facing feature |
| 3 | **F4** — Hard-coded benchmark scorecard | Fake evidence of quality; poisons trust in every other metric |
| 4 | **F3** — No run-time grounding / book-disagreement gate | Zero-hallucination is unenforced where answers are produced; no owner |
| 5 | **F5** — Version governance is intra-skill only; stale provenance stamps | Silent breakage on upgrade; provenance in outputs is wrong today |
| 6 | **F7** — No hermetic end-to-end test | Cross-skill breakage only found on real chapters |
| 7 | **F6** — Unbenchmarked latency claims; subprocess-per-query | Claims cannot be reproduced; no performance owner |
| 8 | **F8** — Hard-coded Windows paths | Blocks CI/portability; failures look like missing routers |
| 9 | **F10** — Silent degradation (unverified fallbacks, swallowed ImportError) | Partial answers look complete |
| 10 | **F9** — Preceptor/Kawsar overlap | Two prescribing-safety sources of truth; maintenance drift |

**Suggested order of work:** F2 → F1 → F4 (all three are "remove the fabricated or unsafe behaviour"; days, not weeks) → F7 + F8 (needed before anything else can be verified in CI) → F3 + F5 + F6 (the structural fixes).

## 6. What I could not verify

- Real retrieval latency/accuracy and hallucination rate (no corpus here).
- Correctness of the six Kawsar rules and the Habijabi bridge CSV (needs clinician review).
- Per-stage behaviour inside the 18-stage Davidson pipeline beyond its tests and the orchestrator's use of the trust ledger.
- Whether `cdss_federated_search.py` (generated by the packager) performs cross-book dedup/reconciliation; I read the generator template only briefly.
- The Davidson, packager and preceptor test suites were not all run to completion here. The packager errored at collection (missing Pillow) and the preceptor suite has a single test.
