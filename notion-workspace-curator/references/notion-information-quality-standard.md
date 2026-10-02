# Notion Information Quality Standard (NIQS) v1.0

**Effective:** 2026-09-25  
**Purpose:** Shared operating standard for readability, evidence quality, freshness, decision-state clarity, speed reading, language/audience fit, and maintenance across governed Notion pages.

## 1. Skill ownership

- `notion-workspace-curator` owns information architecture, page roles, first-screen/readability rules, navigation, freshness routing, language/audience presentation, dashboards, supersession routing, maintenance economics, and AI handoff structure.
- `notion-content-auditor` owns semantic correctness, completeness, claim typing, evidence-state correctness, contradictions, canonicality, freshness sufficiency, confidence/consequence escalation, and decision propagation.
- `research-method-curator` owns source hierarchy, research provenance, claim-to-source support, evidence archives/source cards, research freshness, uncertainty, research readiness, and source recheck triggers.
- Structural PASS never implies semantic PASS. Semantic PASS never implies research-method PASS. Research completion never implies implementation, benchmark, human review, clinical validation, purchase approval, or investment action.

## 2. Page Role taxonomy

Every important governed page should have one primary role:

`HUB` / `CURRENT STATE` / `RESEARCH` / `EVIDENCE ARCHIVE` / `SOURCE CARD` / `DECISION` / `EXECUTION` / `BENCHMARK` / `LEARNING` / `REFERENCE` / `ARCHIVE`.

A page may have secondary roles, but one canonical primary role should be obvious.

Each important page should state, explicitly or structurally:

> **Purpose:** what this page is canonical for, and what it must not be used as.

## 3. Three reading depths

### Fast Read — ~10 seconds
For active control, decision, research-synthesis, and current-state pages, the first visible screen should make clear:
- what this page is;
- current conclusion/state;
- freshness/reliability warning if material;
- next action or next route.

### Working Read — ~60 seconds
Provide:
- decision/current answer;
- 3–5 decisive facts;
- major uncertainty/blocker;
- next action;
- key evidence route.

### Evidence Read — deep
Move methodology, full tables, source cards, detailed calculations, historical audit notes, and long change logs below the working layer or into linked/collapsed evidence surfaces.

Do not force this pattern onto raw evidence, source cards, logs, or archive-only material when it reduces fidelity.

## 4. Evidence-state vocabulary

Use the narrowest valid label:

- `OBSERVED` — directly inspected artifact, screenshot, file, runtime, broker statement, tool result, or measured output.
- `PRIMARY SOURCE` — regulator, official documentation, issuer filing, guideline, original study, source repository.
- `SECONDARY SOURCE` — news, review, third-party analysis, sourced explainer.
- `USER-REPORTED` — supplied by the user but not independently verified.
- `CALCULATED` — derived mathematically from stated inputs.
- `INFERRED` — reasoned interpretation not directly demonstrated.
- `BENCHMARKED` — measured under a defined benchmark with preserved method/evidence.
- `HUMAN-VALIDATED` — reviewed/adjudicated by the required human expert.
- `UNKNOWN` — evidence absent or insufficient.
- `CONFLICTED` — material evidence disagrees and the conflict is unresolved.

Do not collapse these into a generic “verified” label.

## 5. Claim Type

Where ambiguity matters, distinguish:

`FACT` / `MEASUREMENT` / `CALCULATION` / `INTERPRETATION` / `ASSUMPTION` / `SCENARIO` / `DECISION` / `FORECAST` / `UNKNOWN`.

A calculation is not an observed fact. An interpretation is not a measurement. A scenario is not a forecast. A recommendation/decision is not evidence.

## 6. Freshness classes

| Class | Meaning | Default maintenance |
|---|---|---|
| F0 — Structural | architecture, naming rules, stable conventions | event-driven |
| F1 — Low volatility | foundational concepts, stable references | 6–12 months or trigger |
| F2 — Medium | research syntheses, educational resources | 3–6 months or trigger |
| F3 — High | AI models/providers, jobs, prices, financial fundamentals | monthly or before action |
| F4 — Very high | promotions, quotas, openings, market/availability state | live check before action |
| F5 — Safety/legal | clinical guidance, regulation, privacy, deployment rules | authoritative recheck before consequential action |

