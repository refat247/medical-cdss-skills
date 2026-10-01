# CDSS Downstream RAG Integration Guide (Davidson 25th Edition)

This guide provides technical specifications for Clinical Decision Support System (CDSS) engineers integrating the output of the Davidson RAG Pipeline (`{PREFIX}_RAG_Optimised.md`).

---

## 1. Schema Overview

Each emitted micro-chunk carries rich frontmatter designed for medical vector databases (Pinecone, Qdrant, Milvus, Elasticsearch, Weaviate):

```yaml
---
chunk_id: L2-042
chunk_level: 2
semantic_type: management_step
disease_focus: asthma
topic: Asthma — Emergency Stepwise Management
source_lines: "1120-1165"
contains_tables: true
contains_boxes: false
contains_figures: true
figure_assets: ["assets/figures/ch18_fig_04.png"]
figure_captions: ["Fig 18.4: Stepwise escalation protocol in acute severe asthma"]
is_clinical_algorithm: true
algorithm_type: stepwise_escalation
related_chunks: [L2-040, L2-041, L2-043]
coverage_status: complete
gap_note: ""
---
```

---

## 2. Recommended Hybrid Retrieval Pipeline

1. **Intent Extraction & Metadata Classifier**: Extracts disease entity ("asthma"), semantic type ("management_step"), and algorithm preference.
2. **Hybrid Search**: Dense Vector Search (Med-CPT / BGE-M3) + Sparse BM25 with hard metadata pre-filters on `disease_focus` and `semantic_type`.
3. **Context Injection**: Injects primary micro-chunk (<400 tokens) and traverses `related_chunks` as needed without broad whole-chapter dumping.

---

## 3. Decoupled Multi-Modal UI Architecture

Do **not** send raw image pixels to text LLMs during point-of-care inference. Instead:
1. The CDSS retrieves the textual chunk (`L2-042`).
2. The LLM generates the text recommendation in ~300ms using the exact verbatim textbook protocol.
3. The CDSS Frontend UI reads `figure_assets: ["assets/figures/ch18_fig_04.png"]` and `figure_captions` from metadata.
4. The CDSS renders the image in the clinician's right-hand sidebar for visual confirmation (ECG trace, rash photo, X-ray).

---

## 4. Executable Algorithm & Scoring System Routing

When `is_clinical_algorithm == true`:
* **`decision_tree`**: Feed conditional branch rules directly into deterministic clinical pathway engines.
* **`scoring_system`**: Parse point thresholds (e.g. CURB-65 score >= 3, Wells > 4) for automated EHR risk stratification calculators.
* **`stepwise_escalation`**: Map Step 1 -> Step 2 -> Step 3 lines of pharmacotherapy.

---

## 5. Line Provenance & Explainability

Use `source_lines` (e.g. `"1120-1165"`) to provide clickable citation badges in your CDSS UI:
- *"Source: Davidson's Principles and Practice of Medicine (25th Ed.), Chapter 18, Lines 1120–1165"*.
- Clinicians can expand the full original textbook paragraph with 1-click verification.
