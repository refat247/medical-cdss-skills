# Mode Router

Select exactly one primary mode per task and state why.

| Mode | Trigger | Scope |
|---|---|---|
| INSPECT | “audit/check/review” without edits | read-only deck/source/spec audit |
| PATCH | bounded repair requested | protect unaffected content; escalate clinical changes |
| BUILD_STANDARD | ordinary evidence-locked clinical presentation | focused extraction/content map; no exhaustive case library |
| BUILD_CASE_BASED | complete case-based teaching system requested | full corpus + presentation pipelines |
| CORPUS_BUILD | user needs guideline/source -> complete case library | Pipeline A through Master Case Library/architecture as requested |
| DERIVATIVE_BUILD | frozen master/canonical parent exists | reuse frozen corpus/spec; no independent re-research |
| VISUAL_QA | presentation visual review only | render/mechanical/UI review; evidence immutable |
| VISUAL_POLISH | “beautify/polish/improve the visual” of a built deck | content-locked restyle + `VISUAL_POLISH_CONTENT_LOCK`; then normal render/visual QA |
| FINAL_RELEASE | canonical/final release requested | all clinical/mechanical/render/visual/promotion gates |
| MAINTENANCE | closed project reopened | classify defect/source update/new derivative/accessibility/archive |

If multiple modes appear relevant, choose the smallest mode that covers the task and name secondary gates explicitly.
