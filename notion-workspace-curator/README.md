# Notion Workspace Curator

**Package:** `notion-workspace-curator`
**Version:** `0.6.0`
**Date:** 3 Oct 2026
**Status:** Stable package source release. Artifact-form routing is authored on top of NIQS v1.0; runtime installation/activation of v0.6.0 remains a separate fresh-session gate.

## Purpose

This skill audits, repairs and maintains Notion workspaces as structured knowledge systems. It covers canonical navigation, hub/page UX, database indexing, duplicate control, research-output preservation, audit checkpoints, native Notion formatting, mobile-first page readability and a thin Mobile Access Layer.

## What changed in this release

`0.6.0` adds a deterministic artifact/writing routing layer without changing NIQS v1.0. The Curator now routes ambiguous pages through **Domain / Ownership → NIQS Page Role → Artifact Form → Canonical Home**, with precedence **existing canonical parent → domain ownership → NIQS Page Role → artifact form**.

The release also adds:
- an **existing-router-first** guardrail so a new routing/index page is not created when the canonical router can absorb the rule cleanly;
- explicit separation of **Page Role** from **Artifact Form**, preventing a competing taxonomy;
- domain-specific vs cross-domain routing rules for audits, SOPs, guides, prompts, handoffs, learning notes, execution reports and manuscripts;
- a writing-specific guardrail: being prose is not sufficient reason to route content into a writing area;
- the detailed reference `references/artifact-routing.md`.

NIQS remains **v1.0**. Content Auditor and Research Method Curator ownership boundaries are unchanged.
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
