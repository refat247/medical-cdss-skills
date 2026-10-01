---
name: medical-index-rag-compiler
version: 1.3.0
description: |
  Autonomous Index Intelligence Compiler for medical textbooks (Davidson, Hurst, Braunwald, Harrison).
  Compiles back-of-the-book index markdown and completed chapter RAG files (*_RAG_Optimised.md) into
  the complete 26-asset index intelligence suite, GraphRAG co-occurrence networks, GBNF grammars,
  a chunk-derived drug-mention matrix, a computed synthetic self-topic retrieval benchmark, and a small lexical CDSS router (query/vignette only).
---

# Medical Index RAG Compiler (v1.3.0)

Production-grade Autonomous Index Intelligence Compiler for medical textbooks and clinical guidelines. Converts completed chapter RAG outputs (`*_RAG_Optimised.md`) and back-of-the-book index markdown files into a comprehensive, zero-hallucination, sub-millisecond Clinical Decision Support System (CDSS) suite.

---

## 🎯 1. When to Activate This Skill

Activate this skill automatically whenever:
- All chapters or sections of a medical textbook have completed Stages 1 through 18 of the RAG pipeline (`*_RAG_Optimised.md` files exist).
- A back-of-the-book index has been converted to markdown (e.g. via `davidson-ocr-preready` $\rightarrow$ `markdown_inlined.md` or similar).
- The user or physician asks to **"build the index assets"**, **"generate the inverted index"**, **"compile index intelligence"**, or **"create the CDSS router for this book"**.
- Porting the 26-asset architecture from *Hurst's The Heart* to another clinical textbook (*Davidson's Principles and Practice of Medicine 25th Edition*, *Braunwald's Heart Disease*, *Harrison's Principles of Internal Medicine*).

---

## ⚡ 2. Primary CLI Command

The compiler is executed via the unified pipeline orchestrator:

```powershell
python -m scripts.compiler `
  --book "Davidson's Principles and Practice of Medicine" `
  --edition "25th Edition" `
  --corpus "D:\davidson_25_true\TRUE_MD_WITH_IMAGES" `
  --index "D:\davidson_25_true\TRUE_MD_WITH_IMAGES\Davidson_25_Index\markdown_inlined.md" `
  --output "D:\davidson_25_true\TRUE_MD_WITH_IMAGES\Index\rag_pipeline_output"
```

### Optional Flags
| Flag | Description | Default |
|---|---|:---:|
| `--skip-eval` | Skips running the 768-triplet benchmark test harness | `False` |
| `--eval-triplets <N>` | Number of hard-negative evaluation triplets to synthesize | `768` |
| `--prefix <NAME>` | Prefix for generated asset files | Extracted from `--book` |
| `--dry-run` | Validates chunk files and index markdown without writing outputs | `False` |

---

## 🏗️ 3. Autonomous 6-Phase Pipeline Architecture

When invoked, the compiler executes through 6 deterministic, zero-token local phases:

```
[Phase 1: Lexicons & Registries] ──> [Phase 2: Master Catalog & Inverted Index]
                 │
                 ▼
[Phase 3: Knowledge Graphs & Guardrails] ──> [Phase 4: Next-Gen Optimizers & GBNF]
                 │
                 ▼
