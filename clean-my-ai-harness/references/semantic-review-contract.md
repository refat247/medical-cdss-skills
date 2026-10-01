# The model writes one small review file

Treat the scanner and packet generator as black boxes. Run them; do not ask the model to inspect their source, reproduce their logic, edit scanner JSON, hand-write the HTML map, or invent approval IDs.

## Default flow

Use **Quick Check** unless the user explicitly asks for a maintainer audit.

1. Run `scan_visible_harness.py`. It creates the untouched `00` scope JSON and `01` inventory JSON.
2. Give the model those two JSON files, this contract, and `semantic-review.template.json`.
3. The model writes exactly one `semantic-review.json` that matches `semantic-review.schema.json`.
4. Run `build_review_packet.py` with the same audited target. It validates the scanner pair, hashes, locations, and IDs; stages the whole packet; then publishes it in one rename.

The model never edits either scanner file. The generator derives the review ID and every change ID from the frozen baseline and exact proposal. An approval therefore round-trips to one specific review and one specific change.

## Hard bounds

- Semantic-review JSON: at most 1,000,000 bytes.
- Quick Check: at most 50 reviewed controls.
- Maintainer audit: at most 500 reviewed controls.
- Unreviewed control IDs: at most 5,000 and each must be named.
- Coverage gaps: at most 50.
- Model recommendations: at most 20.
- Reader name: at most 160 characters.
- Current effect, protection, risk, rollback, recommendation, cited evidence, and disproof condition: at most 500 characters each.
- Proposed change, reason, shared-core field, why-here explanation, and gap detail: at most 1,000 characters each.

Every visible scanner control must appear exactly once: either in `decisions` or in `unreviewed_control_ids`. Unreviewed controls require a plain-language coverage gap.

## Allowed labels

Decisions:

- `KEEP`
- `ONE_HOME`
- `LOAD_LATER`
- `MAKE_A_CHECK`
- `PROBATION`
- `RETIRE`

Evidence:

- `VERIFIED`
- `USER_REPORTED`
- `INFERRED`
- `INACCESSIBLE`
- `NOT_APPLICABLE`

Do not put private absolute paths, credentials, tokens, key-value secrets, HTML, Markdown links or images, headings, or URI payloads in the semantic review. Use scanner control IDs and plain prose. The public route fails closed; it does not redact and continue.

`SCAN_DIR`, `SEMANTIC_REVIEW`, and `PACKET_DIR` must all be outside the audited target. `PACKET_DIR` must not already exist and cannot contain or overwrite an input. A failed build leaves no packet directory or partial reader files.

## Command

```bash
python3 scripts/build_review_packet.py \
  --target-root TARGET \
  --scan-receipt SCAN_DIR/.scan-receipt.json \
  SCAN_DIR/00-scope-and-coverage.json \
  SCAN_DIR/01-your-ai-setup-map.json \
  semantic-review.json \
  --output-dir review-packet
```

The generator verifies the exact scope and map hashes and their shared scanner-generated `scan_id` before creating anything. It creates the visible `YOUR-AI-SETUP.html` and keeps `04-review-before-changing-anything.json` inside `.clean-my-ai-harness/`. Translate the user's numbered chat choices into a copied manifest, change only that copy's `decision` values, then validate it with:

```bash
python3 scripts/validate_approval_review.py \
  GENERATED-04.json \
  RETURNED-04.json
```

The validator permits `PROPOSED` to become `APPROVED` or `REJECTED`. It rejects edited proposals, hashes, IDs, missing rows, unknown rows, duplicates, and stale baselines.
