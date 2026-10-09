# Semantic Versioning 2.0.0 & Skill Release Rules

Use SemVer as `MAJOR.MINOR.PATCH`, optionally followed by prerelease and build metadata.

- **MAJOR**: incompatible contract, CLI, schema, or behavior change.
- **MINOR**: backward-compatible capability or supported-format expansion.
- **PATCH**: compatible bug fix, metadata repair, documentation correction, or internal maintenance.
- Examples: `1.2.3`, `2.0.0-rc.1`, `2.0.0-rc.1+build.7`.

## Agent-skill guidance

For OpenAI/ChatGPT or other Agent Skills:

- **Major**: remove/rename required inputs, remove guarantees, change execution semantics incompatibly, or require an incompatible runtime/tool contract.
- **Minor**: add supported file types, add optional flags/workflows, expand triggers, or add backward-compatible platform support.
- **Patch**: repair parsing, metadata, wording, tests, packaging hygiene, or non-breaking implementation defects.

## Zero-drift rule

Synchronize **current canonical declarations**, not every historical version mention. Common current declarations include:

- `SKILL.md` top-level `version` or nested `metadata.version`;
- `agents/openai.yaml` top-level `version` when present;
- package/runtime declarations such as `pyproject.toml`, `package.json`, or `__version__`;
- current README version markers;
- the latest changelog release heading;
- intentional version-pinned tests.

Historical changelog entries and archived/reference prose are provenance and normally remain unchanged.

## Drift handling

- Zero discovered declarations = unresolved/failure.
- Multiple current versions = drift/failure.
- Do not choose a relative `major`/`minor`/`patch` baseline silently when drift exists. Repair drift first or supply an explicit target SemVer.

## State boundary

A synchronized package is not automatically installed, runtime-verified, or Git-synced. Record those states separately.
