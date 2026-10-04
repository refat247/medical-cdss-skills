# Governed Production Orchestration

Use this reference for end-to-end source-to-publication execution.

## State machine
`SOURCE SET LOCK → AUDIT/BLOCKER LEDGER → INTERNAL CLOSURE → RESEARCH AUTHORIZATION GATE → EVIDENCE PACKETS → DRAFTING → MANUSCRIPT QA → PRODUCTION ROUTE → ACTUAL ARTIFACT QA → BOUNDED REPAIR/REGRESSION → MODE E → RELEASE CLOSURE`

At every major transition re-read the governing reference for the next phase.

## Blocker ledger
Each material blocker records stable ID, affected chapter/output, evidence deficit, current evidence state, internal-source exhaustion, research authorization, smallest closure action, closure result (CLOSED / PARTIAL-CLOSED / PRESERVED UNRESOLVED / OPEN), and a regression sentinel. A blocker may remain SOURCE PARTIAL or UNRESOLVED when the book can stay truthful without closing it.

## Research authorization
Do not interpret end-to-end execution as permission to add outside facts. If internal evidence is insufficient and external verification is not authorized, stop that blocker at `INTERNAL EVIDENCE EXHAUSTED — EXTERNAL RESEARCH AUTHORIZATION REQUIRED`. When authorized, research only named blockers unless broader research is explicitly authorized. Feed verified repairs back into evidence packets before drafting.

## Drafting gate
Chapter eligibility: READY; READY NARROW; READY WITH SOURCE PARTIAL; BLOCKED.

## Production routing
The Curator is the governor, not necessarily the renderer. Routes may include direct DOCX/PDF build, external document builder, or a specialized builder such as an offline study-guide/reader skill. Record input version, authorized transformation scope, expected output, verification method, and previous artifact when available. Do not merge a specialist builder into the Curator merely because the Curator routes to it.

## Freeze vs release closure
Mode E verifies the publication artifact. After Mode E PASS, when a canonical release is requested, identify exact artifacts, compute SHA-256 when bytes are available, create a compact release manifest, record version/evidence snapshot, state immutability and derivative rules, and define the next-version rule.

Invariant: `PASS — FREEZE READY ≠ RELEASE PACKAGED`.

## Counterfactual anti-bloat test
Before adding a permanent rule ask whether the iteration reflects a reusable orchestration gap, whether the rule would prevent/shorten/make it safer, whether it is already covered, whether it belongs in a reference rather than core, and whether it preserves simple workflows. Reject domain-specific history.
