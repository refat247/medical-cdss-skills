# Notion Workspace Curator

**Package:** `notion-workspace-curator`
**Version:** `0.5.0`
**Date:** 25 Sep 2026
**Status:** Stable package source release. NIQS v1.0 is authored and Git-synchronized; runtime installation/activation of v0.5.0 remains a separate fresh-session gate.

## Purpose

This skill audits, repairs and maintains Notion workspaces as structured knowledge systems. It covers canonical navigation, hub/page UX, database indexing, duplicate control, research-output preservation, audit checkpoints, native Notion formatting, mobile-first page readability and a thin Mobile Access Layer.

## What changed in this release

`0.5.0` adds NIQS v1.0 while preserving the verified mobile/access/provenance rules. Historical `0.4.3` promoted the reconciled `0.4.3-rc.2` package after user-confirmed real-device validation. It retains the verified v0.4.1 mobile first-screen rule and the v0.4.2 Mobile Access Layer guidance, reconciles the two divergent `0.4.3-rc.1` builds, and includes:

- New substantive pages are classified against the technical glossary categories.
- Relevant source pages link to applicable glossary category pages.
- Applicable glossary pages link back to each canonical source/control/project page.
- Descendants are classified independently rather than inheriting parent coverage.
- Every write is re-fetched and verified in both directions.
- Reconciliation uses `EXPECTED = VERIFIED BIDIRECTIONALLY LINKED + UNRESOLVED`.
- Material changes are propagated to the appropriate canonical index or companion page.
- Timestamped evidence archives are placed under the canonical synthesis/status page or nearest durable research hub.
- Canonical pages, evidence archives and source-card children receive verified forward and return navigation without rewriting raw evidence.
- Package identity is declared consistently in `SKILL.md`, this README, the changelog and `agents/openai.yaml`.

The retained Mobile Access Layer guidance includes:

- Mobile Home should be intent-first rather than a miniature workspace tree.
- Recommended first-screen order: Capture → Today / Needs Action → Active Projects → Review → Search / Reference.
- Use one Universal Inbox/staging layer for low-friction capture when needed.
- Capture now, classify later; avoid forcing taxonomy/project/destination at input time.
- Reuse canonical databases and pages through linked views/direct links instead of duplicating mobile databases.
- Prefer compact mobile views with only decision-relevant properties.
- Use native widgets/shortcuts/Share Sheet before heavier external automation.
- Keep schema/relations/formulas/mass triage/structural curation desktop-first.
- Require real-device testing before claiming mobile UX is fully verified.

## Installation

Install the ZIP/folder as a ChatGPT/Work custom skill using the normal manual skill installation flow for your environment. The archive root contains `SKILL.md` directly, with supporting files under `references/`, `agents/`, and `assets/`.

## Package structure

## NIQS v1.0

This release adopts the shared `references/notion-information-quality-standard.md` contract. It covers page roles, three reading depths, evidence/claim states, freshness classes, verification metadata, decision readiness, confidence×consequence escalation, source authority, update impact, supersession/current truth, information density, audience/language modes, staleness, evidence debt, maintenance cost, decision value, change deltas, monitoring, AI handoffs, contradiction states and uncertainty budgets.

The standard is shared, but ownership remains separated across Workspace Curator, Content Auditor and Research Method Curator. Do not treat one skill's PASS as the others' PASS.
