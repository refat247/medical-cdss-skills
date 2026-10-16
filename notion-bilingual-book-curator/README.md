# Notion Bilingual Book Curator

**Version:** 1.2.1  
**Status:** stable  
**Internal skill name:** `notion-bilingual-book-curator`

A reusable workflow for turning Notion-derived or other source-backed material into an evidence-preserving bilingual technical reference book, then auditing the exported artifact through final freeze readiness.

## Core workflow

Source-set lock → source/content audit → blocker ledger → current-vs-historical reconciliation → jargon coverage → bilingual explanation → readability structure → evidence-packet/drafting gate → manuscript QA → production route → actual-artifact verification → artifact diff/regression → bounded repair → Mode E publication freeze → release closure.

## v1.2.0 additions

- governed end-to-end source-to-release state machine
- finite source-set lock with canonical ID/URL preservation
- persistent blocker ledger with closure and regression states
- internal-evidence exhaustion / external-research authorization gate
- evidence-packet and chapter drafting eligibility states
- production-route abstraction: direct build, external builder, or specialist builder
- explicit publication-freeze vs release-closure lifecycle states
- canonical artifact identity, hash/manifest, immutability, derivative, and next-version rules when a release is requested
- `references/governed-production-orchestration.md`

All v1.1.0 jargon, builder-verification, artifact-diff/regression, manual-loading, and freeze controls remain in force.

## What it does not do

- It does not make Genspark or another external builder "run" ChatGPT skills.
- It does not add external facts unless the user explicitly asks for verification/research.
- It does not treat external benchmark performance as project-local or clinical validation.
- It does not invent unavailable tables, source text, attachments, or evidence.
- It does not accept a builder repair/freeze report as proof when the exported artifact is available.

## Manual fallback

When native personal-Skill runtime activation is unavailable, use `MANUAL_ACTIVATION.md`.

Required status language:

`MANUAL PROTOCOL LOADED — native runtime not claimed`

## Recommended use

Examples:

- "Use the Bilingual Book Curator to audit this Notion-derived PDF."
- "Create the complete builder prompt for this source package."
- "Run a jargon coverage audit and produce the locked Appendix glossary patch."
- "Audit the regenerated book and give only the repair micro-patch."
- "Run the final freeze audit and compare it with the previous PDF."

## v1.2.1 reference HTML clarification

Clarify the existing bilingual/readability and specialist-builder route for top-down offline HTML. No new mode or orchestrator is introduced. Load both skills explicitly for combined work; preserve English technical/source identity and place concise Bengali explanation underneath. Browser QA and clinical validation are separate from static/package checks.
