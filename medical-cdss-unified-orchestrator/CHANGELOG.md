# Changelog

All notable changes to the `medical-cdss-unified-orchestrator` skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.0] - 2026-10-01

### Changed
- Partial results (a selected book missing) exit 3 unless --allow-partial; --book honoured by vignette/diff/outline/validate-therapy; --json refused where unsupported; exactly one mode; --output validated; context packet reports not_populated/complete and no longer claims ESC/AHA evidence.

## [1.4.0] - 2026-09-25

### Changed
- Claude audit fixes: exit 1 when no source is reachable; context packet fails closed and excludes error entries; Davidson added to --diff/--outline; packaged Kumar router used in all modes; loud warning on unpackaged build-router fallback; env-configurable paths

## [1.3.1] - 2026-09-25

### Changed
- Include Davidson 25th Edition in clinical vignette and therapy validation dispatch, and propagate exit codes from subcommands throughout main dispatcher

## [1.3.0] - 2026-09-25

### Changed
- ### Fixed
- Fixed run_build_context_packet to seamlessly handle dict-of-books and list search results without AttributeError.
- Forwarded --compress CLI flag to cdss_federated_search.py subprocess in run_federated_query.
- Preserved JSON output formatting without word-budget truncation when --json is requested.

## [1.2.0] - 2026-09-20

### Changed
- Renamed skill from `medical-cdss-unified-navigator` to `medical-cdss-unified-orchestrator` adhering to the Antigravity orchestrator suffix naming standard.
- Added Sub-Skills Inventory and Handover Contracts for `harrison-cdss-navigator`, `hurst-cdss-navigator`, and `kumar-cdss-navigator`.
- Added Pre-Done Corpus Prerequisites and Fallback Protocol for runtime index degradation.
- Added Grounded Context Packet Builder for 4-book bridge note generation.

## [1.1.0] - 2026-09-20

### Added
- Integrated Kumar and Clark's Clinical Medicine (11th Edition 2026) as the 4th major clinical pillar.
- Added `--book kumar` option to cross-book diagnostic federator.
- Token budget guards to prevent prompt context bloat.

## [1.0.0] - 2026-09-19

### Added
- Initial release of Unified Medical CDSS Orchestrator.
- Cross-book federated search across Davidson 25th, Harrison 22nd, and Hurst 15th.
- Complex clinical case vignette decomposition.
- Cross-book drug therapy safety guardrail.
