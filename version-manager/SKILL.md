---
name: version-manager
version: 1.1.1
description: |
  Universal Semantic Version Bumper, Release Synchronizer, and Keep a Changelog Manager.
  ACTIVATE this skill whenever the user asks to bump version, update skill or software version,
  prepare a release, maintain changelogs, synchronize version declarations across code, tests,
  and documentation, or verify zero-drift version consistency across files.
---

# Version Manager Skill (v1.1.1)

Production-grade automated Semantic Versioning ([SemVer 2.0.0](https://semver.org/)) bumper, multi-file release synchronizer, and [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) management skill for Antigravity agent skills, Python packages, and modular codebases.

---

## 1. When to Activate This Skill

Activate this skill automatically whenever:
- Updating or bumping the version of any Antigravity skill or software repository.
- Releasing a new feature, bug fix, or major architectural change.
- Updating `CHANGELOG.md` or `README.md` with release notes.
- Synchronizing version declarations across `SKILL.md`, `pyproject.toml`, `package.json`, `__init__.py`, `README.md`, and test suites.
- Verifying that no version drift exists between skill documentation and runtime code.

---

## 2. Core Protocol: The 5-Step Release Flow

When executing a version bump or release task, follow this deterministic sequence:

```
[1. Inspect & Discover] ──> [2. Determine SemVer Bump] ──> [3. Execute Multi-File Bump] ──> [4. Run Verification Gate] ──> [5. Execute Test Suite]
```

### Step 1: Inspect & Discover Declarations
Inspect the target skill or project directory to identify all existing version declarations and detect any existing drift:
```bash
python "C:\Users\User\.gemini\config\skills\version-manager\scripts\bump_version.py" <target_dir> --inspect
```
The bumper scans:
- `SKILL.md`: Frontmatter `version: X.Y.Z` and inline `# Skill Name (vX.Y.Z)`
- Python: `__init__.py` (`__version__ = "X.Y.Z"`), `pyproject.toml`, `setup.cfg`, `setup.py`
- Node/TypeScript: `package.json` (`"version": "X.Y.Z"`)
- Documentation: `README.md` (`# Name (vX.Y.Z)` and `Installed (vX.Y.Z)`)
- Changelog: `CHANGELOG.md` (verifies existing release headers)
- Tests: `tests/test_*version*.py` (pinned `assert ... == "X.Y.Z"`)

### Step 2: Determine SemVer Increment
Consult [references/semver_rules.md](references/semver_rules.md) to choose the appropriate increment:

| Change Type | Bump Target | Examples |
| :--- | :--- | :--- |
| **Breaking Change** | `major` (X+1.0.0) | Changing required CLI arguments, dropping features, incompatible parser schemas |
| **New Feature / Extension** | `minor` (X.Y+1.0) | Adding new pipeline stages, new optional flags, expanding document type support |
| **Bug Fix / Maintenance** | `patch` (X.Y.Z+1) | Regex corrections, error handling repairs, doc updates, internal refactoring |
| **Pre-Release** | `<custom>` | `2.0.0-alpha.1`, `2.0.0-rc.1` |

### Step 3: Atomic Multi-File Bump & Changelog Prepend
Execute the deterministic bumper script to atomically update all version declarations and prepend the standardized changelog entry:
```bash
python "C:\Users\User\.gemini\config\skills\version-manager\scripts\bump_version.py" <target_dir> --bump <patch|minor|major|VERSION> --message "<high-signal summary of changes>"
```
*Note: You may also pass `--category {Added|Changed|Fixed|Deprecated|Removed|Security}` to categorize the changelog entry (default: `Changed` for minor/patch, `Added` for new features).*

### Step 4: Run Verification Gate
Verify that 100% of discovered version declarations are strictly identical:
```bash
python "C:\Users\User\.gemini\config\skills\version-manager\scripts\bump_version.py" <target_dir> --verify
```
If any file contains an outdated or conflicting version, the command will exit with code 1 and pinpoint the file and line number. Do not proceed until verified.

### Step 5: Execute Test Suite
Run the project's unit tests to ensure that all version assertions pass and no runtime breakage was introduced:
```bash
python -m pytest <target_dir>/tests -v
```

---

## 3. Automation Engine Reference (`scripts/bump_version.py`)

The skill ships with a standalone, zero-dependency Python script at `scripts/bump_version.py`.

### Command-Line Options

| Flag | Argument | Description |
| :--- | :--- | :--- |
| `target_dir` | Positional | Absolute or relative path to the skill or project directory |
| `--inspect` | Flag | Read-only scan of all version declarations and drift report |
| `--verify` | Flag | Exits with code 0 if all declarations match, 1 if drift detected |
| `--bump` | `patch` \| `minor` \| `major` \| `X.Y.Z` | Computes new SemVer and updates all discovered files |
| `--message` | String | Description of changes to record in `CHANGELOG.md` |
| `--category` | Category | Changelog category (`Added`, `Changed`, `Fixed`, `Deprecated`, `Removed`, `Security`) |
| `--dry-run` | Flag | Displays planned modifications without writing to disk |

---

## 4. References

- [Semantic Versioning 2.0.0 Guidelines](file:///C:/Users/User/.gemini/config/skills/version-manager/references/semver_rules.md)
- [Keep a Changelog Specification](file:///C:/Users/User/.gemini/config/skills/version-manager/references/changelog_spec.md)
