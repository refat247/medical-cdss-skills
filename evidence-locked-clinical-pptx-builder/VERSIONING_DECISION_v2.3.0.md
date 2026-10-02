# Versioning Decision - v2.3.0

Release: `evidence-locked-clinical-pptx-builder v2.3.0`

Immediate predecessor: `2.2.1`; schema version: `3`; breaking change: `false`.

The minor release adds a reusable DECIDE scenario/prompt contract and a
case/reveal layout preflight informed by a user-preferred visual repair. The
new `source_derived_scenario` property is optional in the schema for legacy
ledgers and required by workflow for new case-based builds. The v1.5 deck is a
design reference only and has no clinical or certification authority.
