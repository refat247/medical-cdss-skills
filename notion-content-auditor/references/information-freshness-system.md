# Information Freshness System

This reference defines the permanent operating model for keeping a Notion knowledge system current without erasing historical truth.

## 1. Ownership

- `notion-content-auditor` owns semantic freshness, current-vs-historical truth, evidence-state correctness, contradiction handling, change-impact reconciliation and decision propagation.
- `notion-workspace-curator` owns structural placement, canonical routing, view/dashboard usability and supersession navigation.
- `research-method-curator` owns source hierarchy, research-method design and claim-to-source sufficiency.

Do not collapse these specialist roles into one generic maintenance pass.

## 2. Historical preservation

Historical/source-faithful material is immutable by default. When current evidence changes:

1. preserve the prior dated statement;
2. add a dated current-state layer;
3. explain exactly why the state changed;
4. reconcile decision/action impact;
5. record unresolved gates and next trigger;
6. update only the current canonical decision surface.

Minimum delta record:

`DATE → PREVIOUS STATE → CURRENT STATE → WHY/EVIDENCE → IMPACT → UNRESOLVED GATE → CANONICAL TARGET REPAIRED`

Never use an undated overwrite that makes it impossible to reconstruct what was believed earlier.

## 3. Freshness-state model

Recommended `Freshness State` options:

- `Current Verified` — current decision-relevant claims were verified to an explicit as-of date.
- `Review Due` — previously verified, but the next recheck date has arrived or an expiry/deadline is imminent.
- `Needs Revalidation` — decision-relevant current truth is not sufficiently current.
- `Conflicting` — material sources disagree or a prior canonical statement conflicts with newer evidence.
- `Superseded / Historical` — retained for provenance; not current operating truth.
- `Evergreen / Not Required` — revalidation is not routinely required except when embedded volatile claims change.
- `Unknown` — freshness status cannot yet be established.

Recency alone never proves `Current Verified`.

## 4. Structured-field contract

Use structured fields in the existing central audit/freshness registry rather than creating a parallel database unless the existing registry cannot represent the workflow.

Recommended fields:

| Field | Type | Purpose |
|---|---|---|
| Freshness State | Select | Current freshness classification |
| Last Verified | Date | Last date current truth was externally/authoritatively verified |
| Next Recheck | Date | Next planned revalidation point |
| Freshness Trigger | Select | Why revalidation was opened |
| Needs Recheck | Checkbox | Legacy/general recheck gate and optional queue filter |
| Evidence State | Select | Current evidence sufficiency/conflict |
| Canonical State / Duplicate Review | Select | Canonicality and duplicate handling |
| Finding Summary | Text | Compact current state, impact and residual uncertainty |
| Source URL | URL | Canonical target or source route |

Recommended `Freshness Trigger` options:

- `Scheduled Watch Delta`
- `Official Source Change`
- `Expiry / Deadline`
- `Price / Plan Change`
- `Model / Product Change`
- `Job / Availability Change`
- `Policy / Regulation Change`
- `Conflicting Evidence`
- `Decision Use`
- `Manual Request`
- `Periodic Review`
- `Other`

Do not bulk-fill unsupported values. Historical rows may remain blank until they become decision-relevant.

## 5. Operating view

Maintain a compact view named `Freshness — Needs Review`.

Default-filter the view to:
- `Freshness State` = `Review Due`;
- `Freshness State` = `Needs Revalidation`;
- `Freshness State` = `Conflicting`.

Expose `Needs Recheck` as a **quick filter**, not as a default OR condition when a legacy registry already has broad historical recheck flags. This prevents old audit debt from flooding the prospective current-freshness queue while still making legacy rows one click away when deliberately reviewing them.

Show at minimum:
- Page / Scope
- Parent Area
- Freshness State
- Evidence State
- Freshness Trigger
- Last Verified
- Next Recheck
- Needs Recheck
- Disposition
- Finding Summary
- Source URL

Sort by `Next Recheck` ascending, then `Last Verified` ascending when the view engine supports it.

This view is the normal review queue. Do not use multi-database SQL as the daily operating backbone.

## 6. Trigger policy

Open/reopen revalidation when:

1. a scheduled watch produces a material delta;
2. an official/primary source changes or contradicts current KOS truth;
3. a deadline, expiry, promotion, model route, job opening, product availability, policy or price reaches a review point;
4. conflicting evidence appears;
5. an archived/historical page becomes decision-relevant again;
6. a downstream decision depends on Unknown / Needs Revalidation / Conflicting evidence;
7. the user explicitly asks for current verification;
8. a planned periodic review becomes due.

Do not reopen the entire workspace because one trigger fires. Reopen the affected canonical target and its direct downstream decisions.

## 7. Scheduled-watch integration contract

Every operational watch with a fixed canonical target follows this contract.

### Material-delta run
1. Read the previous successful baseline.
2. Verify only material changes.
3. Update the fixed canonical page using `Previous → Current → Evidence → Impact → Unresolved`.
4. Preserve prior dated updates.
5. Refetch and verify the canonical write.
6. Record in the control heartbeat:
   - canonical target;
   - material-delta count;
   - freshness action (`REVALIDATED`, `REPAIRED`, `CONFLICT`, or `UNRESOLVED`);
   - affected freshness target;
   - unresolved gate(s);
   - next baseline/next recheck when meaningful.
7. Update the central freshness registry row when a matching governed row exists; otherwise leave a deterministic handoff for the health/repair run rather than creating an uncontrolled parallel registry row.

### Zero-delta run
- Do not change the canonical content merely to create activity.
- Do not manufacture a fresh verification date unless the relevant current claims were actually revalidated.
- Heartbeat may record `NO DELTA` and `Freshness Action = NONE`.

## 8. Health/repair integration

The Scheduled Runs Health & Repair process verifies:
- every material delta reached the fixed canonical target;
- the historical prior state remains present;
- canonical write was refetched and verified;
- freshness handoff fields are populated consistently;
- unresolved gates were not silently closed;
- central freshness fields were updated when a matching registry row exists;
- no duplicate canonical page or duplicate handoff was created.

A missing freshness propagation is a control defect even if the research finding itself was correct.

## 9. Current-vs-historical repair pattern

Preferred current canonical insertion:

### YYYY-MM-DD — Current update
- **Previous state:** ...
- **Current state:** ...
- **Why/evidence:** ...
- **Impact:** ...
- **Unresolved:** ...
- **Next trigger/recheck:** ...

Do not delete the older dated section unless it is a transcription/provenance error and deletion is explicitly authorized.

## 10. Closure criteria

A freshness task may be marked complete only when:

- scope/trigger is explicit;
- current evidence was retrieved where required;
- previous and current states were compared;
- impact on decisions/actions was reconciled;
- current canonical content was repaired or left explicitly unresolved;
- historical provenance remains readable;
- affected structured fields were updated where applicable;
- write was refetched and verified;
- next trigger/recheck is recorded when meaningful;
- no false workspace-wide completeness claim was made.

## 11. Heavy-audit boundary

Notion is the operating workspace, not the exhaustive multi-database audit engine.

For daily/weekly freshness work:
- use structured fields;
- use filtered views;
- use deterministic canonical targets and handoffs.

For genuinely exhaustive cross-database counts or full physical inventory, use an export/script or another external audit method when required. Do not force multi-database SQL into the daily workflow.
