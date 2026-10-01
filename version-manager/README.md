# Version Manager (v1.2.0)

Automated Semantic Versioning (SemVer 2.0.0), release synchronizer, and Keep a Changelog management skill for Google Antigravity agent skills, Python packages, and multi-file codebases.

---

## 🚀 Key Features

- **Automated Multi-File Discovery**: Automatically scans and detects version declarations across:
  - `SKILL.md` (YAML frontmatter and inline headers)
  - Python packages (`__init__.py`, `pyproject.toml`, `setup.cfg`, `setup.py`)
  - Node / TypeScript (`package.json`)
  - Documentation (`README.md` "Installed (vX.Y.Z)", title headings)
  - Changelogs (`CHANGELOG.md`)
  - Unit tests (`tests/test_*version*.py` pinned version assertions)
- **Zero-Drift Synchronization**: Updates all version declarations atomically in a single pass.
- **Drift Verification Gate**: Flags any mismatched or stale version numbers across the repository with file paths and line numbers.
- **Changelog Automation**: Automatically prepends standardized release sections into `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
- **Zero External Dependencies**: Pure Python standard library implementation (`re`, `os`, `sys`, `datetime`, `argparse`, `typing`).

---

## 🛠️ CLI Usage

The skill provides the `scripts/bump_version.py` utility:

### 1. Inspect Current Versions
Discover all version declarations and check for drift without making any changes:
```bash
python -m scripts.bump_version <target_dir> --inspect
```

### 2. Verify Version Consistency
Verifies that all files are synchronized to the exact same version (fails with exit code 1 on drift):
```bash
python -m scripts.bump_version <target_dir> --verify
```

### 3. Bump Version
Bump the version atomically across all files and update `CHANGELOG.md`:

```bash
# Bump patch (e.g. 1.0.0 -> 1.0.1)
python -m scripts.bump_version <target_dir> --bump patch --message "Fix regex parsing edge cases"

# Bump minor (e.g. 1.0.0 -> 1.1.0)
python -m scripts.bump_version <target_dir> --bump minor --message "Add support for guideline documents"

# Bump major (e.g. 1.0.0 -> 2.0.0)
python -m scripts.bump_version <target_dir> --bump major --message "Overhaul pipeline architecture"

# Set explicit version (e.g. 2.5.0-rc.1)
python -m scripts.bump_version <target_dir> --bump 2.5.0-rc.1 --message "Release candidate 1"
```

---

## 📁 Repository Structure

```
version-manager/
├── SKILL.md                 # Antigravity skill specification & triggers
├── README.md                # Skill overview & CLI usage documentation
├── CHANGELOG.md             # Keep a Changelog history
├── scripts/
│   └── bump_version.py      # Core deterministic version bumper & verifier
├── references/
│   ├── semver_rules.md      # SemVer 2.0.0 specification & agent skill rules
│   └── changelog_spec.md    # Keep a Changelog specification & templates
└── tests/
    └── test_bump_version.py # Automated unit test suite
```
