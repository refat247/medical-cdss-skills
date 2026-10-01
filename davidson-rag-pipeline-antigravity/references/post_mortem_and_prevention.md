# Post-Mortem & Permanent Prevention Strategy Reference

## 1. Forensic Catalogue of Mistakes & Resolutions

1. **Premature Completion Claims**: In Chapter 10, completion was claimed before running mandatory Stage 6 validation. **Resolution**: All 8 post-conditions must pass before declaring completion.
2. **Silent Stage Omission**: Skipping Stage 4.5c/4.5d under assumption that code didn't fail. **Resolution**: Monotonic checkpoint gates enforce strict ordering.
3. **Subagent Prompt Token Exhaustion & Quote Flattening**: Subagents emitting 5,000+ line chunks truncated sections and converted curly quotes to straight quotes. **Resolution**: Stage 4B Deterministic Hybrid Slicer Engine parses byte-for-byte in Python.
4. **Adjudication Desynchronization**: Editing JSON without re-rendering markdown left audit reports reporting unresolved errors. **Resolution**: Stage 8 Dual-Format Precision Synchronizer atomically updates JSON and Markdown.
5. **Disposition Dropping**: Omitting the disposition rationale table when 0 candidates were synthesized. **Resolution**: Stage 5.2 Mandatory Disposition Hook appends rationale table unconditionally.
6. **F-String Syntax Crashes**: Backslashes inside f-string expressions failed on Python < 3.12. **Resolution**: Stage 1 standalone variable pre-calculation.
7. **Missing Review Evidence**: Omitting chunks_reviewed in checkpoint tripped finalizer gates. **Resolution**: Stage 4.6 explicit review count persistence.

## 2. Permanent Prevention Architecture

- **Tier 1 (Execution)**: Byte-level physical slicing in Stage 4B eliminates hallucination, omission, and typographic loss.
- **Tier 2 (Verification)**: Full-scope Gemini 3.7 Flash High semantic classification with in-session human review.
- **Tier 3 (Completeness)**: Persistent disposition tables in `CompletenessChecklist.md` resolve all scattered clusters.
- **Tier 4 (Certification)**: Fail-closed finalization seals artifacts with cryptographic SHA-256 hashes in `CORPUS_OUTPUT_PROTECTED.json`.

---

## 3. Operational Proof & Wording Disciplines (Rule U)

1. **Intended vs Completed**: Never present an intended write as a completed write.
2. **Stdout vs Disk State**: Never present stdout terminal text as proof of saved disk state; inspect the generated `.md` and `.json` files.
3. **Structural vs Semantic**: Never treat a structural pass (e.g. Stage 6) as proof of clinical or semantic correctness.
4. **Transparency**: Never hide unresolved findings or candidates behind a final `PASS` headline.
5. **Read-Back Invariant (Rule T)**: After any live-file mutation or splice repair, re-open and inspect the target file from disk before triggering downstream stages.

---

## 4. Interactive Stop Point & No-Silent-Advance Architecture (Rule V)

When automated pipeline chaining (`--stage auto`) encounters an interactive candidate gate:
- **Stage 4.5d (`pending_manual`)**: Pause immediately and output the candidates requiring triage.
- **Stage 4.6 (`pending_manual`)**: Present flagged chunks for classification review.
- **Stage 4.7 Editorial Curation**: Require explicit textbook-grounded disease list basis; never invent regex heuristics or guess singleton gaps.
- **No-Silent-Advance**: The assistant must never simulate or fabricate user decisions to keep the pipeline moving without explicit approval.

