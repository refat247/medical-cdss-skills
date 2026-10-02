# Humanizer NIQS Bridge

A governance bridge for using upstream `blader/humanizer` v3.1.0 inside Khaled Knowledge OS without allowing prose cleanup to mutate evidence, provenance, clinical/legal meaning, canonical states, or exact technical literals.

## Package identity

- Skill: `humanizer-niqs-bridge`
- Package version: `1.0.0`
- Upstream Humanizer baseline: `blader/humanizer` v3.1.0
- NIQS overlay: v1.0.0
- Release date: 2026-09-28
- Runtime activation: separate state; not implied by the ZIP, Git, or Notion mirror

## Why this is a bridge instead of a fork

The upstream Humanizer release keeps its own identity and version. Knowledge OS adds local governance in a separate package. This prevents an invented `3.1.1-Khaled` lineage and makes later upstream updates easier to audit.

## Package layout

```text
humanizer-niqs-bridge/
  SKILL.md
  README.md
  CHANGELOG.md
  ACTIVATION_SMOKE_TEST.md
  agents/openai.yaml
  references/upstream-humanizer-v3.1.0.md
  references/niqs-preservation-overlay-v1.0.0.md
  references/semantic-drift-check.md
  assets/icon.svg
  PACKAGE_MANIFEST.sha256
```

## Execution order

1. Domain/NIQS work.
2. Upstream Humanizer v3.1.0 on eligible human-facing prose.
3. NIQS preservation override.
4. Semantic-drift recheck.
5. Report runtime state accurately.

## Maintenance

When upstream Humanizer changes, compare the new release against v3.1.0. Update the bridge only if the integration behavior or preservation boundary changes. A new upstream release alone does not automatically require a new bridge version.

If bridge behavior changes, version this package using SemVer and keep `SKILL.md` `metadata.version` synchronized with `agents/openai.yaml`.
