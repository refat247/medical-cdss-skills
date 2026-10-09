# Activation Smoke Test — Notion Bilingual Book Curator v1.2.1

## Purpose

Fresh-session runtime activation test. Do not infer activation from file presence, Git, Notion, ZIP visibility, previous chats, or installed-package discovery.

## Fresh-chat prompt

@notion-bilingual-book-curator fresh runtime activation test.

Read-only only. Do not modify anything.

Do NOT inspect:
- filesystem skill directories
- SKILL.md on disk
- agents/openai.yaml on disk
- README
- CHANGELOG
- ZIP files
- Git
- Notion
- previous chats
- installed-package discovery

Use ONLY instructions already injected into this fresh conversation by the selected Skill/runtime.

If the skill is actually loaded, report:
- internal skill name
- loaded version
- loaded status
- exact loaded title/header
- the first operational heading immediately after the title
- whether MODE F — JARGON COVERAGE AUDIT is present
- whether `2A. Governed End-to-End Production State Machine` is present
- whether the instructions distinguish `PASS — FREEZE READY` from release packaging/canonical-baseline recording
- the three core language roles in the bilingual convention
- whether the instructions explicitly say BUILDER CLAIMED FIXED ≠ VERIFIED FIXED

Expected:
- internal name: `notion-bilingual-book-curator`
- version: `1.2.1`
- status: `stable`
- title/header: `Notion Bilingual Book Curator`
- first operational heading: `1. Operating Contract`
- MODE F present
- governed end-to-end production state machine present
- publication freeze explicitly distinguished from release closure
- bilingual roles: technical identity = English; conceptual understanding = Bengali; evidence/source wording = preserve source fidelity
- builder-verification invariant present

Final verdict exactly one of:

PASS — notion-bilingual-book-curator v1.2.1 activated

or

FAIL — notion-bilingual-book-curator runtime did not activate as declared