[Phase 5: Benchmark Evaluation (768 Triplets)] ──> [Phase 6: CDSS Router & Skill Scaffold]
```

### Phase 1: Lexicons & Registries
- Extracts all clinical acronyms and abbreviations into `*_synonyms_and_acronyms.json`.
- Detects and catalogues landmark randomized clinical trials into `landmark_clinical_trials_registry.json`.
- Parses index taxonomic hierarchies into `index_concept_hierarchy.json`.
- Extracts typographical locator anchors (Tables `t`, Figures `f`, Plates `c`, and page ranges) into `*_typographical_anchors.json`.

### Phase 2: Master Catalog & Inverted Index
- Scans all `*_RAG_Optimised.md` markdown files across the corpus.
- Parses frontmatter and body for all L2 micro-chunks, emitting `*_chunks_master_catalog.json`.
- Generates the integer-offset corpus-wide lexical search index `*_inverted_chunk_index.json`.
- Compiles direct chunk pointer maps: `*_trial_to_chunks_map.json` and `*_synonym_to_chunks_map.json`.

### Phase 3: Clinical Knowledge Graphs & Guardrails
- Synthesizes `*_concept_subtrees.json` for prompt-ready 120-token medical checklists.
- Extracts `"See"` and `"See also"` directives into `*_index_directed_graph.json` for GraphRAG.
- Identifies polysemous, overloaded medical terms for `*_polysemy_disambiguation.json`.
- Corroborates drug indications and contraindications into `*_drug_disease_safety_matrix.json`.
- Computes Inverse Section Frequency (ISF) to build `*_early_exit_section_index.json` (< 0.2 ms routing).

### Phase 4: Next-Gen Optimization & Constrained Decoding
- Compiles `*_canonical_semantic_cache.json` for instant 0.00 ms retrieval.
- Extracts look-alike differential comparators into `*_differential_comparators.json`.
- Calculates page citation intersections to emit `*_clinical_cooccurrence_graph.json`.
- Generates `*_entity_grammar.gbnf` (llama.cpp/vLLM) and `*_entity_schema.json` (OpenAI/Gemini).
- Calculates BM25 token salience multipliers into `*_index_salience_bm25_weights.json`.

### Phase 5: Automated Benchmark Test Harness
- Samples up to N chunks and uses each chunk's own topic as the query (a SYNTHETIC SELF-TOPIC benchmark: an upper bound for lexical retrieval over this catalog, not clinical retrieval quality). Hard negatives are the best-scoring non-gold chunks; ties are scored pessimistically.
- Computes Hit@1, Hit@3, MRR, hard-negative discrimination and in-process lookup latency (P50/P95) from the built index, writes raw per-query results (`*_benchmark_raw_results.json`) and `BENCHMARK_SCORECARD.md`; exits 1 if targets are missed (override: `--allow-benchmark-fail`). Token compression is not measured.
- Emits formal `BENCHMARK_SCORECARD.md`.

### Phase 6: CDSS Router & Skill Scaffold
- Writes a small REAL lexical `cdss_qa_router.py` (`--query`, `--vignette`, `--json`, `--top_k`). `--validate-therapy`, `--outline` and `--diff` are NOT implemented by the generated router and exit 2.
- Scaffolds a new dedicated `<book>-cdss-navigator` skill definition ready for deployment to `~/.gemini/config/skills/`.

---

## 📦 4. Complete Output Deliverables (26 Assets)
Upon completion, the target output directory will contain:
1. `*_synonyms_and_acronyms.json`
2. `landmark_clinical_trials_registry.json`
3. `index_concept_hierarchy.json`
4. `*_typographical_anchors.json`
5. `*_chunks_master_catalog.json`
6. `*_inverted_chunk_index.json`
7. `*_trial_to_chunks_map.json`
8. `*_synonym_to_chunks_map.json`
9. `*_concept_subtrees.json`
10. `*_index_directed_graph.json`
11. `*_polysemy_disambiguation.json`
12. `*_drug_disease_safety_matrix.json`
13. `*_early_exit_section_index.json`
14. `*_rag_eval_triplets.json`
15. `*_canonical_semantic_cache.json`
16. `*_differential_comparators.json`
17. `*_clinical_cooccurrence_graph.json`
18. `*_entity_grammar.gbnf`
19. `*_entity_schema.json`
20. `*_index_salience_bm25_weights.json`
21. `build_inverted_chunk_index.py`
22. `build_advanced_index_suite.py`
23. `build_nextgen_index_assets.py`
24. `cdss_qa_router.py`
25. `eval_index_retrieval.py`
26. `BENCHMARK_SCORECARD.md`

---

## 🔒 5. Versioning & Quality Standards
This skill strictly implements:
- [SemVer 2.0.0](https://semver.org/) rules via `version-manager`.
- Zero version drift across `SKILL.md`, `README.md`, `CHANGELOG.md`, and Python modules.
- Verification gate: `python -m scripts.bump_version <skill_dir> --verify`

## Trusted-Only Indexing (2026-09-25)
- Phase 2 indexes a chapter only if the RAG pipeline's `classify_trust()` marks its output folder `trusted_for_downstream_use`. This is the same verdict as `CORPUS_TRUST_STATUS.md`.
- Protection markers and the Stage 8 checkpoint flag alone do not count.
- Only one copy of each chapter file is indexed: the canonical `rag_pipeline_output` folder wins, and backup, audit and bundle copies are skipped. This prevents duplicate chunks.
- `--allow-unverified` includes untrusted chapters anyway, with a loud warning.
- Requires the `davidson-rag-pipeline-antigravity` skill next to this one (override the location with `CDSS_SKILLS_ROOT`).
