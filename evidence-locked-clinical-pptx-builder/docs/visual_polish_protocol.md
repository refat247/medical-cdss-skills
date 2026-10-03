# VISUAL_POLISH protocol (v2.4.0)

`VISUAL_POLISH` is a presentation-only stage. It restyles a deck that the
evidence-locked pipeline has already built and clinically audited. It changes
how the deck looks and never what it says. It certifies nothing: the existing
preflight, 100% render, 100% individual visual review, independent QA and
promotion gates (SKILL.md sections 18–25) still decide release.

```
pptx_build -> clinical_provenance_audit -> VISUAL_POLISH -> automated_preflight -> full_render_visual_qa -> ...
                                            polish.py + verify.py (VISUAL_POLISH_CONTENT_LOCK)
```

## 1. Non-negotiables

1. **Text is frozen.** Every text run is copied from the built slide with its
   bold, italic, underline and super/subscript. Nothing is retyped, shortened,
   merged, split across meaning, or paraphrased.
2. **Identity is frozen.** Slide count, slide ids, order, layout assignment,
   layout/master/theme parts and speaker notes stay byte-identical (verified).
3. **Fail closed, never fail creative.**
   - `SKIPPED`: role or text structure not recognised, so the slide is left exactly as built.
   - `SPLIT_REQUIRED`: the locked text cannot fit at the profile's body floor,
     so the slide is left as built and routed upstream. Repair follows the
     section 17 order (move detail to evidence-locked notes, split the slide,
     restructure). It is **never** blind font shrinking and never text trimming.
4. **Design tokens only.** The polish stage may add only: the phase icon (`?` / `✓`),
   the `REVEAL •` label, step numbers, `→`, and the case-number watermark.
   `verify.py` whitelists exactly these and rejects anything else as `ADDED`.
5. **Colour is never the only cue.** Phase also uses an icon and the eyebrow
   text; COR colour always sits behind the printed class code.

## 2. Profiles and font floors

| Profile | Body floor (1 / 2 / 3 cards) | Labels / source | Approval |
|---|---|---|---|
| `projector_default` | 24 / 24 / 24 pt | 16 pt | none: SKILL.md section 17 defaults |
| `dense_case_reveal` | 24 / 20 / 18 pt | 16 pt | **required**: `--profile-approved-by` and `release_policy.visual_polish.profile_approved_by` |

`dense_case_reveal` mirrors the observed density of the DYS_2026 v1.5 design
reference (`docs/dys_2026_v1_5_design_reference.md`). It is an explicit project
choice, never a default, and it never lowers the 16 pt source/label floor.
Case-id / phase / COR-LOE pills may step down to 14 pt (`BADGE_MIN`) only when a
compound COR/LOE code would otherwise wrap. They are identifiers, not citations;
the source line stays at 16 pt.

Title size is measured per slide (40 → 24 pt, one line). Body size is measured
per slide and is **identical across all cards on that slide**.

Measurement uses the real Aptos font when installed, otherwise the font the
renderer substitutes (`fc-match Aptos`), with a 3% width safety margin.
Override with `POLISH_METRIC_FONT` / `POLISH_METRIC_FONT_BOLD`.

## 3. Design system

- **Base:** navy `#0B1F33`, ink `#17212B`, light background `#F5F7FA`, blue `#175CD3` (kept from the builder).
- **Phase semantics:** DECIDE = amber `#E39A12` with a `?` icon; SOURCE REVEAL = green `#1E9E73` with a `✓` icon.
  Applied to the phase bar, progress fill, card stripe, header tint, eyebrow and badge.
- **COR (ACC/AHA convention):** 1 green · 2a yellow · 2b orange · 3 red. A compound code
  (`3: No Benefit/A; 1/C-LD`) becomes one pill per code, and the header wraps to a second row instead of clipping.
- **Single-case slides:** body anchored at the top, plus a faint case-number watermark (dropped automatically
  if keeping it would push the body below the floor).
