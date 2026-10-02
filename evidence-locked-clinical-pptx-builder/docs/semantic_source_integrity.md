# Semantic Source Integrity — v2.2.1

For v2.3.0 case-based DECIDE prompts, also apply
`docs/decide_prompt_contract.md`: preserve source-derived scenario and neutral
question as separate fields, validate their combined `prompt_text`, and keep
the source's recommendation withheld until the reveal. The deterministic
validator adds metalanguage, fragment, action leakage, and short-stem screens;
locked-source semantic adjudication remains mandatory.

v2.2.1 hardens the v2.2 semantic-integrity architecture and closes fail-open implementation gaps found by adversarial execution.

## Three separate completeness gates

1. `SOURCE_INVENTORY_CERTIFICATION`: compare an independently established source-structure/recommendation census against the source-recommendation inventory. This proves source → inventory completeness.
2. `SOURCE_EXTRACTION_COMPLETENESS`: compare every certified inventory recommendation against exactly one extraction-accounting record. `EXTRACTED` requires at least one valid decision-node ID; explicit non-node dispositions require reason, reviewer and completed semantic review.
3. `DOWNSTREAM_NODE_COVERAGE`: verify already-extracted nodes are represented downstream.

A perfect downstream score cannot compensate for a missing source recommendation, and a perfect inventory→extraction score cannot compensate for an incomplete source inventory.

## Independent source census

For guideline-style documents, enumerate recommendation tables/rows (plus standalone narrative recommendations when applicable) directly from locked source structure. The census pathway must be independent of the inventory-generation pathway, or receive explicit human semantic adjudication with reviewer and rationale. A 130-row inventory fails against a census expecting 131.

## Footnote binding

The standard ledger uses one row per recommendation-footnote binding: recommendation ID, footnote ID, marker ID, markers present on the recommendation, scope, source locator, source owner/scope, required-for-meaning flag, display location, binding status and semantic adjudication. Dynamic columns such as `footnote_marker__F1` are deprecated.

## Normalization

Bibliographic citation numbers are not clinical numeric facts. Citation-number removal is permitted only when the removed material is recognized as bibliographic citation syntax and the remaining text is otherwise unchanged. Clinically meaningful thresholds, doses, units, percentages, ages, durations, ranges, COR/LOE, operators, markers and negation remain protected.

## Repair authority

User instruction may authorize pedagogy, audience tier, layout/style, meaning-preserving simplification, or formal evidence-boundary expansion. It cannot by itself authorize a clinical factual mutation. Clinical changes require verified support from a currently approved locked source; a new source must first be added and the evidence boundary relocked.

## Promotion

All unresolved CRITICAL/HIGH defects block promotion by default, including future/unknown defect families. Every non-independent required gate accepts only PASS/CERTIFIED. Independent visual QA is the only waivable gate, and only under `required_unless_explicit_user_waiver` with an explicit recorded waiver.
