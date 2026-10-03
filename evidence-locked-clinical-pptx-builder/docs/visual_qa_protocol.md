# 100% Visual / Projector QA Protocol

Contact sheets are triage/navigation only. Final certification requires slide-by-slide review of the rendered final artifact.

For case/reveal layouts, run `scripts/case_reveal_layout_gate.py` before
rendering and inspect long titles, reveal badges, the longest card bodies,
source footers, and closing banners at full size. Keep the result advisory;
it cannot substitute for inspecting rendered pixels. See
`dys_2026_v1_5_design_reference.md` for one user-preferred design profile.
Record the renderer and version; if native PowerPoint fidelity is required but
not checked, retain `POWERPOINT-RENDER-PENDING` or equivalent project status.

For each slide review:
- clipping/cutoff;
- overflow/text-fit;
- unintended overlap;
- edge safety;
- title/body/footer hierarchy;
- font/readability at projection distance;
- source/citation readability;
- density/whitespace;
- alignment/spacing/consistency;
- contrast and non-colour-only encoding;
- image clarity/cropping;
- chart/ECG readability where present;
- case -> decision -> reveal visual rhythm;
- misleading visual emphasis.

If the deck went through `VISUAL_POLISH`, review the polished artifact and use the
ledger skeleton written by `scripts/visual_polish/verify.py --render`; see
`visual_polish_protocol.md`.

Record outcome in `visual_review_ledger.csv`. Any repaired final deck must be fully rerendered and re-reviewed.
