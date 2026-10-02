# Versioning Decision — v2.1.0

## Decision

Release `evidence-locked-clinical-pptx-builder` **v2.1.0**.

## Rationale

This is a backward-compatible minor release over v2.0.0. It adds meaningful capability and policy enforcement based on actual final MI artifact regression, but does not introduce an incompatible architecture or clinical-content schema change.

## Why not v2.0.1?

The update is more than a bugfix: it adds structured independent-review manifests, render-set hashing, domain-complete visual ledgers, fail-closed independent QA status, and final-artifact regression fixtures/reports.

## Why not v3.0.0?

The v2 state model, modes, evidence/case pipeline and artifact pipeline remain compatible. Existing projects can migrate without breaking clinical artifacts.
