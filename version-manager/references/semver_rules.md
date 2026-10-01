# Semantic Versioning 2.0.0 Specification & Agent Skill Rules

This reference outlines Semantic Versioning (SemVer 2.0.0) conventions with specialized guidance for Agent Skills and Python/TypeScript repositories.

---

## 1. SemVer 2.0.0 Summary

Given a version number `MAJOR.MINOR.PATCH`, increment the:

1. **MAJOR** version when you make incompatible API changes, breaking CLI changes, or contract alterations.
2. **MINOR** version when you add functionality in a backward compatible manner.
3. **PATCH** version when you make backward compatible bug fixes or internal maintenance.

Additional labels for pre-release and build metadata are available as extensions to the `MAJOR.MINOR.PATCH` format:
- Pre-release: `1.0.0-alpha`, `1.0.0-beta.1`, `1.0.0-rc.2`
- Build metadata: `1.0.0+20260914`, `1.0.0-beta+exp.sha.5114f85`

---

## 2. Decision Tree for Version Bumps

```
Does the change modify public interfaces, schemas, or behaviors in an incompatible way?
 ├── YES ──> BUMP MAJOR (X+1.0.0)
 └── NO
      ├── Does the change add new features, flags, capabilities, or backward-compatible extensions?
      │    └── YES ──> BUMP MINOR (X.Y+1.0)
      └── NO
           └── Is the change a bug fix, doc update, performance tweak, or internal refactoring?
                └── YES ──> BUMP PATCH (X.Y.Z+1)
```

---

## 3. Agent Skill Specific Guidelines

Agent skills are combinations of markdown instructions (`SKILL.md`), executable Python/Node scripts (`scripts/`), reference documentation (`references/`), and prompt heuristics.

### Major Version (X.0.0)
Trigger a **MAJOR** bump if:
- **Input/Output Schema Breaking Changes**: Changing the expected input structure (e.g. changing mandatory arguments, moving output file locations).
- **Tool or Dependency Incompatibilities**: Requiring a new major runtime or removing previously supported flags (e.g. dropping `--source` in favor of a new syntax).
- **Execution Pipeline Breaking Changes**: Changing pipeline stage IDs, removing intermediate stage artifacts, or altering parser schemas that downstream skills rely upon.

### Minor Version (0.X.0 or X.Y.0)
Trigger a **MINOR** bump if:
- **New Features & Flags**: Adding new CLI options (e.g. `--stage auto`, `--skip-ocr`), new heuristic engines, or supporting additional document types (e.g. adding clinical practice guidelines support).
- **Backward-Compatible Extensions**: Enhancing existing functions with optional arguments or non-breaking default fallbacks.
- **New Skill Triggers**: Expanding frontmatter triggers to activate the skill for broader related workflows without breaking existing ones.

### Patch Version (0.0.X or X.Y.Z)
Trigger a **PATCH** bump if:
- **Bug Fixes**: Correcting regex patterns, fixing boundary conditions, repairing edge-case crashes.
- **Performance & Optimization**: Improving execution speed, reducing memory footprint, eliminating token overhead without altering behavior.
- **Documentation & Formatting**: Updating `README.md`, fixing typos, refining docstrings, improving logging output.
- **Test Suite Updates**: Adding or updating unit/integration tests that do not alter the production API.

---

## 4. Pre-Release & Initial Development

- **Major Version Zero (`0.y.z`)**: Initial rapid development. Anything MAY change at any time. The public API SHOULD NOT be considered stable.
- **Version `1.0.0`**: Signals that the software/skill has reached production-grade maturity, has a defined public API, and follows strict backward compatibility guarantees.

---

## 5. Zero-Drift Synchronization Rule

In modern modular systems, version declarations frequently exist across multiple files:
- `SKILL.md` (frontmatter `version:` and inline text)
- `__init__.py` (`__version__ = "..."`)
- `pyproject.toml` / `package.json` (`version = "..."`)
- `README.md` (`Installed (vX.Y.Z)`)
- `CHANGELOG.md` (`## [X.Y.Z] - YYYY-MM-DD`)
- `tests/test_*version*.py` (`assert __version__ == "..."`)

**Every release MUST synchronize 100% of these files in the same commit/operation.** A version discrepancy of even one patch number between `SKILL.md` and `__init__.py` constitutes a version drift defect.
