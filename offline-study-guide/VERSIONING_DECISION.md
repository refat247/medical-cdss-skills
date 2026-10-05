# Versioning decision — v1.2.1

## Proven predecessor

- package: `offline-study-guide-skill-v1.2.0.zip`
- version: `1.2.0`
- SHA-256: `3e674bdf1efd93251c254466bb026694281c5381b449b34142dfe2663d4018c1`
- functional regression baseline: 59/59 PASS

## Decision

Release `1.2.1` as a SemVer **PATCH**.

Reason: this release repairs package/version governance and install-archive structure without materially changing the skill's decisions, parser, reader shell, source handling, or supported workflow. A MINOR bump would overstate functional change; a MAJOR bump is not justified.

## Retained unchanged

- `scripts/build_guide.py`
- `scripts/check_guide.py`
- `scripts/run_regression.py`
- all reader assets
- all input/reader/clinical references
- eval/triggers behavior

## Added/changed

- version mirrors updated to `1.2.1`;
- OpenAI agent metadata added;
- README/manual activation/smoke test added;
- release verifier and package manifest added;
- install ZIP shape standardized with `SKILL.md` at archive root;
- changelog and release audit updated.

## Compatibility

Backward compatible. No migration is required for v1.2.0 workflows or generated readers.
