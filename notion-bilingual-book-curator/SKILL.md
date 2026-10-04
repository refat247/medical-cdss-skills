---
name: notion-bilingual-book-curator
description: "Governed Notion-to-book workflow: locks finite source scope, audits/reconciles evidence, controls research authorization, curates bilingual English+Bengali manuscripts, routes production, verifies actual artifacts, repairs regressions, freezes publication artifacts, and closes immutable releases."
metadata:
  version: "1.2.0"
  status: "stable"
---

# Notion Bilingual Book Curator

## 1. Operating Contract

Use this skill for a source-preserving book workflow, especially when the source comes from Notion or another structured knowledge base and the final artifact must remain auditable.

The governed workflow is:

SOURCE SET LOCK
→ CONTENT AUDIT / BLOCKER LEDGER
→ CURRENT-vs-HISTORICAL RECONCILIATION
→ INTERNAL EVIDENCE CLOSURE
→ EXTERNAL RESEARCH AUTHORIZATION GATE (only when needed)
→ JARGON COVERAGE & READER ACCESS
→ BILINGUAL EXPLANATION
→ READABILITY STRUCTURE
→ HUMANIZER-STYLE FINISH
→ MANUSCRIPT QA
→ PRODUCTION ROUTE
→ ACTUAL-ARTIFACT VERIFICATION
→ ARTIFACT DIFF & REGRESSION CHECK
→ REPAIR-ONLY MICRO-PATCH
→ MODE E PUBLICATION FREEZE
→ RELEASE CLOSURE

Preserve truth before improving prose or appearance.
Do not silently add outside facts. Do not silently convert uncertain, historical, inferred, external, designed, or benchmark-required material into verified/current/local/validated truth.
When the user supplies a document/PDF, treat that file as the source for the requested task unless they explicitly ask for external verification or expansion.
When Notion is available and the user asks to use Notion, read the relevant live pages rather than relying only on remembered summaries.
A builder's repair report is evidence about what the builder claims it did. It is not proof that the exported artifact contains the repair.

State invariant:

SOURCE SNAPSHOT LOCKED ≠ MANUSCRIPT FROZEN ≠ PUBLICATION ARTIFACT FROZEN ≠ RELEASE PACKAGED / CANONICAL BASELINE RECORDED

PASS — FREEZE READY closes the publication-artifact gate. It does not by itself prove release packaging, hashing, archival, registry promotion, Git synchronization, installation, discoverability, or runtime activation.

Read `references/governed-production-orchestration.md` for the end-to-end state machine and transition rules.

## 2. Workflow Modes

Determine the mode from the request. If unclear but the task is still executable, choose the least-destructive mode.

### MODE A — SOURCE AUDIT
Use when the user asks what is wrong with the source material before book generation.

Audit:
- duplicate and overlapping content;
- source/export artifacts;
- current vs historical truth;
- evidence-state integrity;
- provenance;
- missing tables or attachments;
- contradictions;
- unresolved states;
- source hierarchy;
- jargon/accessibility;
- maintenance/freshness implications.

For a governed end-to-end build, also:
- enumerate the finite source set;
- preserve canonical source IDs/URLs;
- create/update the blocker ledger;
- classify each blocker by whether internal evidence is exhausted.

Output:
1. audit verdict;
2. material defects;
3. preserve/repair rules;
4. recommended next step.

### MODE B — MASTER BUILDER PROMPT
Use when the user wants a complete prompt for Genspark or another external document builder.

First audit the source sufficiently to understand the content and constraints.
Then compile one self-contained prompt that includes:
- source boundary;
- evidence-state rules;
- bilingual convention;
- content-audit rules;
- current-vs-historical rules;
- jargon/readability rules when relevant;
- Humanizer-style rules;
- typography/color rules if applicable;
- document architecture;
- table/export repair;
- navigation requirements;
- semantic-drift checks;
- deliverables;
- stop conditions;
- final QA.

Never tell an external builder that it executed a ChatGPT skill it does not have.

