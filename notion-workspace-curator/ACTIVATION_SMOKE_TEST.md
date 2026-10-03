# Activation Smoke Test — Notion Workspace Curator v0.6.0

## Purpose
Fresh-session runtime activation test for the NIQS v1.0 + artifact-routing release. This test must not infer activation from Git, Notion, installation visibility, filesystem presence, or previous chats.

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
- whether the loaded instructions contain the artifact-routing chain `DOMAIN / OWNERSHIP → NIQS PAGE ROLE → ARTIFACT FORM → CANONICAL HOME`
- whether the loaded instructions require extending an existing canonical router before creating a competing routing surface when safe

Expected:
- internal name: `notion-workspace-curator`
- version: `0.6.0`
- title/header: `Notion Workspace Curator`
- NIQS v1.0 present in loaded instructions
- artifact-routing chain present
- existing-router-first guardrail present

Final verdict exactly one of:

PASS — notion-workspace-curator v0.6.0 activated with NIQS v1.0 + artifact routing

or

FAIL — notion-workspace-curator v0.6.0 runtime did not activate as declared

## Evidence rule
PASS requires runtime-injected instructions in the fresh chat. Package visibility, Git, Notion mirrors, or on-disk files are not sufficient.
