# 18 · token-audit (v1.0.0) — Independent Audit

**Tier:** Platform/meta · **Type:** prompt-only, ~514 words · **Code/tests:** none

| Goal fit | Safety | Tests | Docs accuracy | Portability | **Overall** |
|:-:|:-:|:-:|:-:|:-:|:-:|
| n/a | A (read-only by design) | n/a | C+ | D | **B-** |

## What it does well
- Strictly **read-only** ("Do not fix anything … change no file"), asks for measured numbers not guesses, and covers six useful areas: rules bloat, tool/MCP schema overhead, model/reasoning profile, output discipline, subagents, scheduled tasks `[C]`.

## Findings
| ID | Sev | Ev | Finding | Fix |
|---|---|---|---|---|
| T1 | Medium | C | **States one provider's cache behaviour as fact:** "Compare trigger intervals against the 1-hour prompt cache lifetime window" and "model switching invalidates the cache key". Cache lifetimes and keys differ by provider, model and plan. | Make the window a parameter the audit reads from the active provider's docs; say "verify". |
| T2 | Medium | C | **Host-specific paths and commands:** `~/.gemini/config/skills/`, `~/.gemini/antigravity/builtin/skills/`, `Get-ScheduledTask`. Not usable in Claude Code, Codex on Linux, or CI. | Detect the surface first; provide per-surface path tables. |
| T3 | Low | C | `bytes / 4` token estimate is rough (fine for ranking), and the thresholds (20 KB per file, 40 KB total) are unexplained. | Label as heuristic; cite basis for thresholds. |
| T4 | Low | C | No fixed output template, so two runs are not comparable over time. | Add a table schema (item, measured value, threshold, status). |
| T5 | Low | C | Overlaps `clean-my-ai-harness` (see 17-X4). | Cross-link. |

## Verdict
A sound, safe checklist; make it surface-neutral and give it a result schema.

**Top 3 actions:** (1) provider-neutral cache wording, (2) per-surface path table, (3) fixed report schema.
