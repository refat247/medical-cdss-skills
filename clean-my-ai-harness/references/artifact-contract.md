# What the cleaner gives the reader

The cleaner creates one report folder outside the setup being reviewed. The first run is read-only.

## What the reader sees

### `YOUR-AI-SETUP.html`

This is the only file to lead with. It explains, in plain English:

- what shapes the AI;
- what is helping;
- what may be getting in the way;
- what this product and model need;
- the numbered changes the cleaner recommends;
- what the review could not see.

The user approves in chat with language such as `Approve 1 and 3. Leave 2.` Do not ask an ordinary reader to inspect hashes, change IDs, schemas, or JSON.

## What the cleaner keeps behind the report

The hidden `.clean-my-ai-harness/` directory contains the evidence that makes the simple report safe and reviewable:

- `00-scope-and-coverage.md` and `.json` — scan boundary and blind spots;
- `01-your-ai-setup-map.html`, `.md`, `.json`, and `.inventory.json` — full map and untouched inventory;
- `02-what-stays-and-what-changes.md` — complete decision register;
- `03-what-this-model-needs.md` — evidence for model-specific recommendations;
- `04-review-before-changing-anything.md` and `.json` — exact approval manifest, hashes, protections, risks, and rollback.

These files must remain portable. Use target-relative paths or placeholders such as `<home>` and `<run-root>`. Never expose a local username, home directory, temporary absolute path, or secret.

When the user replies with numbered choices, the cleaner maps those numbers to the generated changes in hidden `04`, changes only the copied manifest's `decision` values, and validates that returned copy before applying anything. One approved number never approves the batch.

## After approved changes

Put one plain-English `WHAT-CHANGED.md` beside the HTML report. It says what changed, what stayed protected, what checks passed, what remains uncertain, and how to undo the work.

Keep detailed `05-your-before-and-after.md`, `06-run-receipt.md`, patches, revised bundles, and optional run-trace evidence inside `.clean-my-ai-harness/`.
