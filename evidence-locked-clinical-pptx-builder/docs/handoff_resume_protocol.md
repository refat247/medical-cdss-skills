# Handoff / Resume Protocol

A versioned handoff/current-state artifact is mandatory for multi-chat projects.

At each major state record: mode/reason, completed work, artifacts/hashes, audit result, frozen state, unresolved items, next dependency-valid task.

If `emit_next_prompt` is enabled, append a copy/paste-ready next prompt. On context uncertainty, reopen the latest state/handoff and required sources; never reconstruct only from memory.