**Scheduled freshness ≠ action freshness.** A page can be within its review interval and still require a pre-action recheck.

## 7. Verification metadata

Consequential pages should expose, in content or structured fields:
- Page Role
- Primary Audience
- Freshness Class
- Last Verified
- What Was Verified
- What Was Not Verified
- Next Recheck Trigger
- Decision Readiness
- Evidence State where useful

Avoid ambiguous “Updated” dates that do not state what changed or what was checked.

## 8. Generic decision lifecycle

Use the lightest appropriate chain:

`DISCOVERED → RESEARCHED → EVIDENCE-COMPLETE → DECISION-READY → DECIDED → EXECUTING → VERIFIED → CLOSED`

Domain-specific gates may refine it:
- AI tools: Discovered → Verified → Trialed → Benchmarked → Adopted/Rejected.
- Purchase: Research → Quote/terms verified → Decision-ready → Bought → Delivery verified.
- Investment: Research → Current-source recheck → Thesis recorded → Action → Monitoring.
- Clinical/CDSS: Designed → Code written → Executed → Tests passed → Benchmark passed → Human review → Clinical validation.

Do not infer later states from earlier ones.

## 9. Confidence × Consequence escalation

Assess:
- **Confidence:** High / Medium / Low.
- **Consequence if wrong:** Low / Medium / High / Critical.

Rules:
- High confidence + low consequence: ordinary use.
- Medium confidence + high consequence: primary/authoritative verification required.
- Low confidence + high/critical consequence: block action until evidence improves.
- Critical consequence: never use secondary convenience evidence as the sole authority when a primary/official source should exist.

## 10. Source Authority Matrix

Default source ordering depends on domain.

### Clinical
Official guideline/regulator → systematic review → primary study → canonical textbook → secondary explainer.

### AI / software / providers
Official docs/API/repository → reproducible local test → independent benchmark → reputable analysis → community/social discovery.

### Finance
Broker/account evidence for personal account state → exchange/regulator/company filing → audited report → reputable financial press → commentary.

### Legal/regulatory
Primary law/regulator/circular/order → official guidance → authoritative legal analysis → reputable secondary reporting.

Preserve disagreements when authority, jurisdiction, date, or scope differs.

## 11. Update Impact Matrix

Classify a material update:

- `NO IMPACT` — archive/source history only.
- `METADATA` — dates/labels/source card only.
- `SYNTHESIS CHANGE` — update the research/synthesis page.
- `DECISION CHANGE` — update decision/current-state surfaces.
- `ARCHITECTURE CHANGE` — propagate to hubs/dependent control pages.
- `SAFETY-CRITICAL` — urgent propagation to affected decisions and blockers.

Do not propagate every minor update everywhere.

## 12. Supersession chains

Superseded pages should state:
- Superseded by
- Superseded on
- Reason
- Still useful for

Replacement pages should state what they supersede when material.

Do not silently rewrite historical provenance into present truth.

## 13. Current Truth vs Historical Truth

Use:
`Current Truth → Decision History → Evidence Archive`

A statement may have been correct at T0 and no longer be current at T1. Preserve both states with dates rather than erasing history.

## 14. Information density rules

For active parent/hub/control pages:
- normally no more than two visible control callouts before deeper content;
- no more than ~5 summary bullets before deeper detail unless necessary;
- keep next action visible;
- collapse dense historical/audit material;
- avoid duplicate route blocks;
- keep mobile-first content single-column and narrow.

Safety warnings and blocking constraints remain visible even when other history is collapsed.

## 15. Table rules

Use tables for real comparison, not paragraph storage.

Prefer compact decision-oriented columns such as:
`Metric | Current | Evidence State | Date | Action`

Move detailed source/provenance fields to source cards or deeper evidence tables when the first view becomes too wide.

## 16. Audience and Language Mode

Define the primary reader.

| Audience | Default language treatment |
|---|---|
| Technical owner | English technical terminology; Bengali reasoning/explanation when useful |
| Clinical professional | Standard medical terms preserved; Bengali/English explanation by context |
| Patient/public | Plain Bengali by default; English only where needed |
| Business/finance personal | Bengali explanation + standard English financial terminology |
| Official/source evidence | Preserve source language and exact terminology |
| External professional deliverable | English unless audience requires otherwise |

