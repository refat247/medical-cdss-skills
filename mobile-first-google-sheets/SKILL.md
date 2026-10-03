---
name: mobile-first-google-sheets
version: 1.2.1
description: Design, audit, repair, and QA Google Sheets workflows for phone-first use, especially Android. Prioritizes low-friction data entry, narrow viewports, single-source-of-truth architecture, tab-order UX, mobile-safe navigation, validation, status semantics, performance, and native Google Sheets conversion checks.
---

# Mobile-First Google Sheets

## 1. Operating Contract

Use this skill when the user wants to create, redesign, audit, repair, or optimize a Google Sheets workflow primarily used on a phone or tablet.

Primary objective:

`fast correct entry → persistent context → immediate validation → compact review → protected backend`

Do not merely make a desktop spreadsheet smaller. Design around the mobile interaction model.

## 2. Invocation Scope and Device-Class Gate

At the start of every task, classify both dimensions below before designing or judging the workbook.

### Invocation scope
Choose exactly one primary scope:
- `BUILD` — create a new workbook or a new operational surface from requirements.
- `AUDIT` — inspect and report defects without modifying the artifact.
- `AUDIT_REPAIR_REAUDIT` — inspect, make the smallest safe repairs, then independently re-check the repaired artifact.

If the user asks to “fix,” “improve,” “optimize,” “repair,” “make mobile-first,” or equivalent and provides an existing workbook, default to `AUDIT_REPAIR_REAUDIT` unless they explicitly request read-only analysis.

Do not confuse BUILD with REPAIR. A mature workbook with valid semantics should normally be repaired conservatively rather than rebuilt.

### Device-use class
Classify the workbook as:
- `MOBILE-PRIMARY` — routine creation/entry/review occurs mainly on a phone/tablet. Apply the full mobile-first standard.
- `MOBILE-SECONDARY` — desktop is the main authoring/analysis surface, but common actions must remain usable on mobile. Optimize the frequent mobile path without degrading justified desktop complexity.
- `DESKTOP-PRIMARY` — the workbook is legitimately wide/complex and mobile use is occasional. Do not force narrow mobile architecture across the whole workbook; create a compact mobile companion surface only when it materially helps.

Base the classification on the user's stated workflow. If not stated, infer cautiously from the requested task and artifact; ask only when the classification would materially change the design.

Every audit/build report should state the selected scope and device-use class. Never label a DESKTOP-PRIMARY workbook defective merely because its full analytical surface is wide.

## 3. Non-Negotiable Principles

1. **Primary action first.** The highest-frequency operational sheet is the first/leftmost visible tab. For data-entry systems, the entry sheet normally comes first.
2. **Tab order is UX architecture.** Order visible tabs by: `ACT → ORIENT → CHECK → NAVIGATE → ANALYZE → ADMINISTER`. Put backend/config/governance last or hide them when safe.
3. **Single editable source of truth.** Never create two independent entry surfaces for the same record unless there is a reliable write-back mechanism and conflict policy.
4. **Narrow viewport.** Prefer 3–6 essential visible columns. Avoid routine horizontal scrolling. If wider data are unavoidable, split operational entry from backend storage.
5. **Persistent context.** Keep date/ID/category visible. Repeat identifiers when that is safer than depending on imported freeze behavior.
6. **Minimal freezing.** Freeze only essential rows/columns; frozen width consumes phone screen space.
7. **Thumb-efficient entry.** Minimize taps, dropdowns, checkboxes, modal interactions, and sheet switching.
8. **Blank is not zero.** Preserve true zero distinctly from unknown/not entered/not applicable.
9. **Automatic completeness.** Derive COMPLETE/PARTIAL/MISSING from required fields whenever possible; do not add manual completion taps that can disagree with the data.
10. **Warnings before rejection for plausible outliers.** Reject impossible formats; highlight plausible-but-unusual values for review.
11. **Color is semantic, not decorative.** Pair color with text/symbol/status so meaning is not color-dependent.
12. **Progressive disclosure.** Operational surfaces first; detailed analytics, configuration, provenance, and audit surfaces later.
13. **Mobile performance budget.** Avoid excessive conditional formatting, volatile formulas, full-column calculations, duplicated computations, images, and unnecessary charts.
14. **Native Google Sheets pass required.** XLSX generation/import is not final verification. A converted workbook must be re-read in native Google Sheets before closure. Verify timezone, merged ranges, freeze state, protection, validation, conditional formatting, formulas/KPIs, tab order, hidden sheets, navigation, and mobile rendering when native access is available.
15. **Do not over-engineer.** Every feature must reduce error, taps, scrolling, or cognitive load.

## 4. Default Tab-Order Logic

For operational trackers, prefer:

