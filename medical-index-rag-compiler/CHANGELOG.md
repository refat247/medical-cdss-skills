# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.1] - 2026-10-01

### Changed
- Review fixes: same-topic benchmark, CDSSRouter class, chunk divider strip

## [1.3.0] - 2026-10-01

### Changed
- Benchmark is now computed (was a hard-coded scorecard); tokenizer keeps acronyms/alphanumerics; first chunk of a frontmatter-first file no longer dropped; apostrophes kept in topics; --dry-run writes nothing; safety matrix derived from chunks; generated router performs real lexical retrieval; exit 1 when benchmark misses targets.

## [1.2.0] - 2026-09-25

### Changed
- Trusted-only indexing via the RAG pipeline's classify_trust(); one copy per chapter file (canonical rag_pipeline_output preferred, backup/audit/bundle copies skipped) to prevent duplicate chunks

## [1.1.0] - 2026-09-25

### Changed
- Claude audit fixes: fail-closed trusted-only indexing (no checkpoint, unreadable checkpoint, stage 6/8 incomplete or untrusted chapters excluded); --allow-unverified override; truncation warning

## [1.0.1] - 2026-09-25

### Changed
- Filter out unverified chapters and chapters with blocked or failed Stage 6/8 validation gates during Phase 2 catalog and inverted index compilation

## [1.0.0] - 2026-09-16

### Added
- Initial production release of `medical-index-rag-compiler`.
- 6-Phase autonomous pipeline compiling back-of-the-book index markdown and completed chapter RAG outputs into the 26-Asset Index Intelligence Suite.
- Phase 1: Lexicon & Registry ingestion (`*_synonyms_and_acronyms.json`, `landmark_clinical_trials_registry.json`, `index_concept_hierarchy.json`, `*_typographical_anchors.json`).
- Phase 2: Corpus Catalog & Inverted Index generator (`*_chunks_master_catalog.json`, `*_inverted_chunk_index.json`, `*_trial_to_chunks_map.json`, `*_synonym_to_chunks_map.json`).
- Phase 3: Clinical Knowledge Graphs & Guardrails (`*_concept_subtrees.json`, `*_index_directed_graph.json`, `*_polysemy_disambiguation.json`, `*_drug_disease_safety_matrix.json`, `*_early_exit_section_index.json`).
- Phase 4: Next-Gen Optimizers & Constrained Decoding (`*_canonical_semantic_cache.json`, `*_differential_comparators.json`, `*_clinical_cooccurrence_graph.json`, `*_entity_grammar.gbnf`, `*_entity_schema.json`, `*_index_salience_bm25_weights.json`).
- Phase 5: Automated 768-triplet benchmark test harness and scorecard generator (`eval_index_retrieval.py`, `BENCHMARK_SCORECARD.md`).
- Phase 6: Turnkey CDSS query router and navigator scaffold generator (`cdss_qa_router.py`).
- Full compliance with `version-manager` SemVer 2.0.0 guidelines and automated test suite.