- **Cover / divider / contract / closure:** role-specific layouts; a red closure check (harm/restriction) stays red.
- **Chrome:** the layout/master footer is never redrawn or duplicated. The slide's own source line sits above it.

## 4. Agent workflow

| Step | Action | Rationale |
|---|---|---|
| 1. Inspect | Render the built deck; read every contact sheet; open one slide of each role at full size. | Most decks are a handful of repeating layouts. Diagnose before prescribing. |
| 2. Diagnose | List concrete defects (mixed autofit sizes, wrapping/shrunken badges, DECIDE ≈ REVEAL, empty single-case cards, cramped cover, duplicated footer). | Every design change must map to a defect. |
| 3. Confirm | Ask the deck owner: scope (sample first or full), profile (`projector_default` or approved `dense_case_reveal`), COR colour coding, phase colours. | Design and density are owner decisions. Record them in project state. |
| 4. Sample | `polish ... --only <cover> <contract> <divider> <3-card DECIDE> <3-card REVEAL> <single-case>`, then render and show it. | Approve the system on 6 slides before applying it to the whole deck. |
| 5. Roll out | `python -m scripts.visual_polish.polish BUILT.pptx POLISHED.pptx --profile ... --report polish_report.json` | Rules, not hand edits: consistent output and zero retyping. |
| 6. Route | Send every `SPLIT_REQUIRED` slide upstream (slide spec / notes / split). Fix the parser for every `SKIPPED` slide, never the slide itself. | Fail-closed outcomes are work items, not noise. |
| 7. Gate | `python -m scripts.visual_polish.verify BUILT.pptx POLISHED.pptx --polish-report polish_report.json --render render/ --json visual_polish_verify.json`. It must exit 0. | Content lock, floors, fit, repo preflight, layout screen and render manifest in one call. |
| 8. Review | Fill `render/visual_review_ledger.csv` slide by slide (all domain columns), then run `render_qa_gate.py --require-ledger`. | SKILL.md section 19: contact sheets triage, they never certify. |
| 9. Repair | Fix the **rule** in `polish.py`/`style.py`, then re-run steps 5–8 on the whole deck. | One fix repairs every slide of that role, and a material repair means a full rerender. |
| 10. Record | Set `gates.visual_polish_applied = true` and `gates.visual_polish_content_lock = PASS` for the promotion gate. Report coverage honestly (which slides were reviewed individually). | The promotion gate blocks a polished deck without the content-lock PASS. It is not waivable. |

## 5. VISUAL_POLISH_CONTENT_LOCK checks

| Check | Blocking | Detail |
|---|---|---|
| identity | yes | slide count, slide id order, layout per slide |
| text lock | yes | every original atom present verbatim on the same slide (multiset) |
| no addition | yes | every polished text box is original text or a whitelisted token |
| notes | yes | speaker-notes text identical per slide |
| chrome | yes | `slideLayouts/`, `slideMasters/`, `theme/` parts byte-identical |
| floors | yes | label/source ≥ 16 pt (badges ≥ 14 pt); body ≥ profile floor |
| fit | yes | each rebuilt body box re-measured independently |
| repo preflight | yes | `scripts/pptx_preflight.py` must pass |
| layout screen | advisory | `scripts/case_reveal_layout_gate.py` issue codes reported |
| render | evidence | LibreOffice → PNG, `render_manifest.json` with slide-set SHA-256, blank per-slide ledger |

## 6. Known limits

- LibreOffice substitutes Aptos, so line breaks can differ slightly from PowerPoint. Where native fidelity matters, keep
  `POWERPOINT-RENDER-PENDING` until the deck has been reviewed in PowerPoint (section 19).
- Parsers match the builder's current conventions (eyebrow strings, cards > 200 pt tall, progress bars < 8 pt tall,
  `CASE nnn` ids, `REVEAL • <COR/LOE>` badges, one `SOURCE…` line). New layouts are `SKIPPED` until a parser is added.
- `dense_case_reveal` is a density choice the deck owner must approve. `projector_default` will route many dense
  three-card slides to `SPLIT_REQUIRED`. That is intended: it surfaces slides that break the section 17 floor.
