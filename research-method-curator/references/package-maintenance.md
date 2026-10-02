# Package Maintenance

Use this reference only when releasing, installing, repairing, or smoke-testing Research Method Curator.

## Version policy

Use semantic versioning:
- `PATCH` for compatible wording corrections, metadata repair, documentation fixes, and safe finishing-layer additions that do not change evidence decisions.
- `MINOR` for backward-compatible new workflows, evidence gates, or supported research modes.
- `MAJOR` for incompatible instruction changes, removed guarantees, or a materially different operating model.

The version in `SKILL.md` is canonical. Mirror the same value in `agents/openai.yaml` and record every release in `CHANGELOG.md`.

## Required release files

- `SKILL.md`
- `README.md`
- `CHANGELOG.md`
- `references/timestamped-discovery-evidence-archive.md`
- `references/package-maintenance.md`
- `agents/openai.yaml`
- `assets/icon.svg`

## Read-only smoke test

1. Load the skill by the name `research-method-curator`.
2. Confirm the complete `SKILL.md` is readable.
3. Parse YAML frontmatter and `agents/openai.yaml` without errors.
4. Confirm both files declare the same version and stable status where applicable.
5. Confirm every required release file exists and is non-empty.
6. Confirm the default prompt explicitly names `$research-method-curator`.
7. Confirm the timestamped evidence archive reference remains available.
8. Confirm the Humanizer finishing-pass boundary is present.
9. Report discovery, version, validation, and file coverage separately; do not infer one from another.
