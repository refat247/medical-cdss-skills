---
name: humanizer-niqs-bridge
description: Apply upstream Humanizer v3.1.0 as the prose-cleanup engine while enforcing the Khaled Knowledge OS NIQS preservation boundary for evidence-bearing, clinical, legal, technical, provenance, and governance text. Use for human-facing prose cleanup in governed Notion workflows when Humanizer and NIQS must cooperate.
metadata:
  version: 1.0.0
---

# Humanizer NIQS Bridge

Use this skill as the governance bridge between upstream `blader/humanizer` v3.1.0 and the Khaled Knowledge OS NIQS preservation rules.

## Operating contract

1. Perform the domain task first. Structural, semantic, research, clinical, legal, evidence, and governance rules remain authoritative.
2. Apply Humanizer only to newly written or materially rewritten human-facing prose.
3. Preserve every supported fact, number, date, quotation, citation, evidence label, uncertainty statement, warning, decision, route, clinical/legal meaning, and exact technical literal.
4. If Humanizer conflicts with NIQS preservation, NIQS wins.
5. Run a semantic-drift check after the prose pass.
6. Never claim native Humanizer runtime activation merely because this bridge is loaded.

## Upstream dependency

The prose engine is upstream `blader/humanizer` v3.1.0. This bridge does not rename or fork that release.

When native upstream Humanizer is available, use it and then enforce this bridge.

When native upstream Humanizer is unavailable, use only a preservation-safe local cleanup and state:

`MANUAL PROTOCOL LOADED — native runtime not claimed`

Do not represent the fallback as full upstream runtime activation.

## v3.1 behavior that matters to this bridge

- Use conversation context when deciding whether a sentence adds information.
- In replies and handoffs, avoid re-explaining background the reader already knows when the decision can be stated directly.
- Remove document-self-narration, sourcing narration, assembly narration, or visible-layout narration only when it carries no evidentiary or operational value.
- Prefer headings that name the section content rather than headings written mainly for effect.
- Remove sentences after examples or numbers when they merely restate what the example already demonstrated.
- Preserve dictionary-required hyphenation such as `third-party` and `cross-functional`.

See `references/upstream-humanizer-v3.1.0.md`.

## NIQS preservation boundary

Do not humanize wording when the wording or value itself carries evidence, audit, safety, legal, clinical, provenance, canonical, or technical meaning.

Protected classes include:

- raw evidence, quotations, and evidence excerpts;
- immutable or canonical source text and protected corpus material;
- clinical or legal meaning, safety warnings, and uncertainty statements;
- evidence state, audit state, canonical state, workflow state, rule state, review state, and decision state;
- exact claim/source-card fields;
- provenance that affects trust, reproducibility, or what the reader may conclude;
- benchmark, qrel, chunk, case, model, version, SHA/hash, and other identifiers;
- code, commands, paths, YAML/JSON, formulas, URLs, and exact technical literals;
- dates, numbers, measurements, rankings, and citations;
- frozen or dated artifacts whose preservation is part of provenance.

See `references/niqs-preservation-overlay-v1.0.0.md`.

## Pattern 25 override

Generic Humanizer may remove text describing how a document was sourced, assembled, verified, or laid out.

In Knowledge OS, retain that text when it changes:

- evidence interpretation;
- provenance;
- verification state;
- reproducibility;
- permitted conclusions;
- auditability.

Remove it only when it is redundant presentation commentary.

## Pattern 26 override

Use conversation-aware compression strongly in replies, handoffs, current-state summaries, dashboards, and next-step instructions.

Do not remove context that a standalone Notion page needs in order to remain intelligible when opened without the surrounding conversation.

## Semantic-drift gate

Compare the final prose with the pre-Humanizer text. Restore any altered or dropped:

- fact;
- number;
- date;
- citation;
- evidence/status label;
- uncertainty;
- decision;
- warning;
- route;
- clinical/legal meaning;
- exact technical literal.

If preservation cannot be guaranteed, do not apply the prose edit.

See `references/semantic-drift-check.md`.

## Output state

A completed run should distinguish:

- upstream Humanizer version used;
- bridge package version;
- NIQS overlay version;
- native runtime activation state;
- whether any text was skipped because preservation rules overrode prose cleanup.

Do not collapse these states into one claim.
