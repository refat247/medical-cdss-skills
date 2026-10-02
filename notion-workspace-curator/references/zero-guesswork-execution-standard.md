# Zero-Guesswork Execution Standard

## Why this exists

A research page can look operational because it contains a task, checklist, database row, sample size, or next-action label while still failing to tell the operator exactly how to perform the work. The Curator must detect this research-to-execution gap.

## Core rule

**Executable does not mean a task/register exists. Executable means another competent person can perform the work from the Notion page alone, consistently, without inventing methodology.**

Apply this standard whenever research says `Do`, `Test`, `Verify`, `Audit`, `Pilot`, `Interview`, `Observe`, `Benchmark`, `Collect N`, `Mystery shop`, `Validate`, or similar.

## Required execution chain

A complete execution instrument should define, as applicable:

1. Objective — what the execution is intended to establish.
2. Subject/sample — who, what, where, inclusion/exclusion and assigned unit.
3. Exact protocol/script — ordered steps the operator follows.
4. Exact questions/observations/measurements — not merely a topic label.
5. Standardized response fields — units, allowed values and free-text boundaries.
6. Evidence requirements — what proof is captured and what is prohibited.
7. Missing/refusal/substitution rules — what to do when the planned observation cannot be obtained.
8. Safety, ethics, privacy and legal constraints where relevant.
9. QA criteria — what must be true before the item is accepted.
10. Completion criterion — when the execution unit is genuinely complete.
11. Downstream decision — what the evidence can unlock, block or update.

Not every action requires a database. A concise protocol/checklist is enough when the work is simple. Use a register when multiple independent execution units need row-level tracking.

## Source-silence rule

If the source research does not specify a required operational detail, do not fill it with plausible fiction. Mark it explicitly:

`UNRESOLVED — SOURCE DOES NOT SPECIFY`

If an operational choice must be made to proceed, document it as an **operational freeze/assumption**, identify who approved it, and keep it distinct from source-derived methodology.

## Execution maturity states

Never collapse these stages:

`Task exists → Instrument exists → Instrument frozen → Execution started → Evidence captured → QA passed → Decision-ready`

Definitions:

- **Task exists:** a future action is identified.
- **Instrument exists:** protocol/questions/measurements/evidence rules are documented.
- **Instrument frozen:** unresolved choices are resolved and the version to be used is locked.
- **Execution started:** real collection/testing has begun.
- **Evidence captured:** required raw proof/data is present.
- **QA passed:** completeness, units, protocol adherence and evidence quality were checked.
- **Decision-ready:** prerequisites for the stated downstream decision are satisfied. This does not imply clinical/legal approval unless those gates separately passed.

## Zero-guesswork test

Before declaring an execution gap repaired, ask:

> Could a competent person who did not participate in the research open this page, perform the task consistently, know exactly what to ask/observe/measure, record missing/refused/substituted cases correctly, submit the required evidence, and know when the item passes QA — without asking the researcher to explain the method?

If the answer is no, the gap remains open.

## Common failure patterns

- `Collect 33 observations` with 33 rows but no observation instrument.
- `Interview 50 people` with a sample register but no questionnaire, inclusion rule or response coding.
- `Run 30 benchmark queries` without frozen queries, qrels/rubric, metrics or error taxonomy.
- `Verify suppliers` without required quote fields, terms, evidence or comparison rule.
- `Pilot the workflow` without scenario, success criteria, failure capture or QA.
- `Human review required` without reviewer role, review packet, rubric or sign-off evidence.

## Curator Change Summary requirement

When this rule causes a research page to be repaired, the page's Curator Change Summary must state the actual maturity reached. Do not write `execution-ready` if only the task/register was created. Explicitly record unresolved instrument freezes or evidence-dependent fields.

## Origin

Added 2026-08-28 after the Lakshmipur mystery-shopping audit showed that creating a 33-observation register did not, by itself, specify what the mystery shopper should observe, ask, measure or submit as evidence.