### MODE C — BOOK AUDIT
Use after a draft/final PDF or book is produced.

Audit both content and rendered-page usability.
Check:
- visual legibility;
- information density;
- scanability;
- line length;
- paragraph density;
- bilingual usability;
- jargon accessibility;
- duplicate/restarted blocks;
- section/page boundaries;
- running headers;
- TOC;
- links;
- PDF outline/bookmarks when inspectable;
- tables;
- SOURCE PARTIAL treatment;
- orphan/widow defects;
- mobile/tablet/desktop suitability;
- evidence hierarchy;
- narrative hierarchy.

When the pre-repair artifact is available, also run the artifact-diff and regression gate.

Give a readiness verdict:
- PASS;
- PASS WITH TARGETED REPAIR;
- FAIL — MATERIAL REPAIR REQUIRED.

Do not give a high-level "looks good" verdict without checking the actual exported file.

### MODE D — REPAIR-ONLY MICRO-PATCH
Use after a book audit identifies bounded defects.

Generate a surgical patch prompt that:
- names the exact defects;
- names exact headings/locations when known;
- explicitly protects all substantive content;
- authorizes only the listed edits;
- forbids new research and redesign;
- requires final artifact verification;
- requires a repair report.

Prefer a micro-patch over replaying the entire master prompt once the book is already structurally mature.

Patch granularity should normally ratchet smaller as the artifact matures:

MASTER BUILD
→ TARGETED REPAIR
→ MICRO-PATCH
→ FINAL MICRO-REPAIR
→ FREEZE

Do not broaden scope again unless a newly discovered material defect requires it.

### MODE E — FREEZE AUDIT
Use after the final repair pass.

This mode is binary and conservative.

Audit the actual exported artifact at minimum for:
- substantial duplicates/restarts;
- extraction/export artifacts;
- TOC completeness and link targets;
- bookmark correctness;
- section boundaries and running headers;
- orphan pages;
- font/Bengali rendering;
- source provenance;
- evidence-state preservation;
- semantic drift;
- unresolved SOURCE PARTIAL areas;
- regression of previously closed blockers;
- authorized-vs-unauthorized changes relative to the immediately previous artifact when available.

Do not accept the builder's freeze report as proof. Verify the artifact itself.

Final verdict exactly one of:

PASS — FREEZE READY
FAIL — FREEZE REPAIR REQUIRED

If FAIL, state only material blocking defects and provide the smallest repair action.

After PASS, do not silently equate publication freeze with release closure. If the user requested a governed release, continue to RELEASE CLOSURE as defined in `references/governed-production-orchestration.md`.

### MODE F — JARGON COVERAGE AUDIT
Use when the user asks whether a book explains its jargon, acronyms, technical vocabulary, or domain-specific terms sufficiently for the intended reader.

1. Inventory technical terms and acronyms actually used in the artifact.
2. Compare them against:
   - the book's local glossary;
   - the canonical external/Notion glossary when the user asks to use it and it is available.
3. Classify each candidate:
   - DEFINED LOCALLY;
   - READER-CRITICAL MISSING;
   - EXTERNAL-GLOSSARY ONLY;
   - NO LOCAL ENTRY NEEDED;
   - PROPER NAME / MODEL / PRODUCT — NOT A GLOSSARY HEADWORD;
   - ALIAS / GROUP WITH CANONICAL HEADWORD.
4. Prefer grouped headwords for aliases rather than duplicate definitions.
5. Produce the smallest reader-critical glossary expansion rather than importing an entire enterprise glossary.
6. When the user approves insertion, lock the glossary text before sending it to an external builder.
7. After production, verify the exact supplied entries and expected field counts in the actual exported PDF.

Read `references/jargon-coverage-audit.md` for the detailed method.

## 3. Source and Evidence Invariants

Apply these distinctions strictly:

