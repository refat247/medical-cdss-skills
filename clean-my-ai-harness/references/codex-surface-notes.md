# Codex surface notes

## Discovery

Codex begins with skill names, descriptions, and paths, then loads a full `SKILL.md` after selection. Current OpenAI documentation caps the initial list at two percent of context, or 8,000 characters when context is unknown. When the catalog is large, descriptions may be shortened and skills may be omitted.

Measure the visible catalog and preserve any runtime warning. Do not claim a routing failure without a routing test or trace.

## Project scope

Codex scans repository skill locations from the current working directory up to the repository root. A current project can also inherit `AGENTS.md`, tools, permissions, sandboxes, hooks, schemas, tests, and other configuration.

Map the exact roots visible to this run. Global or admin controls should be `VERIFIED` only when the session exposes them.

## Actual run evidence

When available, use terminal output, tool-call receipts, loaded-skill messages, file hashes, diffs, tests, and output artifacts to distinguish:

`Available -> Eligible -> Shown -> Consulted -> Acted through -> Checked -> Accepted`

Existence is not activation. A directive to load a reference is not proof that it loaded.

## Safe changes

Codex can often edit local state. That makes the review boundary more important, not less. Check the working tree, create a reversible patch or copy, preserve unrelated changes, and apply only explicitly approved items.

## Other OpenAI surfaces

ChatGPT Work and the OpenAI API can expose different instructions, tools, memory, and controls. Do not claim this Codex adapter mapped those surfaces. An exported bundle can be audited as data, but hidden cloud state remains inaccessible.
