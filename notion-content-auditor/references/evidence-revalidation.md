# Evidence Revalidation

L3 checks whether decision-relevant external claims remain true **as of the audit date** and what any intervening change means for the older note.

## Trigger

Volatile/time-sensitive; high-stakes; conflicting sources; decision-critical; weak provenance with meaningful consequence; explicit current-verification request; or any older note whose claims could have materially changed between its original date and the audit date.

## Source hierarchy

1. Primary/official source or authoritative standard.
2. Strong secondary source with transparent sourcing.
3. Community/social evidence for experience, failure modes, sentiment and discovery.

Do not promote anecdotes to verified general facts without corroboration.

## Temporal comparison rule

For a note written at `T0` and audited at `T1`, investigate material developments during `T0 → T1`. Do not assume that an old fact is stale, and do not assume that silence means unchanged. Search specifically for changes relevant to the note's claims and decisions.

## Required change-impact record

For every material current-evidence change, record:
- **Original state (T0):** what the note said or concluded and when.
- **Current evidence (T1):** what is now supported, source URL, source/effective date and audit as-of date.
- **Delta:** exactly what changed; distinguish new fact, correction, supersession, reversal, expansion, narrowing, deprecation or no material change.
- **Impact:** how the delta affects the previous conclusion, recommendation, risk, priority, ranking, workflow, decision or planned action.
- **Decision status:** `UNCHANGED`, `STRENGTHENED`, `WEAKENED`, `MODIFIED`, `SUPERSEDED`, `REVERSED`, `INVALIDATED`, or `UNKNOWN`.
- **Propagation:** which canonical page(s), decision(s), task(s), status fields or downstream notes require an update.
- **Residual uncertainty / next review trigger.**

## Repair rule

Historical text must remain historically faithful. Do not silently overwrite what was believed at T0. Add or update a clearly separated **Current update / What changed / Impact on prior conclusion** section, or supersede the old page when a separate canonical page is cleaner. A current operational page must be substantively corrected, not merely labelled `Needs Revalidation`.

## Output standard

A successful L3 audit answers four questions:
1. What did we believe then?
2. What is supported now?
3. What changed between then and now?
4. What does that change mean for the previous decision or action?

## Freshness & Current-Evidence Gate

Classify content before revalidation:
1. **Current / operational content:** verify materially volatile claims against evidence current to the audit date before treating the content as current, canonical, or audit-complete.
2. **Historical / source-faithful content:** preserve what the historical source said. Add a separate current-status, supersession, or correction layer when present truth differs.
3. **Evergreen theory / methodology:** validate against the relevant authoritative source or edition; revalidate only volatile embedded components.

For decision-relevant current pages, do not stop at `Needs Revalidation` when evidence retrieval is feasible.

Required flow:
`READ -> identify volatile claims -> retrieve current evidence -> compare -> update substantive Notion content where needed -> record as-of date + provenance -> preserve historical claim/context -> re-fetch -> verify`.

Every refreshed current-evidence claim should record `As of: YYYY-MM-DD`.

Retroactive reopening rule: `prior L2 closure + current decision relevance + volatile unresolved claim = L3 REOPEN REQUIRED`.
