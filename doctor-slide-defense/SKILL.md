---
name: doctor-slide-defense
description: "Build a doctor-panel defense for a clinical slide deck. Retrieve by claim, then render output version 1, 2, 3, or 4 from one claim ledger. Use when the speaker, audience, and critics are doctors and a PowerPoint must be defended from books and guidelines. Not a generic slide beautifier and not a study-book first."
metadata:
  version: "1.0.0"
  status: "stable"
  lifecycle: "active"
version: "1.0.0"
---

# Doctor slide defense (v1.0.0)

Package version is SemVer `1.0.0`. Output versions `1`, `2`, `3`, and `4` are reading shapes, not package versions. Do not bump this package when the user asks for output version 4.

## When to use

Use this when a doctor must defend a clinical deck to other doctors. Do not start by writing a textbook essay or an HTML study book.

## Output versions

| Flag | Shape | Use when |
|---|---|---|
| `1` | Citation map. Books, then guidelines, then what not to say. | You need every locator before prose. |
| `2` | One-argument prose. | You want a continuous read without status labels. |
| `3` | Rehearsal. Claim, what you may say, if asked. | You want the smoother read. |
| `4` | Labeled claims. SUPPORTED, SLIDE-PAPER, DO NOT SAY, CONFLICT. | You are about to be stopped on one number. Default for a panel. |

Same ledger. Switch with `--output-version`. Do not keep four hand-edited manuscripts.

## Workflow

1. Do not overwrite the PowerPoint.
2. Extract every number, class, dose, and drug claim from the deck. Freeze them in a claim ledger. See `references/claim-ledger.schema.json`.
3. For each claim, retrieve only the matching textbook chunk or guideline PDF page. Label it. Do not ask for “everything on angina.”
4. Render:

```bash
python scripts/render_defense.py LEDGER.json --output-version 4 --out defense-v4.md
```

5. HTML is optional and last. Pass `--html out.html` only after the markdown exists. It calls `offline-study-guide` when `DOCTOR_SLIDE_DEFENSE_HTML_BUILDER` points at `build_guide.py`. A missing builder is a warning, not a successful reader.
6. The ward limit must survive in every output version.

## Labels

- `SUPPORTED` — a named book chunk or guideline page states it.
- `SLIDE_PAPER` — only the citation printed on the slide.
- `DO_NOT_SAY` — absent, or stronger than the sources allow.
- `CONFLICT` — the slide figure and the source figure are not the same fact.

Never convert a slide-paper percentage into a textbook fact. Never call a symptom drug a survival drug unless a retrieved guideline page says so.

## States

Package edited, tests passed, installed, runtime-loaded, and Git-synced are separate. Rendering a fixture is not clinical validation.

## References

- `references/output-versions.md`
- `references/claim-ledger.schema.json`
- `fixtures/angina_trimetazidine_ledger.json` — worked example from the 14 October 2026 VMR trimetazidine session. It does not replace a new deck’s own retrieval.
