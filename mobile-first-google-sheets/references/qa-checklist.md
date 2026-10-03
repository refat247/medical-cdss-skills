# Mobile-First QA Checklist

Binary PASS/FAIL unless marked N/A.

## Workflow
- [ ] Primary operational tab is first/leftmost visible tab.
- [ ] Sole editable source is explicit.
- [ ] Tab order follows frequency and workflow.

## Viewport
- [ ] Routine entry avoids unnecessary horizontal scrolling.
- [ ] Essential identifier/context remains visible or repeated.
- [ ] Frozen region is minimal.

## Entry integrity
- [ ] Required inputs are obvious.
- [ ] Blank remains distinct from zero.
- [ ] Partial entry is detectable.
- [ ] Future records are not overdue/pending.
- [ ] Off-day/not-applicable records are not treated as missing.
- [ ] Backfill behavior is explicit.
- [ ] Impossible values are rejected where appropriate.
- [ ] Plausible outliers warn rather than silently reject.

## Visual/accessibility
- [ ] Color is paired with text/symbol/status.
- [ ] Warning colors are reserved for actionable states.
- [ ] Images are not used when text/symbols suffice.

## Navigation/analysis
- [ ] Current-record navigation is efficient.
- [ ] Long datasets have period landmarks/navigation.
- [ ] Mobile dashboard, if present, is compact.

## Performance
- [ ] Conditional formatting is scoped and minimal.
- [ ] Volatile functions are centralized/minimized.
- [ ] Repeated computations are centralized where practical.
- [ ] Full-column/heavy formulas are avoided when bounded ranges suffice.

## Safety/protection
- [ ] Backend/configuration surfaces are protected or clearly non-editable.
- [ ] Formula-error scan is clean.
- [ ] Core analytics reconcile after repair.

## Google-native conversion
- [ ] Intended operating timezone verified after conversion.
- [ ] Native tab order verified.
- [ ] Native freeze verified.
- [ ] Native protection and intended unprotected input ranges verified.
- [ ] Native validation verified.
- [ ] Conditional-format rules reviewed for stale/duplicated/obsolete rules.
- [ ] Key formulas/KPIs, blanks, and true zeros re-read and verified.
- [ ] Merged ranges inspected where converted cells are blank/unwritable/unexpected.
- [ ] Backend/config/audit visibility matches the intended workflow.
- [ ] Navigation tested as a working action, not only displayed instructions.
- [ ] Material native mutations were followed by a re-read of affected state.
- [ ] Android/mobile rendering verified.

## Closure state
- [ ] Lifecycle state is reported explicitly: SOURCE VALIDATED / CONVERTED / NATIVE AUDITED / NATIVE REPAIRED / RE-AUDITED / MOBILE VERIFIED.
- [ ] MOBILE VERIFIED is used only when applicable native checks passed.

If native access is unavailable, mark this section `NATIVE GOOGLE SHEETS — UNVERIFIED`; do not convert it to PASS.