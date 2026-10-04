# External Builder Prompt Compiler

Use this structure for Genspark or another document builder.

## 1. Role and Input

State:
- exact input artifact/version/page count if known;
- whether source is Notion-derived;
- whether this is a fresh build, repair pass, glossary patch, or freeze-candidate pass.

## 2. Source Boundary

Explicitly forbid:
- new external research unless authorized;
- invented missing content;
- silent factual updates;
- evidence-state strengthening.

## 3. Audit Rules

Include duplicate classification, current-vs-historical reconciliation, SOURCE PARTIAL behavior, provenance, and jargon coverage when applicable.

## 4. Bilingual Rules

Technical English / Bengali explanation / evidence fidelity.

## 5. Humanizer Rules

Only narrative prose; semantic-drift check required.

## 6. Design Rules

Typography, colors, line measure, tables, callouts, font embedding.

## 7. Book Architecture

Front matter, parts/chapters, appendices, reading routes, glossary, source registry as needed.

## 8. Navigation

TOC, internal links, PDF outline/bookmarks, section starts, running headers.

## 9. Repair-Only Constraint

For mature books:
- name exact defect;
- name exact location/heading;
- authorize only listed edits;
- forbid broad rewriting/redesign;
- require a repair report;
- require verification against the exported artifact, not source HTML alone.

Patch scope should normally shrink with each late-stage pass.

## 10. Jargon Patch

When inserting a glossary expansion:
- lock exact supplied definitions;
- name exact insertion boundary;
- give exact grouped-headword count;
- give expected field counts when useful;
- prohibit additional invented headwords;
- allow page count to grow naturally.

## 11. Final QA

Require:
- duplicate scan;
- semantic-drift scan;
- rendered-page inspection;
- glyph/font check;
- link/bookmark test;
- source/provenance preservation;
- regression recheck of previously closed blockers.

## External Runtime Honesty

Never instruct the builder to claim it executed ChatGPT skills. Say "apply the supplied rules".
