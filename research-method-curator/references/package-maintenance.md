# Package Maintenance
Use this reference only when releasing, installing, repairing, or smoke-testing Research Method Curator.
## Version policy
Use semantic versioning:
- `PATCH` for compatible wording corrections, metadata repair, and documentation fixes that do not materially change decisions.
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
4. Confirm both files declare the same version and stable status.
5. Confirm every required release file exists and is non-empty.
6. Confirm the default prompt explicitly names `$research-method-curator`.
7. Confirm the timestamped evidence archive reference remains available.
8. Run the Skill Creator `quick_validate.py` validator.
9. Report discovery, version, validation, and file coverage separately; do not infer one from another.
## Release procedure
1. Read the current package and Git status.
2. Preserve unrelated working-tree changes.
3. Fetch upstream and reconcile any newer canonical release before choosing a version.
4. Make the smallest compatible update.
5. Update both version declarations and the changelog.
6. Run the read-only smoke test and inspect the diff.
7. Commit only this package with a descriptive message.
8. Push or synchronize the commit through the configured skills Git remote.
9. Re-read the remote commit and verify that it contains only intended paths.
Recommended commit form:
```plain text
<type>(research-method-curator): <imperative summary>
```
Use `fix` for instruction defects, `feat` for compatible new capability, and `chore` for packaging-only releases.
