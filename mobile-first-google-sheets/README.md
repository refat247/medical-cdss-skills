# Mobile-First Google Sheets v1.2.1

Reusable ChatGPT skill for designing, auditing, repairing, and QA-testing Google Sheets workflows intended primarily for phone/tablet use.

Invocation scopes: **BUILD | AUDIT | AUDIT_REPAIR_REAUDIT**.

Device classes: **MOBILE-PRIMARY | MOBILE-SECONDARY | DESKTOP-PRIMARY**.

Core model: **ACT → ORIENT → CHECK → NAVIGATE → ANALYZE → ADMINISTER**.

The skill treats tab order, viewport width, context persistence, tap count, blank/zero semantics, partial-entry detection, performance, protection, and Google-native conversion as first-class UX and integrity concerns. v1.2.0 introduced the strengthened native-conversion gate with timezone, merged-range, freeze, stale conditional-format, protection, navigation, and post-mutation re-read verification.

## Package
- `SKILL.md` — canonical instructions and version
- `README.md` — package overview
- `CHANGELOG.md` — release history
- `MANUAL_ACTIVATION.md` — fallback when native activation is unavailable
- `ACTIVATION_SMOKE_TEST.md` — fresh-runtime activation gate
- `agents/openai.yaml` — agent metadata/version mirror
- `references/` — capability evidence, QA checklist, audit rubric
- `scripts/bump_version.py` — SemVer synchronization/verification
- `tests/` — package/regression tests

## Release state language
Keep `PACKAGE BUILT`, `PACKAGE VERIFIED`, `INSTALLED`, `RUNTIME ACTIVATED`, `SMOKE TESTED`, `BEHAVIOR VERIFIED`, `GIT SYNC VERIFIED`, and `NOTION ARCHIVE VERIFIED` separate.

## Native lifecycle
`SOURCE VALIDATED → CONVERTED → NATIVE AUDITED → NATIVE REPAIRED → RE-AUDITED → MOBILE VERIFIED`

`MOBILE VERIFIED` is reserved for applicable native checks that have actually passed.