# Independent Second-Runtime Visual QA Prompt — v2.2.0

## Policy

`independent_visual_qa_policy` must be one of:
- `required`
- `required_unless_explicit_user_waiver`
- `optional`

High-stakes clinical projects default to `required_unless_explicit_user_waiver`.

## Certifying format

A human-readable Markdown report is useful for discussion but is **non-certifying**. For certification, return normalized JSON conforming to `templates/independent_visual_review_report.json`.

The JSON must contain reviewer/runtime identity, candidate PPTX hash, rendered-slide-set hash, slide count, one unique slide row for every slide, `clinical_change_authority: NONE`, and adjudication for every warning/finding/proposed repair.

Adjudication values:
- `ACCEPT`
- `REJECT`
- `CLINICAL_ADJUDICATION_REQUIRED`

If any finding needs clinical adjudication, stop independent certification and send it back to the locked clinical pipeline.

If any presentation repair is accepted, the original candidate cannot be certified. Require repaired PPTX hash, repaired rendered-set hash, repair mapping, `second_full_render_verification: true`, and a complete 100% post-repair slide-by-slide review before certification.

## Reviewer prompt

```text
INDEPENDENT VISUAL QA — READ-ONLY FIRST PASS

Candidate deck: <PPTX>
Candidate PPTX SHA-256: <HASH>
Render set: <DIRECTORY OR FILE LIST>
Rendered-slide-set SHA-256: <HASH>
Design/projector contract: <FILE>
Evidence boundary: <APPROVED CLINICAL SOURCES / NO-INVENTION RULE>

Your audit domain is ONLY visual/UI/UX/mechanical presentation quality.
Do NOT add or rewrite clinical facts, reinterpret recommendations, or change thresholds/doses/Class/LoE/terminology. clinical_change_authority = NONE.

Inspect every rendered slide individually. Contact sheets may help navigation but do not certify slides.
For every slide return a unique row with status and finding. Use finding=NONE for a clean slide.
For every warning/finding/proposed repair include adjudication: ACCEPT, REJECT, or CLINICAL_ADJUDICATION_REQUIRED.

Return structured JSON suitable for templates/independent_visual_review_report.json. Markdown narrative may accompany it but cannot certify the deck.
```

Main workflow: findings -> adjudication -> accepted visual repairs -> full rerender -> complete post-repair review -> independent certification gate.