1. primary entry/action
2. current/today locator or current work queue
3. compact mobile dashboard/status
4. historical/current-period navigation
5. short-horizon analysis
6. long-horizon analysis
7. full desktop dashboard/reporting
8. instructions/start-here
9. derived database/backend
10. configuration/reference tables
11. audit/provenance logs

Hide protected backend/config/audit sheets when hiding does not impair the workflow. Never hide the only recovery/documentation path.

## 5. Mobile Entry Surface Standard

Before building, identify:
- primary device/platform;
- primary action;
- record unit;
- required fields;
- frequency of entry;
- whether entry is prospective, retrospective, or both;
- off-day/not-applicable semantics;
- correction/backfill workflow;
- collaboration roles;
- whether Google Sheets native conversion is expected.

Then design the entry surface so:
- the user can identify the current record without horizontal scrolling;
- only editable cells look editable;
- derived cells are visually de-emphasized or protected;
- required fields fit within a phone-friendly width where feasible;
- dates/IDs repeat when needed for context;
- row heights and text remain legible without excessive zooming;
- the user can recover from partial entry safely.

## 6. Status Semantics

Use explicit states appropriate to the workflow, such as:
- `COMPLETE`
- `PARTIAL — CHECK ENTRY`
- `PENDING`
- `FUTURE`
- `NOT SCHEDULED`
- `BACKFILLED`
- `NOT APPLICABLE`

Do not classify future expected records as overdue/pending. Do not classify scheduled off-days as missing. If a normally off-day record is later entered, preserve the distinction between routine compliance and data coverage.

## 7. Navigation Standard

Prefer, in order:
1. correct tab order;
2. compact current/today locator;
3. repeated record identifiers;
4. minimal native freeze;
5. month/period landmarks or navigation sheet;
6. filters only when they reduce taps on the target mobile platform.

Do not rely on desktop-only filter views for an Android-first workflow.

## 8. Validation and Error Prevention

For each input field classify constraints as:
- impossible → reject;
- unusual but plausible → warn/highlight;
- optional/unknown → allow blank;
- genuine zero → preserve as numeric zero.

Use automatic completeness checks for multi-field records. Highlight missing required cells only after a record has been started, unless the user explicitly wants all missing future fields highlighted.

## 9. Visual Semantics

Use restrained semantic formatting:
- category identity: symbol/text + consistent color;
- status: short label + restrained fill;
- editable cells: clear but not visually dominant;
- warnings: amber/red only for action-worthy conditions;
- off-day/not-applicable: neutral gray;
- completed: green or equivalent positive state.

Avoid images when symbols/text communicate the same information with less space and load.

## 10. Mobile Dashboard Standard

Create a separate compact mobile dashboard only when it reduces navigation. Prefer 4–8 decision-relevant KPIs, current status, and concise exceptions. Avoid desktop-scale chart walls. Keep detailed charts in a secondary dashboard.

## 11. Performance Rules

Use closed/bounded ranges when practical. Centralize repeated calculations. Use volatile functions such as `TODAY()`/`NOW()` sparingly; prefer one helper cell referenced elsewhere. Keep conditional-format rules few, non-overlapping, and scoped to necessary ranges. Avoid duplicated formulas and excessive imported/external data dependencies in the operational surface.

Read `references/google-sheets-mobile-capabilities.md` for platform-specific evidence and limitations.

## 12. Google Sheets Conversion Gate

When an XLSX is intended for Google Sheets:

**Pre-conversion:**
- use portable formulas;
- minimize Excel-only constructs;
- keep data validation simple;
- make the layout usable even if freeze/protection does not survive conversion.

**Post-conversion native audit:**
- confirm spreadsheet timezone matches the intended operating timezone; never assume the import default is correct;
- confirm first visible sheet/tab order;
- confirm freeze rows/columns survived and remain minimal;
- confirm editable vs protected ranges using native Sheets protection;
- confirm validation/dropdowns/checkboxes;
- enumerate/review conditional-format rules for stale, duplicated, or semantically obsolete rules;
- confirm formulas, key KPIs, blanks, and true zeros by re-reading representative cells;
- inspect merged ranges when a target cell is unexpectedly blank, unwritable, or behaves differently after conversion;
- confirm hidden/backend sheets and recovery/documentation access;
- test navigation as an action, not merely as displayed instructions or row numbers;
- test Android/mobile rendering;
- test partial entry, correction, backfill, future dates, and off-days.

**Native mutation verification:**
- treat a successful API/tool response as evidence that a request was accepted, not proof that the workbook behaves correctly;
- after each material native repair, re-read the affected cells/properties/rules and verify the intended effective state;
- if a write reports success but the visible/effective value is still wrong or blank, inspect protection, merged ranges, formulas, and formatting before retrying;
- keep native protections/hiding/navigation separate from source-XLSX verification.

