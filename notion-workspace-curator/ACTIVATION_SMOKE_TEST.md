# Activation Smoke Test — Notion Workspace Curator v0.5.0

## Purpose
Fresh-session runtime activation test for the NIQS release. This test must not infer activation from Git, Notion, installation visibility, filesystem presence, or previous chats.

## Fresh-chat prompt

@notion-workspace-curator fresh runtime activation test.

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
- internal name: `notion-workspace-curator`
- version: `0.5.0`
- title/header: `Notion Workspace Curator`
- NIQS v1.0 present in loaded instructions

Final verdict exactly one of:

PASS — notion-workspace-curator v0.5.0 activated with NIQS v1.0

or

FAIL — notion-workspace-curator v0.5.0 runtime did not activate as declared

## Evidence rule
PASS requires runtime-injected instructions in the fresh chat. Package visibility, Git, Notion mirrors, or on-disk files are not sufficient.
