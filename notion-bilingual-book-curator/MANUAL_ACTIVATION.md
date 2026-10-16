# Manual Activation Protocol — Notion Bilingual Book Curator v1.2.1

## Purpose

Use this when native personal-Skill runtime activation is unavailable or unreliable.

This is **manual protocol loading**, not native runtime Skill activation.

## Canonical source files

Primary operating instructions:
- `SKILL.md`

Supporting references:
- `references/bilingual-convention.md`
- `references/content-audit.md`
- `references/humanizer.md`
- `references/typography-color.md`
- `references/book-readability-audit.md`
- `references/prompt-compiler.md`
- `references/freeze-gates.md`
- `references/output-templates.md`
- `references/jargon-coverage-audit.md`
- `references/builder-verification.md`
- `references/artifact-diff-regression.md`
- `references/package-maintenance.md`
- `references/governed-production-orchestration.md`

## Fresh-chat bootstrap prompt

MANUAL PROTOCOL LOAD — `notion-bilingual-book-curator` v1.2.1

Native personal-Skill runtime activation is currently unavailable or unreliable. Do NOT infer or claim native Skill activation.

Before doing the task:

1. Read the complete file `SKILL.md` from the Project/conversation files.
2. Read only the supporting reference files relevant to the requested task.
3. Treat those files as the operating protocol for this chat.
4. Follow their workflow, evidence-state rules, bilingual convention, builder-verification rules, regression gates, repair-only rules, and freeze gates faithfully.
5. Do not use memory as a substitute for unread protocol text.
6. If a required protocol file is unavailable, say exactly which file is unavailable before proceeding.
7. Distinguish:
   - NATIVE SKILL RUNTIME: NOT VERIFIED
   - MANUAL PROTOCOL LOAD: YES/NO
8. After loading, report only:

MANUAL LOAD — notion-bilingual-book-curator v1.2.1
Primary protocol: SKILL.md
Relevant references loaded: <list>
Native runtime activation: NOT CLAIMED

Then perform the user's task.

## Task-specific loaders

### END-TO-END governed production / release closure

Read:
- `SKILL.md`
- `references/governed-production-orchestration.md`
- then only the phase-specific references required by the current state.

At every major phase transition, re-read the governing reference for the next phase. Do not infer end-to-end execution as permission for external research. After Mode E PASS, run release closure only when a canonical release is requested.

### MODE A — Source/content audit

Read:
- `SKILL.md`
- `references/content-audit.md`
- `references/bilingual-convention.md`
- `references/humanizer.md` only when editorial polish is part of the task.

### MODE B — Complete external-builder prompt

Read:
- `SKILL.md`
- `references/content-audit.md`
- `references/bilingual-convention.md`
- `references/humanizer.md`
- `references/typography-color.md`
- `references/prompt-compiler.md`
- `references/builder-verification.md`

### MODE C — Book/PDF readability audit

Read:
- `SKILL.md`
- `references/book-readability-audit.md`
- `references/content-audit.md`
- `references/typography-color.md`
- `references/bilingual-convention.md`
- `references/builder-verification.md`
- `references/artifact-diff-regression.md` when a previous artifact exists.

### MODE D — Repair-only prompt

Read:
- `SKILL.md`
- `references/content-audit.md`
- `references/prompt-compiler.md`
- `references/book-readability-audit.md`
- `references/builder-verification.md`
- `references/artifact-diff-regression.md`
- `references/freeze-gates.md`

### MODE E — Final freeze audit

Read:
- `SKILL.md`
- `references/freeze-gates.md`
- `references/content-audit.md`
- `references/book-readability-audit.md`
- `references/bilingual-convention.md`
- `references/builder-verification.md`
- `references/artifact-diff-regression.md`

Final verdict must be exactly:

PASS — FREEZE READY

or

FAIL — FREEZE REPAIR REQUIRED

### MODE F — Jargon coverage audit

Read:
- `SKILL.md`
- `references/jargon-coverage-audit.md`
- `references/bilingual-convention.md`
- `references/content-audit.md`
- `references/prompt-compiler.md` if a glossary patch will be generated.
- `references/builder-verification.md` and `references/artifact-diff-regression.md` for post-build verification.

## Integrity rules

Manual loading is valid only when the model actually reads the protocol files in that chat.

Installed/visible/on-disk ≠ loaded.

A prior chat's successful manual load does not prove the current chat has loaded the protocol.

Builder report ≠ exported-artifact verification.

A previously passed defect must be rechecked after later repairs when freeze readiness depends on it.

## Recommended status language

Use:

`MANUAL PROTOCOL LOADED — native runtime not claimed`

Do not use:

`Skill activated`

unless native runtime injection is independently verified.
