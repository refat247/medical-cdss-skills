# Source-Lock Contract

Clinical evidence sources and non-clinical context must be separately registered.

Approved clinical sources may support clinical claims. Operational context, style references, user images and external/generated visuals may not silently become evidence.

Required source fields: `source_id`, `path`, `role`, `source_type`, `status`, `sha256` when feasible, `correction_of` if applicable.

Required clinical traceability: source locator -> decision node -> case -> slide spec -> slide/source map -> notes.
