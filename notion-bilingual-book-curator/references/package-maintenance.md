# Package Maintenance

Use this reference only when releasing, installing, repairing, or smoke-testing Notion Bilingual Book Curator.

## Version policy

Use semantic versioning:

- `PATCH` for compatible wording corrections, metadata repair, and documentation fixes that do not materially change decisions.
- `MINOR` for backward-compatible new workflows, evidence gates, or supported modes.
- `MAJOR` for incompatible instruction changes, removed guarantees, or a materially different operating model.

The version in `SKILL.md` frontmatter `metadata.version` is canonical.
Mirror the same value in `agents/openai.yaml` and record every release in `CHANGELOG.md`.

## Required release files

- `SKILL.md`
- `README.md`
- `CHANGELOG.md`
- `MANUAL_ACTIVATION.md`
- `ACTIVATION_SMOKE_TEST.md`
- `agents/openai.yaml`
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

## Read-only smoke test

1. Read the complete `SKILL.md`.
2. Parse YAML frontmatter and `agents/openai.yaml`.
3. Confirm both declare the same version and `stable` status.
4. Confirm every required release file exists and is non-empty.
5. Confirm the default prompt explicitly names `$notion-bilingual-book-curator`.
6. Confirm `MANUAL_ACTIVATION.md` names the same release.
7. Confirm the activation smoke test names the same release.
8. Inspect the archive path list for missing or duplicate package roots.
9. Report version agreement, required-file coverage, and validation separately.

## Release procedure

1. Read the current package and any known version-manager policy.
2. Preserve unrelated files.
3. Choose the smallest semver-compatible release.
4. Update the canonical version and all mirrors.
5. Update the changelog.
6. Run the read-only smoke test.
7. Inspect the diff against the prior package.
8. Package the exact skill directory.
9. Compute a SHA-256 of the release ZIP.
10. If Git sync is not actually performed, report `Git sync: NOT PERFORMED` rather than implying a commit exists.

The v1.2.1 package also requires `references/html-reader-handoff.md`, `assets/icon.svg`, `VERSION`, `VERSIONING_DECISION.md`, `TEST_REPORT.md`, `PACKAGE_MANIFEST.json`, and `scripts/verify_release.py`. Use the canonical Version Manager engine first, then verify every nested or visible version mirror explicitly. Preserve historical version references.
