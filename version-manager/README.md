# Version Manager (v1.2.1)

Portable Semantic Versioning and release synchronization for **OpenAI/ChatGPT Agent Skills**, Python packages, Node/TypeScript projects, and other file-based repositories.

**Version:** 1.2.1

## What v1.2.0 adds

- ChatGPT/OpenAI skill-package support without Windows/Gemini-specific paths.
- Detection and update of both `SKILL.md` top-level `version` and nested `metadata.version`.
- Detection and update of `agents/openai.yaml` version metadata.
- Full SemVer 2.0.0 prerelease/build parsing in supported declarations.
- Zero declarations now fail as `UNRESOLVED` instead of falsely passing.
- `--dry-run` support.
- Rollback-protected staged writes with accurate non-transactional wording.
- Regression tests for the current Workspace Curator, Content Auditor, and Research Method Curator version-layout patterns.
- Clean distributable packaging rules for ChatGPT skills.

## Typical usage

```bash
python scripts/bump_version.py <target_dir> --inspect
python scripts/bump_version.py <target_dir> --verify
python scripts/bump_version.py <target_dir> --bump patch --message "Repair version metadata" --dry-run
python scripts/bump_version.py <target_dir> --bump patch --message "Repair version metadata"
python scripts/bump_version.py --suite <skills_parent_dir> --verify
```

The script is standard-library only. The bundled test suite uses `pytest` when available.

## Supported ChatGPT skill metadata

The manager recognizes current declarations in:

- `SKILL.md` frontmatter: `version:` or `metadata.version`
- `agents/openai.yaml`: top-level `version:`
- current version markers in `README.md`
- latest release heading in `CHANGELOG.md`

It does not intentionally force historical version mentions in archived prose or reference notes to match the current release.

## Safety boundary

A file synchronization is not proof of installation, runtime activation, or Git synchronization. For manually uploaded ChatGPT skills, run a fresh-session smoke test after installing the generated ZIP.

## Package layout

```text
version-manager/
├── SKILL.md
├── README.md
├── CHANGELOG.md
├── agents/
│   └── openai.yaml
├── assets/
│   └── icon.svg
├── references/
│   ├── semver_rules.md
│   └── changelog_spec.md
├── scripts/
│   ├── __init__.py
│   └── bump_version.py
└── tests/
    ├── __init__.py
    └── test_bump_version.py
```
