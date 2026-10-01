# Review Before Changing Anything

Review ID: [generated from the scope and map baselines by `build_review_packet.py`]  
Target: [target label]  
Baseline map SHA-256: [hash of reviewed map JSON]  
Permission mode: READ ONLY UNTIL INDIVIDUAL APPROVAL

To approve, return this same file or reply with the review ID plus the exact change IDs and `APPROVED` or `REJECTED`. Approval of one item never approves the batch.

| Change ID | Control IDs | Current source hashes | Exact proposed change | Protection that must survive | Risk | Rollback | Decision |
|---|---|---|---|---|---|---|---|
| [generator-derived change ID] | [IDs] | [hashes] | [change] | [protection] | [risk] | [rollback] | PROPOSED |

Do not invent or rename review IDs or change IDs. Approval must quote the exact generated values.

## Apply gate

Before applying an approved item:

1. verify the review ID and baseline map hash;
2. re-hash every affected source and stop if it changed;
3. create a recoverable copy, patch, or replacement bundle;
4. apply only rows marked `APPROVED`;
5. run the named preservation and finish checks;
6. stop and record any failed check.

## What I Could Not See

[Coverage and approval gaps.]
