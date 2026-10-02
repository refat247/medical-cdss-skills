# Notion UX Patterns

## Practical hub layout

1. Current-status callout
2. Start Here / what to open first
3. Current phase and next action
4. Quick navigation / compact destination table
5. Warnings and blockers
6. Current work or filtered database view
7. Detailed content
8. Historical/reference archive
9. Curator Change Summary when the research page was materially changed

## Semantic color system

- Blue: current phase, canonical navigation, informational/current state.
- Green: verified/complete/approved or the single immediate active action.
- Yellow: prerequisite, caution, pending validation, needs review/recheck.
- Orange: stronger operational caution, action-soon or degraded-but-not-blocked.
- Red: blocked, unsafe, failed, high-risk or do-not-proceed.
- Gray: reference-only, archive, superseded/history and neutral metadata.
- Brown: raw-source/provenance/legacy or field-observation grouping.
- Purple: methodology/model/analysis/system-design layer.
- Pink: qualitative/editorial/human-review category when genuinely useful.

Keep long body text neutral. Prefer semantic background callouts for whole-block meaning and short colored labels for status.

## Emphasis hierarchy

Heading hierarchy → bold → semantic color/background → italics → underline → strikethrough.

Use bold for current decisions/actions and decisive values. Use italics for nuance or interpretation. Underline only exceptional critical constraints. Use strikethrough only for preserved superseded history with the replacement state nearby.

## Block patterns

- Bullets: unordered findings/options.
- Numbered lists: real sequences and procedures.
- To-dos: actionable work with completion state.
- Callouts: current decision, blocker, safety warning, time-sensitive item, provenance or next action.
- Quotes: brief attributed source wording, not generic emphasis.
- Code: exact technical literals, commands or configuration.
- Equations: actual mathematical notation only.
- Toggles: optional detail, appendices, raw excerpts and historical context. Never hide the only current decision, blocker or next action.

## Column patterns

- Two columns are the preferred maximum for substantive side-by-side content.
- Three columns are suitable only for short symmetric summaries.
- Four columns are a dashboard/KPI exception.
- Five columns should be limited to very short desktop KPI/icon strips.
- Never place the only safety warning, final decision or legal/clinical constraint in a narrow column.
- Ensure the page still makes sense when columns stack vertically on mobile.

## Page-level presentation

- Default font is standard for research, dashboards and operations.
- Serif is for long-form narrative reading.
- Mono is for code/config/schema/log-heavy pages.
- Small text is a density option, not a default.
- Full width is useful for dashboards, matrices, databases and wide comparisons; keep normal width for focused narrative reading.
- Do not claim UI-only page settings were changed when the connected API cannot expose/verify them.

## Research visual QA

Within about five seconds, a reader should identify what is current, what to do next, what needs recheck, what is blocked and what is reference/archive only. Keep evidence quality, audit status, freshness and workflow state separate.

## Curator Change Summary pattern

For a research page materially changed by the curator, append or update a compact summary containing review date/time and writer, what changed, visual logic actually applied, what was intentionally preserved, unsupported/UI-only limitations, current page state and next action when relevant.

`CURATOR REVIEWED` is not evidence verification, clinical verification, statistical validation or freshness. On raw/source pages, keep the curator summary outside the preserved original output.

## Block-action governance

Duplicate only when needed and relabel immediately. Move only to improve canonical architecture without breaking provenance or links. Prefer archive/supersede over delete for research content. Comments are discussion, not authoritative decisions. Suggest edits when canonical content should not be silently overwritten. Synced blocks are reserved for intentionally global canonical instructions/status. Copy block links for precise evidence/decision deep-links. Clear format only to remove accidental/inconsistent formatting, not meaningful status.