# 17 · clean-my-ai-harness (v1.0.1) — Independent Audit

**Tier:** Platform/meta · **Code:** 3,088 LOC (6 scripts, 6 schemas/templates, 5 reference docs) · **Tests: 0**

| Goal fit | Safety | Tests | Docs accuracy | Portability | **Overall** |
|:-:|:-:|:-:|:-:|:-:|:-:|
| n/a | B+ | F | B | B | **B-** |

## What it does well
- Careful design: the scanner treats audited files as untrusted data (never executes, imports, follows links or emits contents), bounded by file-count/byte/depth limits `[C]`. I ran it on this repo: it completed and found **50 visible controls** and wrote the scope/coverage and setup-map JSON `[M]`.
- JSON schemas plus validators for run traces and approval reviews; run-trace marked `NOT_EXPOSED` rather than guessed `[M]`.

## Findings
| ID | Sev | Ev | Finding | Fix |
|---|---|---|---|---|
| X1 | High | M | **No tests for 3,088 lines**, including a 1,206-line packet builder and a security-oriented scanner. | Golden-file tests on a small fixture harness; test the byte/file/depth limits and symlink handling. |
| X2 | Medium | M | `check_skill_overlaps.py` (96 LOC) is not an overlap detector: it checks that three hard-coded navigator names mention "single/alone" and that two protocols exist. It reported "All boundaries verified" for this repo while real overlaps exist (13 vs 14 vs 9 on federation, SBA, prescribing safety). | Compute description/trigger similarity and duplicated-capability claims; validate `requires:` once defined. |
| X3 | Medium | C | Reference `model-profile-gpt56-codex-2026-07.md` ties guidance to one model and date; will go stale. | Version and date-stamp it; separate from stable protocol. |
| X4 | Low | C | Large overlap with `token-audit` (both inventory installed skills, rules and tools) with no cross-reference. | Merge or cross-link with a clear split (security/overlap vs token cost). |
| X5 | Low | I | Unrelated to the clinical goal; adds 3k LOC to the repo's maintenance surface. | Consider a separate repo. |

## Verdict
Thoughtfully built and demonstrably runnable, but unverified by tests and shipping a trivial overlap check under a strong name.

**Top 3 actions:** (1) tests for scanner limits, (2) real overlap detection, (3) merge/cross-link with `token-audit`.
