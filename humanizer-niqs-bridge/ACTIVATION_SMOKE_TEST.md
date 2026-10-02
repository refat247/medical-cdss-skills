# Activation Smoke Test — Humanizer NIQS Bridge v1.0.0

## Purpose

Verify fresh-session loading without inferring activation from Git, Notion, ZIP presence, filesystem visibility, or previous chats.

## Fresh-chat prompt

@humanizer-niqs-bridge fresh runtime activation test.

Read-only only. Do not modify anything.

Use ONLY instructions already injected into this fresh conversation by the selected Skill/runtime.

Do NOT inspect:
- filesystem skill directories
- SKILL.md on disk
- README
- CHANGELOG
- agents/openai.yaml
- ZIP files
- Git
- Notion
- previous chats
- installed-package discovery

If the skill is loaded, report:
- internal skill name
- loaded package version
- exact loaded title/header
- upstream Humanizer baseline
- NIQS overlay version
- whether the instructions explicitly state that native Humanizer runtime activation is a separate state

Expected:
- internal name: `humanizer-niqs-bridge`
- package version: `1.0.0`
- title/header: `Humanizer NIQS Bridge`
- upstream baseline: `blader/humanizer v3.1.0`
- NIQS overlay: `v1.0.0`

Final verdict exactly one of:

PASS — humanizer-niqs-bridge v1.0.0 activated

or

FAIL — humanizer-niqs-bridge runtime did not activate as declared
