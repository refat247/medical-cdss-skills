# Explicit reference layout

Use an opt-in Markdown fence named `reference-entry` containing JSON. Do not silently transform ordinary prose, Markdown lists, DOCX or PDF text into this schema. Prepare an explicit source-grounded map first.

```reference-entry
{"schema":"reference-entry-v1","source_text":"Example term\nSource statement.","rows":[{"start":0,"end":13,"role":"heading"},{"start":13,"end":30,"role":"source"}],"explanation_bn":"এখানে ধারণাটির অর্থ সংক্ষেপে লিখুন।","locator":"Synthetic example only"}
```

Offsets are Python Unicode code-point positions, start inclusive and end exclusive. The concatenated spans must cover source_text exactly once, in order, without gaps or overlaps. Do not normalize whitespace, clinical values or punctuation while creating spans. When uncertain, use a single source row and log a review finding.

Allowed roles: heading, context, dose, preparation, concentration, example, brands, loading, dilution, maintenance, indication, comparison, review, source. Roles only affect presentation; no inferred clinical labels are added. Each optional group is a nonempty formulation identifier whose rows stay contiguous. A group cannot close and later reopen. Group membership must come from the source. Optional explanation_bn must be a string containing Bengali; locator is a string.

The builder assigns occurrence-specific reference IDs and escapes source text without interpreting Markdown inside immutable source spans. It embeds the source JSON; the checker compares full text, offsets, roles and rendered formulation containers. This verifies internal integrity; compare the payload against the independently locked original source as well.

`--density-policy report` (default) flags rows/prose/list items over 320 characters, or over 180 characters with at least two explicit Dose/Syrup/Drop/Brand/Loading/Maintenance/Dilution/DS/Example labels. Findings are heuristics, not a readability or clinical certificate. `--density-policy error` blocks rendering when findings remain. An explicit structure override is never a successful standard QA result. Density findings and visual_qa=NOT EXECUTED appear in the census; automated builds never claim browser QA.

Run `python3 -B scripts/test_reference_layout.py` for source integrity, ownership, escaping, repeated-entry and density-gate tests; retain `scripts/run_regression.py` for legacy paths. Read references/bilingual-handoff.md for the Curator transfer and actual-artifact gates.
