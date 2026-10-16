# Activation Smoke Test — Notion Content Auditor v1.5.0

## Purpose
Fresh-session runtime activation test for the current release. This test must not infer activation from package visibility, Git, Notion, filesystem state, or prior conversations.

## Fresh-chat prompt

@notion-content-auditor fresh runtime activation test.

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
- exact loaded title/header
- the first operational heading or sentence after the title
- whether the loaded instructions explicitly reference NIQS v1.0 / Notion Information Quality Standard

Expected:
- internal name: `notion-content-auditor`
- version: `1.5.0`
- title/header: `Notion Content Auditor`
- NIQS v1.0 present in loaded instructions

Final verdict exactly one of:

PASS — notion-content-auditor v1.5.0 activated with NIQS v1.0

or

FAIL — notion-content-auditor v1.5.0 runtime did not activate as declared

## Evidence rule
PASS requires runtime-injected instructions in the fresh chat. Package/Git/Notion state remains separate from runtime activation.
