# DYS_2026 v1.5 case/reveal design reference

The user preferred the appearance of the exact deck at
`assets/design_references/DYS_2026_Master_Core_v1.5_VISUAL_REPAIR_PRECANONICAL.pptx`.
SHA-256: `71c61806dba38d06ecef730bf8a8a0073995596327da6b6f567490fbf2f913d2`.
This is a **STYLE_REFERENCE** only. Its state is
`PRECANONICAL / POWERPOINT-RENDER-PENDING / VISUAL-HOLD`. No 193/193 formal
individual native-PowerPoint visual review or independent QA is claimed here.
Do not copy its clinical claims, source mapping, source footers, case count,
or release status into a new project.

Design lessons from comparing the supplied v1.3 baseline and v1.5:

1. Fit long title text within the title band before it reaches the eyebrow or
   progress rule. Check the longest source-reveal and numbered-part titles.
2. Give `REVEAL` badges enough width and height for COR/LOE text; keep them
   separate from each card's body.
3. Top-align dense card bodies and use consistent inner margins. Verify the
   longest card on each 1-, 2-, and 3-card slide at presentation size.
4. Keep source/footer labels readable and outside the card body region.
5. Check closing/banner slides separately; they may use different geometry.

The sample uses a 13.333 x 7.5 inch canvas, title sizes that vary with title
length, and dense three-card body text sometimes around 17-21 pt. Those are
observed design features, **not** new global font floors. The normal
projector rule in `SKILL.md` still applies unless a project approves and
visually validates a denser profile. A visually attractive reference can
still contain defects; validate every generated slide.

v2.4.0 encodes this density as the opt-in `dense_case_reveal` profile of
`scripts/visual_polish/` (approval required; see `visual_polish_protocol.md`).

Run `scripts/case_reveal_layout_gate.py` as an early warning screen, then
render and inspect each final slide. Record renderer identity/version and
distinguish an alternate-renderer review from native PowerPoint confirmation.
