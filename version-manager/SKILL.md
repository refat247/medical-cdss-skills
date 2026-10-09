---
name: version-manager
description: Portable Semantic Versioning and release-synchronization skill for OpenAI/ChatGPT Agent Skills and conventional software projects. Use when inspecting version drift, choosing a SemVer bump, synchronizing current version declarations across SKILL.md and agents/openai.yaml plus package/runtime/docs files, updating changelogs, preparing releases, or verifying package version consistency.
metadata:
  version: 1.2.1
---

# Version Manager

Use this skill to inspect, synchronize, bump, and verify software or skill-package versions without assuming a specific operating system or agent runtime.

## Core rule

**Discover before changing. Treat zero discovered declarations as unresolved, not success. Stage edits before writing. Verify after writing. Never infer Git sync, installation, or runtime activation from a file edit alone.**

This package is designed for OpenAI/ChatGPT Agent Skills while remaining portable to Python, Node/TypeScript, and other file-based repositories.

## Environment behavior

- Use paths available in the **current execution environment**. Never assume `C:\Users\...`, `.gemini`, or any other machine-specific path.
- Prefer the bundled `scripts/bump_version.py` when code execution and file access are available.
- Resolve the script relative to this skill package or copy/use it from the mounted package. Do not invent a path to a user's local computer.
- If the target files are not accessible in the current runtime, report that boundary instead of claiming a version update was executed.
- A successful file update proves only the files changed. Keep these states separate: **package edited → validation passed → ZIP/export created → manually installed → runtime smoke-tested → Git-synced**.

## Release flow

1. **Inspect** — inventory all current version declarations and identify drift.
2. **Choose bump** — major, minor, patch, or explicit SemVer 2.0.0 value.
3. **Dry run** — for nontrivial packages, preview planned modifications first.
4. **Synchronize** — update the canonical current declarations and prepend a changelog release when appropriate.
5. **Verify** — require at least one declaration and exact agreement across all discovered current declarations.
6. **Test** — run the package/project tests when they exist.
7. **Package/runtime boundary** — when working on a ChatGPT skill, verify package structure separately and perform a fresh-session smoke test after manual installation.

## Supported ChatGPT skill declarations

For OpenAI/ChatGPT skill packages the engine explicitly supports:

- `SKILL.md` frontmatter `version: X.Y.Z`
- `SKILL.md` nested `metadata.version`
- optional `# Name (vX.Y.Z)` current heading
- `agents/openai.yaml` top-level `version`
- current `README.md` forms such as `**Version:**`, `Version:`, `**Working version:**`, `Installed (vX.Y.Z)`, and title `(vX.Y.Z)`
- latest `CHANGELOG.md` release heading

Do not treat historical version mentions buried in prose/reference archives as declarations that must equal the current version.

## Other supported declarations

- `pyproject.toml`
- `package.json`
- `setup.cfg` / `setup.py`
- `__version__` in Python `__init__.py`
- selected `PIPELINE_VERSION`, `VERSION`, and `APP_VERSION` Python constants
- pinned version assertions in version/consistency tests

Full SemVer 2.0.0 prerelease and build metadata are supported, e.g. `2.0.0-rc.1+build.7`.

## Commands

Run from a location where the package script and target files are accessible.

```bash
python scripts/bump_version.py <target_dir> --inspect
python scripts/bump_version.py <target_dir> --verify
python scripts/bump_version.py <target_dir> --bump minor --message "Add OpenAI skill metadata support" --dry-run
python scripts/bump_version.py <target_dir> --bump minor --message "Add OpenAI skill metadata support"
python scripts/bump_version.py --suite <skills_parent_dir> --verify
```

### Exit semantics

- `--inspect` and `--verify` return success only when **one or more** declarations are discovered and all agree.
- Zero declarations = **UNRESOLVED / failure**.
- Drift = failure with declaration-level evidence.
- `--dry-run` performs no writes.

## Bump selection

Read [references/semver_rules.md](references/semver_rules.md).

| Change | Bump |
|---|---|
| incompatible behavior/API/schema | major |
| backward-compatible new capability | minor |
| compatible bug fix/docs/metadata repair | patch |
| explicit prerelease/build | explicit SemVer |

For this v1.2.0 adaptation, the change is **minor** because OpenAI/ChatGPT skill-package support and new declaration types were added without intentionally breaking the CLI.

## Write safety

The engine computes all target file contents before committing them. It writes temporary files and attempts rollback if an ordinary write/replace operation fails. Do **not** call this a true cross-file filesystem transaction: a process crash or external filesystem failure can still interrupt a multi-file update.

For important repositories, use source control and inspect the diff before release.

## ChatGPT skill package verification

When the target is a reusable ChatGPT skill, separately verify:

- `SKILL.md` is present at the skill root;
- referenced files actually exist;
- `agents/openai.yaml` parses if the package uses it;
- `SKILL.md` and `agents/openai.yaml` declare the same current version when both carry a version;
- cache/build artifacts such as `.pytest_cache/`, `__pycache__/`, `.DS_Store`, and temporary files are excluded from the distributable ZIP;
- package validation/test results are distinguished from installation/runtime smoke-test results.

## Human-facing reporting

Report:

- discovered declarations and files;
- baseline version and any drift;
- chosen target and why its SemVer class fits;
- files changed or planned;
- verification and tests separately;
- package/export/install/runtime/Git states separately;
- unresolved limitations.

## References

- [Semantic Versioning rules](references/semver_rules.md)
- [Keep a Changelog conventions](references/changelog_spec.md)
