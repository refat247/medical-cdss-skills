# Migration Notes - v2.3.0 to v2.4.0

Existing project state files remain valid. To adopt the new pipeline state,
insert `visual_polish` (depends on `clinical_provenance_audit`) and make
`automated_preflight` depend on it. Projects that do not polish should mark
`visual_polish` as `complete` or `waived` with a note.

To polish a built deck:

1. Set `release_policy.visual_polish.enabled: true` and choose a profile.
   `dense_case_reveal` needs `profile_approved_by`.
2. Run `python -m scripts.visual_polish.polish` (sample with `--only` first).
3. Run `python -m scripts.visual_polish.verify ... --render <dir>`; it must exit 0.
4. Complete the generated per-slide ledger, then run `render_qa_gate.py --require-ledger`.
5. Add `"visual_polish_applied": true, "visual_polish_content_lock": "PASS"` to
   the promotion gates JSON.

`scripts/case_reveal_layout_gate.py` no longer requires Windows. Set
`LAYOUT_GATE_FONT` to pin a specific metric font.
