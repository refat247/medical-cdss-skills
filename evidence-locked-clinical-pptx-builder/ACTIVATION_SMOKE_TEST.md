# Runtime Activation Smoke Test - v2.4.0

Run in a fresh chat after installing the package.

Ask the runtime to report only instructions already injected by the selected skill, without reading Git, Notion, ZIPs or files.

Expected identity:
- skill: `evidence-locked-clinical-pptx-builder`
- version: `2.4.0`
- schema version: `3`

Expected capability markers include:
- independent `SOURCE_EXTRACTION_COMPLETENESS` and downstream node coverage;
- semantic recommendation-boundary and footnote-binding controls;
- source-hierarchy attribution distinct from editorial modules;
- CASE/DECIDE prompt leak/coherence gate;
- source-derived scenario to neutral DECIDE prompt alignment;
- advisory case/reveal layout screen plus full rendered visual review;
- `VISUAL_POLISH` mode with `VISUAL_POLISH_CONTENT_LOCK` gate (fail-closed SKIPPED / SPLIT_REQUIRED);
- `SOURCE_NATIVE_EXACT` / `SOURCE_NATIVE_NORMALIZED` / `PEDAGOGIC_PARAPHRASE`;
- repair-fidelity audit;
- CRITICAL/HIGH semantic canonical-promotion blocking.

PASS string: `PASS - evidence-locked-clinical-pptx-builder v2.4.0 activated`