SEARCHED ≠ READ
READ ≠ AUDITED
AUDITED ≠ REPAIRED
REPAIRED ≠ VERIFIED
OLD ≠ STALE
SIMILAR ≠ DUPLICATE
SUPERSEDED ≠ DELETE
DESIGNED ≠ IMPLEMENTED
IMPLEMENTED ≠ EXECUTED
EXECUTED ≠ BENCHMARKED
BENCHMARKED ≠ CLINICALLY VALIDATED
EXTERNAL BENCHMARK ≠ LOCAL BENCHMARK
LOCAL TECHNICAL BENCHMARK ≠ HUMAN CLINICAL VALIDATION
MODEL SHORTLIST ≠ MODEL SELECTION
MODEL SELECTION ≠ PRODUCTION APPROVAL
TOOL ACCEPTANCE ≠ VERIFIED RESULT
BUILDER CLAIMED FIXED ≠ VERIFIED FIXED
SOURCE HTML VERIFIED ≠ EXPORTED PDF VERIFIED
PATCH APPLIED IN SOURCE ≠ PATCH PRESENT IN EXPORTED ARTIFACT
EXPORTED FILE EXISTS ≠ CURRENT REVISION EXPORTED
PREVIOUSLY PASSED ≠ STILL PASSED AFTER A LATER REPAIR
ARTIFACT FROZEN ≠ ALL SOURCE CLAIMS REVALIDATED
SOURCE SET ENUMERATED ≠ SOURCE SET LOCKED
INTERNAL EVIDENCE EXHAUSTED ≠ EXTERNAL RESEARCH AUTHORIZED
CHAPTER DRAFTABLE ≠ CHAPTER EVIDENCE COMPLETE
MANUSCRIPT AUDITED ≠ PUBLICATION ARTIFACT VERIFIED
PUBLICATION ARTIFACT FROZEN ≠ RELEASE PACKAGED
RELEASE PACKAGED ≠ GIT-SYNCED
PACKAGE PRESENT ≠ RUNTIME ACTIVATED

Never strengthen an evidence state during editing.

For evidence-sensitive or clinical content, distinguish:
- general knowledge;
- external research;
- external benchmark results;
- project-local results;
- implementation state;
- physician/human validation;
- governance/regulatory conclusions.

## 4. Bilingual Convention

Default convention for this skill:

TECHNICAL IDENTITY = ENGLISH
CONCEPTUAL UNDERSTANDING = BENGALI
EVIDENCE/SOURCE WORDING = PRESERVE SOURCE FIDELITY

Keep in English:
- technical terminology;
- medical professional terminology where English is standard;
- model/software names;
- code;
- commands;
- paths;
- filenames;
- schema/property names;
- metrics;
- benchmark names;
- acronyms;
- status/evidence labels;
- official titles;
- exact quotations;
- exact numerical results;
- URLs.

Use Bengali mainly for:
- what a concept means;
- why it matters;
- how it works;
- failure interpretation;
- project/clinical implication;
- what the reader needs to understand.

Do not create line-by-line parallel translation.
Do not force technical English into Bengali-script transliteration.

For major teaching concepts, use when useful:

**সহজ অর্থ:**
**Why it matters:**
**Project / clinical mapping:**
**Evidence boundary:**
**আপনার যা বুঝতে হবে:**

Do not force this template on every paragraph.

Read `references/bilingual-convention.md` when performing a bilingual rewrite or audit.

## 5. Content Audit

Before major rewriting, classify repeated material as one of:

EXACT DUPLICATE
SEMANTIC DUPLICATE
OVERLAPPING CONTENT
HISTORICAL VERSION
SUPERSEDED VERSION
PARENT / GENERAL SOURCE
DISTINCT DESPITE SIMILARITY

Only remove true redundancy.

When later material contains a unique delta plus repeated baseline:
- preserve the unique delta;
- remove the repeated baseline;
- preserve chronology.

For current vs historical material, prefer:

**Historical state:** ...
**Current state:** ...
**What changed:** ...
**Impact:** ...

Use only when supported by the source.

Read `references/content-audit.md` for detailed audit rules.

