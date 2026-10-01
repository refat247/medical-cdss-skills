"""Stage 4.6 checkpoint-decision logic (CP-02 branch + CP-05 degraded-run
block + correction H's chunks_reviewed==0 guard), extracted so it's testable
without a live Sonnet API call or a hand-run manual-review session.

Consumes the metadata dict already produced by
stage_4_6_sonnet_verification.py's stage_4_with_verification() /
apply_manual_corrections() — that module's own logic is unchanged (per
IMPLEMENTATION_MAP.md's finding: it already computes status="partial_success"
correctly; the bug was SKILL.md never reading it). This module is the piece
that was missing.
"""

DEGRADED_RATIO_THRESHOLD = 0.10


def decide_checkpoint_action(meta, *, total_flagged=None):
    """Returns (action, metadata) where action is one of:
      "pending_manual"    — needs_manual_verification is True; caller must run
                             the manual protocol and call this again with the
                             resulting metadata before a final action is known.
      "failed"            — chunks_reviewed == 0 (correction H): never silently
                             treated as a 0%-unparsed clean pass. Ambiguous
                             between "legitimately nothing to review" and "a
                             parsing bug reviewed nothing" — both require an
                             explicit human look, neither completes silently.
      "blocked"           — chunks_unparsed / chunks_reviewed exceeds the 10%
                             degraded-run threshold (CP-05).
      "review_incomplete" — v2.6.5 (emergency fix, see
                             V2_6_5_EMERGENCY_INTEGRITY_FIX_REPORT.md): the
                             regex baseline flagged `total_flagged` candidates
                             for review and fewer than that were actually
                             reviewed. Before v2.6.5, ANY chunks_reviewed > 0
                             satisfied "complete" regardless of how small a
                             fraction of the flagged set that was (confirmed
                             on Chapter 14: 45/283 flagged candidates reviewed,
                               10 corrected, returned "complete" with no
                             signal that 238 remained unreviewed). A stage must
                             not be marked complete merely because SOME review
                             was documented — the acceptance condition is that
                             the REQUIRED review (every flagged candidate) was
                             done. Caller should mark this stage IN_PROGRESS
                             (the pipeline's existing state for "needs human
                             adjudication before it can resolve"), not
                             COMPLETED, and the chapter's trust classification
                             must not claim full semantic-review completion
                             until this becomes "complete".
      "complete"          — verification succeeded within threshold AND (when
                             total_flagged is provided) chunks_reviewed >=
                             total_flagged.

    `total_flagged` (optional, v2.6.5): pass `len(meta['review_priority'])`
    from stage_4_with_verification()'s output (or the equivalent regex-flagged
    candidate count) to enable the completeness check above. Omitting it
    preserves the exact pre-v2.6.5 behavior (chunks_reviewed > 0 alone can
    still reach "complete") — existing callers that don't have this figure
    handy are not broken, but should be migrated to pass it where available.
    """
    if meta.get('needs_manual_verification', False):
        return "pending_manual", {
            "reason": "no Gemini API key/package configured — in-session Antigravity manual verification required",
        }

    chunks_reviewed = meta.get('chunks_reviewed', 0) or 0
    chunks_unparsed = meta.get('chunks_unparsed', 0) or 0

    if chunks_reviewed == 0:
        return "failed", {
            "chunks_reviewed": 0,
            "chunks_unparsed": chunks_unparsed,
            "reason": (
                "chunks_reviewed=0 — never treated as a clean 0% unparsed pass "
                "(correction H). Verify whether this chapter genuinely has zero "
                "eligible L2 chunks in the requested levels, or whether chunk "
                "parsing silently found nothing."
            ),
        }

    unparsed_ratio = chunks_unparsed / chunks_reviewed
    metadata = {
        "chunks_reviewed": chunks_reviewed,
        "chunks_unparsed": chunks_unparsed,
        "unparsed_ratio": round(unparsed_ratio, 4),
        "chunks_corrected": meta.get('chunks_corrected', 0),
    }
    if unparsed_ratio > DEGRADED_RATIO_THRESHOLD:
        metadata["reason"] = (
            f"chunks_unparsed/chunks_reviewed = {unparsed_ratio:.1%} exceeds the "
            f"{DEGRADED_RATIO_THRESHOLD:.0%} degraded-run threshold (CP-05)"
        )
        return "blocked", metadata

    if total_flagged is not None:
        metadata["total_flagged"] = total_flagged
        metadata["review_completeness_ratio"] = (
            round(chunks_reviewed / total_flagged, 4) if total_flagged else 1.0
        )
        if chunks_reviewed < total_flagged:
            metadata["reason"] = (
                f"chunks_reviewed ({chunks_reviewed}) < total_flagged ({total_flagged}) — "
                f"{total_flagged - chunks_reviewed} flagged candidate(s) were never reviewed. "
                f"A partial review is real progress, not a completed one; this stage stays "
                f"IN_PROGRESS until every flagged candidate has been reviewed."
            )
            return "review_incomplete", metadata

    return "complete", metadata