Do not mechanically translate database/property names, code, commands, paths, schemas, metrics, official titles, drug names, guideline names, or error messages.

## 17. Staleness Dashboard

Governed workspaces should be able to surface:
- High Risk — Stale
- Needs Primary Source
- Decision Active — Recheck Required
- Research Complete — Benchmark Pending
- Evidence Missing
- Human Review Pending
- Superseded but still linked
- Contradiction Open

Use structured fields/views when practical; do not rely on memory or prose-only review.

## 18. Evidence Debt

Track unresolved proof requirements separately from ordinary tasks.

Minimum fields:
- Evidence Debt
- Decision affected
- Severity
- Required proof
- Owner
- Trigger/deadline
- State
- Canonical destination

Do not mark a parent “complete” merely because the debt is documented.

## 19. Maintenance Cost

Classify live pages:
- Self-maintaining / structural
- Low maintenance
- Periodic maintenance
- Event-driven
- High-maintenance live intelligence

A high-maintenance page with low decision value should usually be reduced, archived, or converted to trigger-based monitoring.

## 20. Decision Value Matrix

Evaluate:
- Information value: High / Low.
- Decision value: High / Low.

Rules:
- High information + high decision: maintain aggressively.
- High information + low decision: reference/archive.
- Low information + high decision: gather evidence.
- Low information + low decision: archive/delete candidate only after governance review.

## 21. Change Delta block

Frequently updated pages should expose:
- NEW
- CHANGED
- UNCHANGED
- REMOVED
- DECISION IMPACT

Do not make readers reconstruct the delta from the full page.

## 22. Research vs Monitoring

- **Research:** establishes what is true and what conclusion is justified.
- **Monitoring:** checks whether material truth changed.

Once an area is mature, prefer delta monitoring over repeatedly restarting broad research.

## 23. AI-safe handoff block

Important control pages intended for reuse by AI systems should expose:
- Canonical state
- Do not change / protected items
- Current next action
- Open blockers
- Allowed sources
- Forbidden assumptions
- Validation boundary

This block is for state transfer, not permission to bypass evidence or safety gates.

## 24. Contradiction as a first-class state

Use `CONFLICTED` / `CONTRADICTION OPEN` when material evidence disagrees.

Record:
- competing claims;
- evidence/source for each;
- why the conflict matters;
- what would resolve it;
- whether action is blocked.

Do not force false consensus.

## 25. Uncertainty budget

For major decisions, explicitly separate:
- Known
- Probable / supported inference
- Unknown
- Blocked

This can replace vague confidence prose and makes the next evidence need obvious.

## 26. Migration / rollout rule

Do **not** mechanically rewrite the entire workspace.

Priority:
1. governing hubs and control surfaces;
2. active decision pages;
3. high-risk/high-freshness research;
4. recurring operational pages;
5. dormant/archive pages only when reactivated.

Preserve raw evidence and historical content. Apply the standard through audit → minimal repair → re-fetch/re-audit.

## 27. Shared completion rule

A NIQS upgrade is complete only when:
- role/audience/read-depth requirements are appropriate to the page;
- evidence/claim/freshness states are not overstated;
- next action and recheck triggers are explicit where needed;
- current vs historical truth is preserved;
- contradictions/evidence debts remain visible;
- structural edits are re-fetched;
- semantic/evidence-method claims are delegated to the owning skill instead of inferred from structure.

## 28. 26-improvement coverage map

The standard covers:
1 reading depths; 2 evidence vocabulary; 3 freshness matrix; 4 Last Verified/Next Recheck; 5 Page Role; 6 decision lifecycle; 7 confidence×consequence; 8 source authority; 9 claim type; 10 update impact; 11 supersession; 12 current vs historical truth; 13 information density; 14 table rules; 15 purpose line; 16 bilingual/audience convention; 17 audience; 18 staleness dashboard; 19 evidence debt; 20 maintenance cost; 21 decision value; 22 change delta; 23 research vs monitoring; 24 AI-safe handoff; 25 contradiction state; 26 uncertainty budget.