## 6. SOURCE PARTIAL and Missing Material

Never invent unavailable tables, attachments, rows, values, quotations, or missing source text.

Standard compact forms:

SOURCE PARTIAL — source table unavailable in this compilation; no values reconstructed.

SOURCE PARTIAL — source continues beyond the reader/extraction cap; remainder unavailable in this compilation.

SOURCE PARTIAL — source attachment body is not readable in this compilation.

If the exact platform-specific cause is known and material, name it accurately. Otherwise use a neutral "reader/extraction cap".

Do not publish raw export artifacts such as:
- `[table]`;
- `[child_page]`;
- `[truncated]`;
- `page has more blocks`;
- orphan extraction numbering.

## 7. Humanizer-Style Editorial Pass

Humanization happens only after:
1. source structure is understood;
2. audit is complete enough;
3. duplicate/history/evidence issues are resolved;
4. bilingual explanation is in place.

Humanize only new or materially rewritten human-facing narrative.

May:
- remove robotic phrasing;
- reduce repetitive conclusions;
- shorten bloated sentences;
- improve paragraph rhythm;
- remove canned transitions;
- reduce excessive headings/bolding;
- make Bengali sound natural.

Must not change:
- facts;
- numbers;
- dates;
- URLs;
- evidence labels;
- uncertainty;
- warnings;
- clinical/regulatory implications;
- project decisions;
- benchmark interpretation.

Do not freely humanize raw evidence, quotations, code, logs, identifiers, tables, exact labels, or immutable source text.

Read `references/humanizer.md` when performing or auditing editorial polish.

## 8. Typography and Color

Use the user's audited system when the project requests it.

Default evidence-informed implementation:
- English/Latin body: Atkinson Hyperlegible Next, about 11.5 pt;
- Bengali companion: use one high-quality Bengali-capable typeface with full glyph coverage and embedding; if the source/design record already names one, preserve it;
- numeric-heavy tables: Inter around 10.5–11 pt when useful;
- light positive-polarity reading pages;
- very dark text;
- restrained teal/blue for information/navigation;
- green for verified/current/pass;
- amber for warning/inferred/benchmark-required/unresolved;
- red for danger/reject/do-not-use;
- gray for historical/superseded/provenance.

Color must never be the sole carrier of meaning.

Prefer roughly 60–75 characters per prose line when feasible.

Do not solve oversized tables by shrinking text first. Prefer:

simplify → restructure → split → landscape if needed → reduce type only as final controlled step.

Do not claim exact font sizes, fonts, or HEX values are medically proven optimal.

Read `references/typography-color.md` before generating a design specification.

## 9. Book Readability Standard

A good reference book should work in three layers:

10–15 seconds:
reader understands what the chapter is and why it matters.

2–5 minutes:
reader can extract the controlling decision/evidence boundary.

Deep reading:
reader can continue into preserved evidence and provenance.

For major chapters, prefer a concise orientation block:

**What this section covers**
**Current project relevance**
**Established (source-supported)**
**Not established / still untested**

Do not put long audit history before the current interpretation.

Add a Reading Routes page when a book is large enough that cover-to-cover reading is not the best use pattern.

Prefer real vertical lists for three or more independent items.

A technical book can be dense, but density should come from information, not from missing whitespace, inline list compression, or repeated boilerplate.

Read `references/book-readability-audit.md` for audit criteria and scoring guidance.

## 10. Actual-Artifact Verification and Regression Control

Builder/source reports are claims. Verification is performed against the exported artifact.

When an external builder claims a repair:
1. inspect the actual returned PDF/book;
2. verify the named change at the rendered-page level when visual layout matters;
3. verify extracted text when exact wording/counts matter;
4. verify PDF navigation objects separately from printed navigation when inspectable;
5. compare with the immediately previous artifact when available.

If the previous artifact is available, perform an artifact-diff gate:
- page count;
- changed pages;
- extracted-text differences;
- rendered-page differences;
- outline/bookmark changes when relevant;
- link/annotation changes when relevant.

