# Architecture Overview

## Pipeline A — Evidence / Case Corpus

1. evidence/source lock
2. independent source-structure/recommendation census
3. source-recommendation inventory
4. `SOURCE_INVENTORY_CERTIFICATION`
5. decision-node extraction
6. `SOURCE_EXTRACTION_COMPLETENESS`
7. extraction audit -> repair -> re-audit -> freeze
8. cross-source reconciliation + conflict/terminology register
9. candidate case generation
10. case source-fidelity audit
11. deduplication/overlap adjudication
12. downstream coverage audit including explanatory-only accounting
13. Master Case Library freeze
14. audience prioritization
15. teaching architecture / anchor paths
16. storyboard + case-to-slide mapping

## Pipeline B — Presentation / Artifact

1. slide-level specification
2. semantic source-binding QA + source hierarchy/footnote validation
3. prompt semantic QA
4. normalization/repair-fidelity QA
5. visual/source-figure register
6. speaker-note schema
7. PPTX build
8. clinical/provenance audit
8a. optional VISUAL_POLISH (content-locked restyle) + `VISUAL_POLISH_CONTENT_LOCK`
9. automated structural/mechanical preflight
10. full render
11. 100% visual/projector/UI review ledger
12. repair
13. full rerender + preflight + 100% re-review
14. independent visual QA or explicit policy-governed waiver
15. canonical promotion decision
16. derivatives / advanced / reference products from frozen corpus
17. modular indexing
18. closure manifest/archive

The two pipelines intersect through frozen identifiers and provenance, not by rewriting clinical evidence during design work.
