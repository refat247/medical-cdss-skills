# 16 · ultimate-protocol (v1.0.0) — Independent Audit

**Tier:** Platform/meta · **Type:** prompt-only, ~344 words · **Code/tests:** none

| Goal fit | Safety | Tests | Docs accuracy | Portability | **Overall** |
|:-:|:-:|:-:|:-:|:-:|:-:|
| n/a | C | n/a | B | C | **C+** |

## What it does well
- Narrow, explicit trigger ("ultimate mode", "json mode", …), unlike 15. Defines one status schema and a fallback for blocking questions `[C]`.

## Findings
| ID | Sev | Ev | Finding | Fix |
|---|---|---|---|---|
| U-1 | **High** | C | **Suppresses safety information.** "NEVER output conversational text … The ONLY permitted end-of-turn output is the single minified JSON block" has no channel for warnings. If the mode is left on while a clinical or safety-relevant finding appears (e.g. a failing grounding gate, a contraindication), the user sees only `{"status":…}`. | Add a mandatory `warnings` array and require non-empty output for any failed safety/grounding gate. |
| U-2 | Medium | C | "If it fails, fix internally **WITHOUT asking the user**" encourages autonomous retry loops on repos that hold clinical content, with no iteration cap. | Cap retries (e.g. 3) then emit `failed_needs_review`. |
| U-3 | Medium | C | **Self-reported counters:** `tool_calls_made` and `files_mutated` come from the model's own tally, are not verifiable, and the first has no defined counting rule. The schema also shows `true|false` (not valid JSON) as a template. | Derive from the harness log, or drop them; give a valid example. |
| U-4 | Low | C | Overrides `antigravity-protocol` "absolutely", but nothing says how to exit the mode. | Add "ultimate mode off" exit phrase. |

## Verdict
Good as a narrow automation mode, risky if left active during clinical work because it removes the user's visibility of failures.

**Top 3 actions:** (1) add a warnings channel, (2) retry cap, (3) drop unverifiable counters.