Use the lifecycle:
`SOURCE VALIDATED → CONVERTED → NATIVE AUDITED → NATIVE REPAIRED → RE-AUDITED → MOBILE VERIFIED`

`MOBILE VERIFIED` requires applicable native checks to pass; a clean formula scan alone is insufficient.

If native Google Sheets cannot be accessed, label this gate `NATIVE GOOGLE SHEETS — UNVERIFIED`; do not claim it passed.

## 13. Audit → Repair → Re-Audit Workflow

Audit these dimensions:
1. `PRIMARY ACTION / TAB ORDER`
2. `VIEWPORT / HORIZONTAL SCROLL`
3. `CONTEXT PERSISTENCE`
4. `ENTRY FRICTION`
5. `SINGLE SOURCE OF TRUTH`
6. `VALIDATION / ZERO / BLANK SEMANTICS`
7. `COMPLETENESS / ERROR RECOVERY`
8. `STATUS / SCHEDULE SEMANTICS`
9. `VISUAL SEMANTICS / ACCESSIBILITY`
10. `NAVIGATION`
11. `MOBILE DASHBOARD`
12. `PERFORMANCE`
13. `PROTECTION / BACKEND SAFETY`
14. `GOOGLE SHEETS CONVERSION / NATIVE STATE`
15. `REGRESSION / FORMULA INTEGRITY`

For each issue report: severity, evidence, mobile impact, smallest safe repair, and verification method.

Repair conservatively. Preserve valid formulas, source data, analytics, provenance, and business semantics unless the user explicitly authorizes a redesign.

Re-audit the repaired artifact. A design proposal is not a completed repair.

## 14. QA Gates

A mobile-first workbook can be called `MOBILE-READY` only when applicable gates pass:
- primary action is first and obvious;
- routine entry does not require avoidable horizontal scrolling;
- current record context remains visible/recoverable;
- blank/zero semantics are correct;
- partial records are detectable;
- future/off-day states are not mislabeled;
- backend formulas remain intact;
- formula-error scan is clean;
- mobile dashboard is compact if present;
- intended operating timezone is verified in native Sheets;
- converted merge/freeze/protection/conditional-format/navigation state is verified where applicable;
- material native repairs have been re-read after mutation;
- native Google Sheets state is verified, or explicitly marked unverified.

Do not use `MOBILE VERIFIED` when the native gate is unverified or when only source/XLSX checks have passed.

Use `references/qa-checklist.md` for the binary checklist.

## 15. Output Discipline

When auditing: lead with material defects and highest-value repairs.
When building: state the intended mobile workflow and which sheet is the sole editable surface.
When delivering XLSX for Google Sheets: explicitly separate `PACKAGE/XLSX VERIFIED` from `NATIVE GOOGLE SHEETS VERIFIED`.
When a native-only action remains (e.g., protected ranges after conversion), provide the exact one-time step.

## 16. Release and Version Governance

Canonical version: `metadata.version` in this file.
Mirror the same version in `README.md`, `CHANGELOG.md`, and `agents/openai.yaml`.
Use SemVer 2.0.0 and Keep a Changelog conventions.
Run `python scripts/bump_version.py --verify` before packaging.
Run all tests; release requires 100% pass.
Keep states separate:
- `PACKAGE BUILT`
- `PACKAGE VERIFIED`
- `INSTALLED`
- `RUNTIME ACTIVATED`
- `SMOKE TESTED`
- `BEHAVIOR VERIFIED`
- `GIT SYNC VERIFIED`
- `NOTION ARCHIVE VERIFIED`

Never infer one state from another.

## 17. Manual Protocol Loading

If native personal-skill activation is unavailable/unreliable, `MANUAL_ACTIVATION.md` is a first-class fallback. Manual loading does not prove runtime activation.

## 18. Do Not Do

Do not:
- put documentation before the primary operational tab by default;
- create duplicate editable entry surfaces without write-back/conflict control;
- use color as the only semantic signal;
- convert blanks to zero;
- mark future rows pending;
- treat off-days as missing;
- add checkboxes/dropdowns just because Sheets supports them;
- depend on freeze surviving XLSX import;
- claim Google-native protection/freeze passed without native verification;
- assume the imported spreadsheet timezone is correct;
- assume a successful native write request proves the effective sheet state;
- ignore merged ranges when a post-conversion target cell remains blank or unwritable;
- leave stale conditional-format rules merely because they survived conversion;
- overload phone dashboards with desktop charts;
- use broad conditional formatting when a scoped rule works;
- silently change business or clinical semantics while optimizing UX.