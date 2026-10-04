# 07 · cdss-bridge-note-publisher (v1.2.1) — Independent Audit

**Tier:** Goal-adjacent (documentation leg) · **Code:** 1,286 LOC · **Tests:** 17 pass / 1 skipped `[M]` (with Pillow)

| Goal fit | Safety | Tests | Docs accuracy | Portability | **Overall** |
|:-:|:-:|:-:|:-:|:-:|:-:|
| A | B | B+ | B- | B+ | **B+** |

## What it does well
- The only skill with a **post-generation grounding gate** that is wired into publishing: grounding → cleanroom guard → docx; each stage fails closed. Missing guard script ⇒ refuses to publish; ambiguous note match ⇒ error `[C]`.
- `verify_grounding.py` rejects uncited claim lines, non-Davidson citations in the Davidson-only layer, unresolved chunk IDs, and flags parametric formulas ("red flags") in Layer 2 `[C]`.
- Declares `Pillow` in `pyproject.toml`.

## Findings
| ID | Sev | Ev | Finding | Fix |
|---|---|---|---|---|
| B1 | **High** | C | **The "zero-hallucination gate" checks citation *existence*, not support.** A claim passes if it carries a citation whose chunk ID resolves in the package. Nothing compares the claim text with the chunk text. A fabricated or mis-cited claim that quotes a real chunk ID passes. `weak_citations` are warnings only. | Add an entailment step: lexical overlap of numbers/drug names/units between claim and cited chunk at minimum, and fail when dose, unit, or drug name in the claim is absent from the chunk. Escalate low-overlap claims to human review. |
| B2 | Medium | C | `is_claim_line` treats bullets, table rows and lines of ≥6 words as claims. Short imperative lines (e.g. "Give 5 mg IV") in plain paragraphs fall below the threshold and are not checked. | Treat any line containing a number+unit or a drug name as a claim regardless of length. |
| B3 | Medium | C | The "Clinical Evidence Notes (guidelines outside package)" section and others are **exempt** from grounding by design. Claims there are ungrounded and may look identical to grounded ones in the final docx. | Visibly tag exempt content (e.g. `[UNGROUNDED]`) in the rendered document. |
| B4 | Medium | C | Layer 2 red flags are regexes for "parametric formulas" only. Other parametric facts (doses, thresholds) are not screened. | Extend with a dose/threshold scan against cited chunk text (see B1). |
| B5 | Low | C | Note selection by topic requires every topic word in the filename; good fail-closed behaviour but brittle for renamed notes. | Prefer explicit `--note`. |

## Verdict
Best-designed gate in the repo and correctly placed after generation, but it verifies provenance, not truth. Call it a "citation integrity gate" until B1 lands.

**Top 3 actions:** (1) claim-vs-chunk number/drug/unit check, (2) mark exempt sections in output, (3) widen claim detection.
