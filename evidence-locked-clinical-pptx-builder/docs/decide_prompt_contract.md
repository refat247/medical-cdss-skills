# DECIDE scenario and prompt contract (v2.3.0)

For new case-based projects, keep these fields separate in the Master Case
Library and prompt review ledger:

- `source_derived_scenario`: the minimum locked-source facts needed for the decision;
- `case_query_setup`: one neutral learner decision question ending in `?`;
- `prompt_text`: the scenario, one space, then the question;
- `expected_answer` and `withheld_decision_text`: revealed only after commitment.

Reject learner-facing stems containing source/pipeline terms such as
"source-defined branch" or "source-supported decision". Reject incomplete
clauses, stranded action nouns, extremely short non-decision stems, and
recommendation predicates in the scenario. A neutral question such as
"Should a further measurement be considered?" is allowed; the source's
declarative recommendation must remain withheld.

Run `python scripts/prompt_semantics_validator.py <ledger.csv>`. A deterministic
PASS does not certify clinical fidelity. A reviewer must compare each scenario,
question, expected answer, source locator, and correction state against the
locked source and record all three semantic statuses as `PASS` only when
adjudicated. Existing v2.2.x ledgers without `source_derived_scenario` remain
readable; migrate them before new builds so scenario-to-prompt drift is checked.

Repair at the earliest valid layer and rebuild dependent specs, slide maps,
slides, and rendered set. Do not change clinical values or recommendation
polarity to make a prompt read smoothly without approved source support.
