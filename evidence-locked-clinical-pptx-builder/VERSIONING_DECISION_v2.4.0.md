# Versioning Decision - v2.4.0

Release: `evidence-locked-clinical-pptx-builder v2.4.0`

Immediate predecessor: `2.3.0`; schema version: `3`; breaking change: `false`.

Minor release: adds an optional presentation-only `VISUAL_POLISH` mode with
its own blocking content-lock gate. Existing projects are unaffected unless
they set `release_policy.visual_polish.enabled: true` or declare
`visual_polish_applied` in the promotion gates. The new pipeline state
`visual_polish` sits between `clinical_provenance_audit` and
`automated_preflight`; projects that do not polish mark it `waived` or
`complete` with a note. No gate was relaxed.
