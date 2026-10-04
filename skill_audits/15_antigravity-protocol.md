# 15 · antigravity-protocol (v1.0.0) — Independent Audit

**Tier:** Platform/meta (orthogonal to the clinical goal) · **Type:** prompt-only, ~710 words · **Code/tests:** none

| Goal fit | Safety | Tests | Docs accuracy | Portability | **Overall** |
|:-:|:-:|:-:|:-:|:-:|:-:|
| n/a | B | n/a | B | D | **B-** as a protocol |

## What it does well
- Clear, usable directives: targeted reads, chunk-based edits, no exploratory guessing, no filler; three modes (investigate / fast path / strict plan) with an approval gate for multi-file work `[C]`.
- Declares mutual exclusion with `ultimate-protocol`.

## Findings
| ID | Sev | Ev | Finding | Fix |
|---|---|---|---|---|
| A1 | Medium | C | **Over-broad trigger:** "Use this skill ALWAYS whenever the user asks to write code, modify files, fix bugs, plan…". In this suite it would also activate while running clinical pipeline commands. | Narrow to "interactive coding sessions"; exclude autonomous/pipeline runs. |
| A2 | Medium | C | **Mode C requires halting for approval**, which stalls unattended runs (e.g. orchestrator `auto`). | State that approval gates apply only to interactive sessions. |
| A3 | Medium | C | **Host-specific:** tool names (`replace_file_content`, `view_file`, `grep_search`, `find_by_name`) and an `<appDataDir>\brain\…` Windows artifact path exist only in Antigravity; on any other agent they are dead instructions. | Describe behaviours generically, list tool names as an appendix. |
| A4 | Low | C | Mutual exclusion is prose-only; nothing detects both being active. | Documented tie-break is enough; add a one-line precedence statement in both skills (already partly present). |
| A5 | Low | I | No eval prompts to show it reduces tokens or edits correctly. | Add 5–10 before/after prompts and measured tool-call counts. |

## Verdict
Reasonable personal-workflow protocol, unrelated to clinical correctness. Keep it out of the clinical skill suite's "critical path" in docs.

**Top 3 actions:** (1) narrow the trigger, (2) mark approval gates interactive-only, (3) make tool names generic.