Map every changed region to the authorized patch scope.

A later repair can regress an earlier pass. Recheck previously closed blockers at each final micro-repair and before freeze.

If tooling cannot support a requested diff dimension, state that limitation rather than assuming no change.

Read:
- `references/builder-verification.md`
- `references/artifact-diff-regression.md`

## 11. Production Route Boundary

After manuscript QA, select one explicit production route:
- DIRECT DOCX/PDF BUILD;
- EXTERNAL BUILDER;
- SPECIALIST BUILDER / DOWNSTREAM SKILL;
- DIRECT EDIT of an existing mature artifact.

A specialist builder such as `offline-study-guide` remains a separate execution skill. Do not merge its implementation contract into this curator.

Regardless of route:
- preserve the same evidence/source boundary;
- preserve the same frozen manuscript/build specification;
- treat builder reports as unverified until the actual artifact is inspected;
- compare repaired artifacts with the previous artifact when available;
- return to bounded repair rather than broad redesign once mature.

This skill may prepare instructions for Genspark or another external builder, but it must not claim that external builder executed:
- this skill;
- Humanizer;
- Notion Content Auditor;
- any other ChatGPT runtime.

Use language such as:
- "Apply the supplied audit rules";
- "Apply Humanizer-style editorial rules";
- "Perform a preservation-oriented content audit."

Do not say:
- "Humanizer skill passed";
- "Notion Content Auditor executed";

unless that runtime truly executed and evidence exists.

## 12. Prompt Compiler

When generating a builder prompt:
- make it self-contained;
- state the current input version/page count if known;
- state whether the task is a fresh build, repair-only pass, or freeze-candidate pass;
- authorize only needed changes;
- preserve source and semantic boundaries;
- require verification against the exported artifact rather than source HTML alone;
- require explicit final QA;
- require a repair/audit report.

Once the book is mature, never send a broad "improve readability" prompt. Compile a bounded micro-patch.

Read `references/prompt-compiler.md` for the prompt structure.

## 13. Governed Production Orchestration

For end-to-end work, use the state machine in `references/governed-production-orchestration.md`.

Minimum controls:
- lock the finite source set before substantive drafting;
- maintain a blocker ledger rather than rediscovering unresolved issues;
- exhaust authorized internal evidence before requesting outside research;
- never browse externally without explicit authorization when source-preserving mode applies;
- classify chapter/evidence-packet readiness before drafting;
- perform manuscript-level factual/bilingual/jargon/provenance QA before production;
- choose and record one production route;
- verify the actual artifact;
- ratchet repair scope smaller as maturity increases;
- run Mode E on the actual final artifact;
- if a governed release is requested, perform release closure after Mode E rather than treating Mode E as packaging proof.

Do not hard-code project-specific blocker names, chapter counts, drafting batch counts, or domain facts into the reusable workflow.

## 14. Freeze Gates

A freeze-ready book must pass all applicable gates:

CONTENT
- no known substantial duplicate restart;
- no unsupported substantive additions;
- evidence states preserved;
- current/historical states distinguishable;
- provenance intact.

BILINGUAL
- technical identity remains English;
- Bengali is explanation/reasoning;
- no mechanical parallel translation;
- no unnecessary technical transliteration.

PRODUCTION
- no raw export artifacts;
- no broken glyphs;
- no clipping/overlap;
- no severe orphan page;
- correct section headers;
- readable tables.

NAVIGATION
- TOC complete;
- TOC targets correct;
- bookmark tree correct when required;
- source links usable;
- appendices findable.

REGRESSION
- previously closed blockers remain closed;
- only authorized changes occurred since the previous artifact when a comparison artifact is available;
- the builder report matches the actual exported artifact.

SAFETY / EVIDENCE
- benchmark is not represented as clinical validation;
- shortlist is not represented as approval;
- unresolved and SOURCE PARTIAL states remain visible.

Freeze semantics:

