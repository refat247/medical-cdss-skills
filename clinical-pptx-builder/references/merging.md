# Merging and Editing

Raw PPTX package concatenation is not a reliable merge strategy. It can leave broken relationship targets, duplicate slide IDs, missing theme/font references, and hidden overflow introduced by incompatible masters.

Use this sequence:

1. Inspect each source deck and record slide count, aspect ratio, fonts, theme colors, notes, citations, and clinical claims.
2. Extract a slide-level specification: purpose, title, evidence, interpretation, visual, source, and disposition.
3. Deduplicate repeated claims and preserve the strongest source trace.
4. Rebuild in one canonical theme with explicit geometry and stable slide IDs.
5. Re-run all structural, clinical, render, and ZIP checks on the combined output.

If preserving an original slide exactly is essential, use a supported slide-copy mechanism and still validate the resulting package and render.
