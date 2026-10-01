# Changelog

All notable changes to this skill are documented here (Keep a Changelog).

## [1.1.1] - 2026-10-01

### Changed
- Review fixes: revive --search, alerts exit 1, plural/brand matching, negation note

## [1.1.0] - 2026-10-01
### Changed
- `--prescribing-safety`: no matching rule now reports `NOT_EVALUATED` (exit 3) instead of `PERMITTED_WITH_ROUTINE_MONITORING`; all matching rules are shown (previously only the first); matching is whole-word (no more "iron" in "environment" or "ttp" in "http").
- `--tropical-calc`: all inputs are required and range-checked; the former default patients (Na 140/Cl 100/HCO3 15, MCV 65/RBC 5.8, 50 kg) are gone; maintenance fluid uses a continuous Holliday-Segar (was 2000 mL at 20 kg vs 1520 mL at 21 kg); anion-gap and Mentzer text no longer over-claims (needs low HCO3 for "acidosis"; MCV < 80 for Mentzer; index = 13 is indeterminate); dengue output carries a "static estimate, not a prescription" notice.
- `--federated`: now an honest Habijabi-to-Davidson bridge lookup. The canned Harrison/Hurst/Kumar text is removed; those books are reported as NOT QUERIED with the unified-orchestrator command to use. No-match no longer falls back to the first row.
- `--preceptor`, `--ward-facilities`, `--search`: stop-word-filtered whole-word matching, no silent fallback to record 0, Bengali words no longer split at vowel signs, short English terms (TB, DM, MI) kept.
- CLI: empty values are errors, two modes at once is an error, unknown SBA ids are an error, `--top_k` must be >= 1, exit codes reflect the outcome; corpus root via `CDSS_HABIJABI_ROOT`.
### Added
- `tests/test_habijabi_navigator.py` (40 tests).
### Needs clinician sign-off
- The linezolid rule's serotonergic list was extended (paroxetine, citalopram, fluvoxamine, venlafaxine, desvenlafaxine, amitriptyline, nortriptyline, tramadol, tricyclic).
- Unreviewed and unchanged: the six rule texts, the 4 hard-coded SBA items (including keys/explanations flagged in the audit), and the dengue fluid method.

## [1.0.0]
- Initial release.