`PASS — FREEZE READY` means the publication artifact is editorially/structurally closed at the stated evidence snapshot. It does not mean every historical/source claim has been newly revalidated, and it does not mean release packaging is complete.

Read `references/freeze-gates.md` for the final binary audit.

## 15. Release Closure

Run release closure only when the user requested a governed/canonical release.

Record, when applicable:
- canonical artifact names and version;
- evidence/source snapshot date;
- artifact hashes or manifest;
- release/package identity;
- immutable baseline rule;
- derivative labeling rule;
- next-version rule for future substantive changes;
- distribution surfaces actually synchronized;
- surfaces not synchronized;
- runtime activation state separately from package correctness.

Never claim:
- Git sync without verifying Git;
- Notion registry promotion without verifying Notion;
- installation/discoverability without evidence;
- native runtime activation from package presence.

Release closure does not change the Mode E wording. Mode E remains:

PASS — FREEZE READY
or
FAIL — FREEZE REPAIR REQUIRED

## 16. Manual Protocol Loading

Native personal-Skill activation may be unavailable or unreliable.

`MANUAL_ACTIVATION.md` is a first-class release file.

Manual execution pattern:

PROJECT/CONVERSATION FILES
→ READ COMPLETE SKILL.md
→ READ ONLY PHASE-RELEVANT REFERENCES
→ REPORT MANUAL LOAD STATUS
→ EXECUTE TASK
→ RE-READ GOVERNING REFERENCE AT MAJOR PHASE TRANSITIONS

Status language:

MANUAL PROTOCOL LOADED — native runtime not claimed

Do not infer runtime activation from:
- installation;
- package visibility;
- on-disk presence;
- prior-chat success;
- correct-looking output.

## 17. Output Discipline

When auditing:
- lead with the verdict;
- separate material blockers from optional polish;
- cite exact file/page evidence when available;
- do not overproduce recommendations once the next action is obvious.

When producing a repair prompt:
- return one copy/paste-ready prompt;
- include exact protected content boundaries;
- include exact repair targets;
- include final artifact QA;
- include regression recheck;
- avoid generic redesign instructions.

When producing a jargon patch:
- return the locked glossary insertion text separately from the builder instructions;
- count grouped headwords;
- define expected field counts when possible;
- verify those counts in the final artifact.

When producing a freeze audit:
- do not score cosmetically;
- use PASS/FAIL;
- if FAIL, provide the smallest next corrective action.

For governed end-to-end execution:
- keep a concise transition log;
- keep the blocker ledger current;
- distinguish phase completion from final release closure.

## 18. Clinical / Evidence-Sensitive Mode

When the book is medical, clinical, regulatory, or otherwise high-stakes:
- preserve source wording for safety-critical facts;
- never convert technical readiness into clinical readiness;
- never convert external leaderboard scores into clinical approval;
- never convert benchmark performance into prospective clinical validation;
- keep physician/human adjudication distinct;
- keep regulatory interpretation distinct from written regulator determination;
- preserve exact numbers, dose/unit notation, dates, and citations.

## 19. Do Not Do

Do not:
- rebuild a mature book from scratch when a surgical patch will suffice;
- silently browse the web and update a source-preserving book;
- remove history just because it is old;
- invent missing tables;
- accept a builder report without checking the actual exported artifact when the file is available;
- treat source-HTML verification as exported-PDF verification;
- assume an earlier repair remains fixed after a later edit;
- claim a tool/skill/runtime executed when it did not;
- call a document FINAL/FROZEN while material production defects remain;
- imply artifact freeze revalidated all historical evidence;
- imply Mode E PASS proves release packaging;
- imply release packaging proves Git/registry/runtime synchronization;
- optimize for page count at the expense of readability or evidence fidelity.

## 20. Package Maintenance

For release/version decisions, read `references/package-maintenance.md`.

The canonical package version is `metadata.version` in this `SKILL.md`.
Mirror the same version in `agents/openai.yaml` and record every release in `CHANGELOG.md`.
