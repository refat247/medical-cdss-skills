# Hard-Won Rules Reference (Davidson RAG Pipeline)

The following rules were established across production runs of Chapters 01, 02, 03, 05, 07, 08, 09, 10, 11, 12, 14, 16, and 31. Every rule represents a hard-fought fix to a real failure mode observed in production.

---

### Rule A — Piracy guard must use is_clinical(), not line length
`len > 120` incorrectly removes MCQ answer options (A./B./C.) and answer lines. Always use `pipeline/stages/stage_2_repair.py`'s `is_clinical()` (v2.6.4). Protects decimal-numbered MCQ stems (`5.1.`, `5.1.2.`) and dash-prefixed options (`- A.`, `- A)`), extending protection to the whole paragraph containing a protected line.

### Rule B — Curly-quote count is NOT used in Stage 4.5
Chunk headers repeat "Davidson's" N times, inflating chunk count vs source. The verbatim body-text check is the correct and sufficient signal.

### Rule C — Stage 4.5 is always exhaustive (all L2 chunks, no sample cap)
A 10-sample gate missed systematic curly-quote flattening across 49/66 chunks in Ch01. On chapters with >200 L2 chunks, never skip the full check on first failure.

### Rule D — Verbatim failures: splice-fix, never re-run subagent
Re-running Stage 4 risks introducing new defects. For failed chunks: locate the text in `REPAIRED_S2.md` and overwrite the chunk body directly.

### Rule E — SKEW_THRESHOLD = 60 for pharmacology chapters, 40 for others
Set `SKEW_THRESHOLD` in Stage 4.6. Pharmacology/cardiology/infectious = 60. Clinical reasoning/anatomy/physiology = 40.

### Rule F — SOURCE_PATH is never modified. Always safe to re-read for splice repairs
If piracy removal sweeps up clinical content: source file is intact, splice back from it.

### Rule G — L1 semantic_type is advisory; RAG_Optimised.md only ever uses L2
L1 macro chunks are hierarchical/overlapping by design (a full `##` section including its nested `###` subsections). Stage 5 only emits L2 chunks into `RAG_Optimised.md`. Default Stage 4.6 verification to `levels=(2,)`.

### Rule H — Back-matter is not clinical content
No semantic_type in the 7-type taxonomy fits reference lists. Stage 4B excludes "Journal articles" / "Websites" / "Patient organisations" / "Further information" sections from chunk emission entirely.

### Rule I — Sibling type-bleed is the #1 semantic-tagging failure mode
A chunk sitting near another chunk with a strong-signal type tends to inherit that type regardless of its own content. Always classify a chunk from its own body text; title-based signals (`TITLE_RULES` in `pipeline/stage_4_6_gemini_verification.py`) take priority over body-keyword matching.

### Rule J — Flat-`##` sections without `###` children are NOT optional to chunk
Confirmed on a real chapter run: 263/312 `##` sections had no `###` child, and every one was silently absent from `RAG_Optimised.md` (~71% of content). Stage 4B's flat-`##` fallback (one L2 chunk per orphan `##` section) exists specifically to close this gap.

### Rule J2 — Per-`####` chunking when a `##` section has only `####` subheadings (Rule J3 Manifest)
When a section has no `###` headers but multiple `####` subsections, emit one L2 chunk per `####` subsection.

### Rule K — `disease_focus` and Stage 4.7's disease/ruleset maps are curated per chapter
There is no reliable automatic way to build `DISEASES_<CH>` or `SUSPECTED_GAP_RULESET_<CH>` without an editorial judgment call. Budget ~15 min per chapter before running Stage 4.7.

### Rule L — Tier 2 synthesis (5.2) and Tier 3 gap stubs (5.3) require verification
Not every `SCATTERED` entry names a real disease. `SUSPECTED_GAP` entries must be confirmed genuinely absent via grep pass + human confirmation before a stub is written.

### Rule M — Stage 4.7 category inference needs semantic_type fallback for all 5 categories
`infer_categories()` maps `pathophysiology` -> `causes`, `diagnostic_criteria` -> `causes`, and `drug_info` -> `complication_or_safety`.

### Rule N — Cluster Stage 4.7's disease groups on `disease_focus`, not topic
Topic-string matching undercounts generic sub-chunks. Cluster on `disease_focus` assigned in Stage 4B.

### Rule O — `infer_categories()` needs body-text scan tier
Flowing single-paragraph disease overviews cover 3-4 categories in one chunk. Scanning body text prevents false-positive gap flags.

### Rule P — Parent disease slug inheritance in Stage 4B
Automatically bind child subsections (`###`, `####`) to their enclosing `##` parent disease entity slug, preventing generic slug pollution (`investigations`, `management`).

### Rule Q — Intro prose before first subsection is chunked as an Overview L2 chunk
Introductory text in a `##` section before the first `###` header must be emitted as an L2 chunk (`{Section} — Overview`) to prevent silent omission of pathogenesis/intro text.

### Rule R — Decoupled Figure Asset Invariant (Zero Raw Pixels in RAG)
Never embed raw base64 or pixel blobs directly into text chunks or vector embeddings. All figures must be referenced via structured `figure_assets: ["assets/figures/..."]` and `figure_captions` metadata in chunk YAML frontmatter, with high-resolution image files stored in a decoupled asset directory/CDN. 100% of the diagnostic criteria and findings must be transcribed into the chunk text so the AI can reason over it without vision token overhead.

### Rule S — Clinical Algorithm & Scoring System Classification
Any chunk containing conditional decision logic ($IF \to THEN$), clinical scoring thresholds (e.g. CURB-65, Wells, CHA2DS2-VASc, MELD), or stepwise escalation protocols (Step 1 $\to$ Step 2) must be flagged with `is_clinical_algorithm: true` and classified into `algorithm_type: "decision_tree" | "scoring_system" | "stepwise_escalation"` for direct integration into CDSS decision engines. Enforced via Stage 6 Invariant 6.5.

### Rule T — Read-Back Invariant on File Mutations
After performing any text splice (Rule D/F), manual correction, or metadata remap to a live artifact (`chunks.md`, `REPAIRED_S2.md`, `_CHECKPOINT.json`), the agent must re-open and read back the target file directly from disk to verify the mutation landed before proceeding to downstream automated chaining (`--stage auto`). Never trust stdout summaries or in-memory state.

### Rule U — Golden Proof & Wording Disciplines
1. Never present an intended write as a completed write.
2. Never present stdout terminal text as proof of saved disk state (always verify the physical output file).
3. Never treat a structural pass (e.g. Stage 6) as proof of clinical/semantic correctness.
4. Never hide unresolved findings or candidates behind a final PASS headline.

### Rule V — Stop Point & No-Silent-Advance Control
When hitting interactive candidate triage (`pending_manual` in Stage 4.5d, Stage 4.6, or Stage 4.7 editorial curation), never guess, simulate, or fabricate adjudication decisions to bypass pauses. Always present the candidate batch to the operator for explicit confirmation.

