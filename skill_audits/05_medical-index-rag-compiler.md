# 05 · medical-index-rag-compiler (v1.2.0) — Independent Audit

**Tier:** Critical path (index) · **Code:** 645 LOC · **Tests:** 11 pass / 0 fail `[M]`

| Goal fit | Safety | Tests | Docs accuracy | Portability | **Overall** |
|:-:|:-:|:-:|:-:|:-:|:-:|
| C | F | C | F | B | **D** |

The description promises "26-asset index intelligence suite, GraphRAG networks, GBNF grammars, drug safety matrices, 768-triplet validation, turnkey CDSS routers". The code I read delivers materially less.

## Findings
| ID | Sev | Ev | Finding | Fix |
|---|---|---|---|---|
| I1 | **Critical** | C | **Fabricated benchmark.** `phase_5_benchmark_retrieval` writes `BENCHMARK_SCORECARD.md` from a literal table: Hit@1 78.4%, Hit@3 89.1%, MRR 0.824, P50 6.54 ms, token savings 95.8%, all "PASS". No retrieval runs and nothing is timed. Identical for every book. The triplets use each chunk's own topic as the query and the chunk 50 positions away as the "hard negative". | Delete the literal table. Implement a real evaluation (run queries against the built index, time with `perf_counter_ns`, compute metrics, exit non-zero below threshold); write raw per-query results next to the scorecard. |
| I2 | **Critical** | C | **The "turnkey `cdss_qa_router.py`" is a stub.** Phase 6 emits a script whose `main()` only prints `[CDSS ROUTER] Query received: …`. It has no retrieval and none of `--validate-therapy`, `--outline`, `--diff` that the navigators and unified orchestrator call. The packager's verification imports `HarrisonCDSSRouter.retrieve_chunks`, a class this compiler does not produce. The real routers are therefore built by something not in this repo. | Either generate the real router here (and test it) or rename Phase 6 "scaffold" and document where production routers come from. Add a contract test: compiler output ⇒ `navigator.py --query` returns chunks. |
| I3 | High | C | **"GraphRAG co-occurrence graph" is adjacent index terms.** Edges link `index_terms[i]` to `index_terms[i+1]` (alphabetical neighbours) with weight 1.0 and are published as `comorbidities`. Alphabetical adjacency is not clinical co-occurrence; a consumer would read these as clinical relations. | Build edges from actual co-occurrence (same chunk or index page) with counts; label otherwise. |
| I4 | Medium | C | **Cardiology-specific input used for every book:** the GBNF grammar and JSON schema read a hard-coded `cardiology_synonyms_and_acronyms.json`, take the first 50 keys, and fall back to the placeholder `"ACRONYM"` if absent. The grammar constrains output to a single `{"acronym": …}` field. | Parameterise per book; fail when the synonym file is missing instead of emitting a placeholder grammar. |
| I5 | Medium | C | Description claims "drug safety matrices"; I found no code deriving one in the phases read (4 and 6). Not verified exhaustively. | Verify or remove the claim. |
| I6 | Low | C | README says "P50 under 10 ms", SKILL says sub-ms elsewhere, scorecard says 6.54 ms. Three different numbers, none measured. | Single measured number (see I1). |

## What works
Index ingestion, chunk cataloguing and inverted-index phases exist and are tested (11 tests); the compiler consults the pipeline trust classifier before building `[C]`.

## Verdict
Highest claim-to-implementation gap in the repo. Until I1 and I2 are fixed, its outputs should not be described as benchmarked or turnkey.

**Top 3 actions:** (1) remove the hard-coded scorecard, (2) real router or honest rename, (3) real co-occurrence edges.
