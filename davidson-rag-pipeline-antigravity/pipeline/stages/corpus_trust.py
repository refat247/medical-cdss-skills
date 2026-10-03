"""Deterministic corpus-trust classifier (v2.6.2, read-access helper added v2.6.3).

Before this module existed, chapter trust classification lived only as
hand-written prose in `CORPUS_TRUST_STATUS.md`, independently re-derived
per chapter. That process produced a real, confirmed error: `25_AI_H` was
classified identically to `25_AI_C` ("no checkpoint exists") when it
actually has a checkpoint — an ancient one, predating Stage 4.5c. A
deterministic classifier, fed explicit evidence rather than re-inspected by
hand each time, is how that class of error gets structurally prevented
going forward.

`classify_trust()` takes small, explicit evidence inputs — a loaded
checkpoint dict (or `None`), an optional loaded
`{PREFIX}_ClinicalFidelityGate.json` dict, and two booleans for the
no-checkpoint case (`has_stage6_validation_file`,
`has_coverage_gaps_file` — evidence an ad hoc, pre-checkpoint-system run
actually reached those stages). It deliberately has NO
"rag_optimised_exists" parameter and never will: `RAG_Optimised.md`'s mere
presence proves nothing about certification (every one of the four real
chapters inspected during the audit has this file; only one is actually
trustworthy) — see the evaluation guide's own rule ("Do not infer
certification from RAG_Optimised.md's existence").
"""
import os

from pipeline import checkpoint_utils


def load_checkpoint_for_classification(output_dir, prefix):
    """v2.6.3 — sanctioned way to load a checkpoint for trust
    classification. Thin wrapper around checkpoint_utils.read_checkpoint()
    (never load_checkpoint()/load_checkpoint_for_run()) so trust
    classification can never accidentally see a migrated/mutated shape
    instead of the historical file as it actually exists on disk — the
    exact distinction this classifier exists to get right (see module
    docstring's 25_AI_H example). Returns (checkpoint, checkpoint_path), or
    (None, checkpoint_path) if no checkpoint file exists for this chapter
    (the caller then passes checkpoint=None into classify_trust(), same as
    before this helper existed).
    """
    cp_path = checkpoint_utils.checkpoint_path_for(output_dir, prefix)
    if not os.path.exists(cp_path):
        return None, cp_path
    checkpoint, cp_path = checkpoint_utils.read_checkpoint(output_dir, prefix)
    return checkpoint, cp_path


CLASSIFICATIONS = (
    "CORPUS_TESTING_READY",
    "CORPUS_REVIEW_PENDING",
    "LEGACY_UNCHECKPOINTED",
    "LEGACY_STALE_CHECKPOINT",
    "LEGACY_UNGATED",
    "IN_PROGRESS",
)


def _result(classification, trusted, reasons, required_action):
    return {
        "classification": classification,
        "trusted_for_downstream_use": trusted,
        "reasons": reasons,
        "required_action": required_action,
    }


def _bad_count(value):
    """v2.6.6 — True if `value` is missing (None) or not a well-formed
    non-negative int. `bool` is deliberately excluded even though it is a
    Python subclass of `int` -- a stray `True`/`False` where a genuine count
    is expected must be treated as malformed, not silently coerced to 1/0.
    Used to distinguish "explicitly present and well-formed" (may proceed)
    from "missing or malformed" (must fail closed) for every mandatory
    evidence count this classifier checks."""
    if value is None:
        return True
    if isinstance(value, bool):
        return True
    if not isinstance(value, int):
        return True
    if value < 0:
        return True
    return False


def classify_trust(checkpoint, clinical_fidelity_gate=None,
                    has_stage6_validation_file=False, has_coverage_gaps_file=False,
                    source_lines_precision_summary=None, protection_marker=None,
                    stage_4_6_review_status=None, unresolved_completeness_clusters=None,
                    stage_4_6_chunks_reviewed=None, stage_4_6_total_flagged=None):
    """Pure function — no filesystem access. Callers load the checkpoint
    JSON (or pass None if no `*_CHECKPOINT.json` exists) and the Gate JSON
    (or None) themselves; this function only classifies from that already-
    loaded evidence.

    v2.6.4 additions (Corpus-Scale Gate Closure, required outcome #3 — "an
    untested source-line mapping cannot receive CORPUS_TESTING_READY"):

    `source_lines_precision_summary`: the dict `stages.source_lines_precision
    .build_precision_summary()` produces (`{"tested": bool,
    "unresolved_count": int, ...}`), or `None`.

    SCOPING — read this before passing (or omitting) this parameter:
    `None` means "this classification call is not considering source-lines
    precision at all" — every pre-v2.6.4 caller and every existing unit test
    in this file omits it, and for THOSE call sites `None` preserves the
    exact prior CORPUS_TESTING_READY behavior unchanged (no regression).
    The REAL canonical call site (Stage 8 / stages.trust_ledger, see
    build_corpus_trust_ledger()) never passes None in real usage — it always
    supplies a concrete summary (even one with `tested: False`), because a
    chapter processed under v2.6.4+ genuinely always has Stage 8 either run
    or explicitly skipped, and either way that fact is real evidence, not an
    "opt out of this check" signal the way an ad hoc unit test's omission is.
    Passing an explicit `{"tested": False, ...}` (as the real Stage 8 caller
    does for a chapter that hasn't been precision-checked yet) demotes an
    otherwise-CORPUS_TESTING_READY result to CORPUS_REVIEW_PENDING; passing
    `None` does not.

    `protection_marker`: the loaded `CORPUS_OUTPUT_PROTECTED.json` dict, or
    None. Disclosed in the result as `protection_marker_present` ONLY — per
    the task's explicit requirement, this is a separate SAFETY field, never
    an input to the trust/classification decision itself (a chapter is not
    more or less trusted for having, or lacking, this marker).

    v2.6.5 additions (emergency fix — see V2_6_5_EMERGENCY_INTEGRITY_FIX_REPORT.md):
    found on Chapter 14 that a chapter could reach `CORPUS_TESTING_READY` /
    `trusted_for_downstream_use: True` while Stage 4.6's semantic-type review
    covered only 45 of 283 flagged candidates and 18 of 35 Stage 4.7
    completeness clusters were genuinely undetermined — because this
    classifier never looked at either stage at all. A single broad
    `trusted_for_downstream_use` boolean must never conceal that kind of
    incomplete review.

    `stage_4_6_review_status`: the chapter's Stage 4.6 checkpoint `status`
    string (e.g. "COMPLETED", "IN_PROGRESS"), or None. `None` preserves
    prior behavior exactly (not considered — every pre-v2.6.5 call site and
    unit test omits it). A concrete value other than "COMPLETED" demotes an
    otherwise-CORPUS_TESTING_READY result to CORPUS_REVIEW_PENDING.

    `unresolved_completeness_clusters`: count of Stage 4.7 SCATTERED disease
    clusters whose genuine-gap-vs-artifact status was never determined
    (i.e. NOT the raw SCATTERED count — a chapter can legitimately have
    triaged SCATTERED entries down to zero unresolved ones and still reach
    CORPUS_TESTING_READY), or None (not considered, prior behavior
    preserved). A value > 0 demotes to CORPUS_REVIEW_PENDING.

    The result dict also always reports three explicit sub-status booleans
    (`semantic_metadata_review_complete`, `completeness_review_complete`,
    `retrieval_ready`) so a reader never has to infer partial review status
    from the single aggregate classification/boolean alone — see each
    field's None-vs-True-vs-False semantics in `result()` below.

    v2.6.6 additions (Fail-Closed Finalization — see
    V2_6_6_FAIL_CLOSED_FINALIZATION_REPORT.md): found on Chapter 11 that a
    checkpoint that never recorded `stage_completions["4.7"]
    ["unresolved_completeness_clusters"]` at all reached CORPUS_TESTING_READY
    anyway, because the v2.6.5 parameters above treat `None` as "not
    considered" for EVERY caller, including a real production chapter whose
    evidence field is genuinely missing. That "None = skip this gate" design
    is correct for a chapter that never reached the corpus_completed+gate_pass
    milestone at all (this classifier's early-return LEGACY_* paths), and for
    hand-written unit tests intentionally simulating those legacy paths — but
    it is wrong for a chapter that DID reach that milestone: at that point,
    every one of Stage 4.6's status/chunks_reviewed/total_flagged, Stage 4.7's
    unresolved_completeness_clusters, and Stage 8's tested/unresolved_count is
    now MANDATORY evidence. Once execution reaches the
    `corpus_completed and gate_pass` branch below, `None` (or any malformed
    value — wrong type, negative, or a `bool` where an `int` count is
    expected; see `_bad_count()`) for any of these fields means "evidence is
    missing," never "not considered," and demotes to CORPUS_REVIEW_PENDING
    with a reason naming the exact missing/malformed field. This is an
    additive tightening of that one branch only — the LEGACY_* early-return
    paths above it, and their existing unit tests, are completely unchanged.

    `stage_4_6_chunks_reviewed` / `stage_4_6_total_flagged` (new in v2.6.6):
    the chapter's Stage 4.6 checkpoint `chunks_reviewed` / `total_flagged`
    counts, or None. Both must be explicitly present, well-formed
    non-negative ints, and `chunks_reviewed >= total_flagged`, or the
    chapter demotes to CORPUS_REVIEW_PENDING — this is the exact gap that let
    a chapter with `status: "COMPLETED"` but a genuinely partial review
    (e.g. 45 of 283 flagged candidates actually reviewed) go undetected,
    because the pre-v2.6.6 classifier had no parameter to receive these
    counts at all.
    """
    def result(classification, trusted, reasons, required_action):
        d = _result(classification, trusted, reasons, required_action)
        d["protection_marker_present"] = protection_marker is not None
        # v2.6.5: explicit sub-status booleans, independent of the single
        # aggregate classification — None means "not evaluated this call"
        # (caller didn't pass the relevant evidence), never silently True.
        d["semantic_metadata_review_complete"] = (
            None if stage_4_6_review_status is None else stage_4_6_review_status == "COMPLETED"
        )
        d["completeness_review_complete"] = (
            None if unresolved_completeness_clusters is None else unresolved_completeness_clusters == 0
        )
        # This pipeline does not implement retrieval, embeddings, or any
        # retrieval-quality evaluation (explicitly out of scope per the
        # code-freeze policy) -- always False, never inferred from
        # RAG_Optimised.md's mere existence or any other proxy signal.
        d["retrieval_ready"] = False
        return d

    if checkpoint is None:
        if has_stage6_validation_file and has_coverage_gaps_file:
            return result(
                "LEGACY_UNCHECKPOINTED", False,
                ["No checkpoint file exists for this chapter.",
                 "Stage6_Validation.md and L1L2_CoverageGaps.md exist on disk, indicating an "
                 "ad hoc (non-checkpointed) script run reached those stages, but with no "
                 "verifiable checkpoint trail behind that claim."],
                "Full canonical rerun through the checkpointed pipeline required for certification.",
            )
        return result(
            "LEGACY_UNGATED", False,
            ["No checkpoint file exists for this chapter.",
             "No Stage6_Validation.md / L1L2_CoverageGaps.md evidence that any process ever "
             "reached Stage 4.5c or Stage 6, checkpointed or not."],
            "Full canonical rerun from Stage 1 required.",
        )

    sc = checkpoint.get("stage_completions", {})
    ps = checkpoint.get("pipeline_state", {})
    has_4_5c = "4.5c" in sc
    has_4_5d = "4.5d" in sc

    if not has_4_5c:
        reasons = [
            "Checkpoint exists but predates Stage 4.5c (no '4.5c' key in stage_completions).",
            "Checkpoints predating Stage 4.5c cannot be upgraded to corpus-certified status "
            "by metadata migration alone — required blocking-stage evidence does not exist "
            "and cannot be reconstructed without fabricating provenance.",
        ]
        if ps.get("pipeline_status") == "COMPLETED":
            reasons.append(
                "Historical pipeline_status=='COMPLETED' (pre-v2.6.0 literal string) is NOT "
                "equivalent to current CORPUS_PIPELINE_COMPLETED — it reflects completion "
                "under a rule set that lacked Stage 4.5c and Stage 4.5d entirely."
            )
        return result("LEGACY_STALE_CHECKPOINT", False, reasons, "FULL_CANONICAL_RERUN_REQUIRED")

    if not has_4_5d:
        return result(
            "LEGACY_UNGATED", False,
            ["Checkpoint reached Stage 4.5c but has no '4.5d' entry — predates the v2.6.0 "
             "clinical fidelity gate, or never completed that stage."],
            "Rerun from Stage 4.5d forward through Stage 6.",
        )

    # L7: STALE is an explicit statement that this evidence was produced
    # before an earlier stage was re-completed. Old evidence files may still
    # look clean on disk, so trust must follow the checkpoint lifecycle and
    # fail closed until every stale stage is genuinely revalidated.
    stale_stages = [
        stage for stage in checkpoint_utils.STAGE_ORDER
        if isinstance(sc.get(stage), dict) and sc[stage].get("status") == "STALE"
    ]
    if stale_stages:
        return result(
            "CORPUS_REVIEW_PENDING", False,
            ["Checkpoint contains stale downstream evidence after an earlier-stage re-run: "
             + ", ".join(stale_stages) + "."],
            f"Resume from Stage {stale_stages[0]} and re-run every required downstream stage "
            "through Stage 8; then re-run finalize_trusted_chapter.py and "
            "verify_trusted_corpus_invariants.py before trusted use.",
        )

    corpus_completed = bool(ps.get("corpus_pipeline_completed", False))
    gate_pass = bool(clinical_fidelity_gate) and clinical_fidelity_gate.get("verdict") == "PASS"

    # `corpus_pipeline_completed` is a monotonic milestone flag: marking a later stage BLOCKED/FAILED
    # (e.g. after a forced re-run) never cleared it. A gating stage that is present but not COMPLETED
    # must withdraw trust no matter what the flag says.
    open_gates = {k: sc[k].get("status") for k in ("4.5", "4.5c", "4.5d", "6")
                  if k in sc and isinstance(sc[k], dict) and sc[k].get("status") != "COMPLETED"}
    if corpus_completed and open_gates:
        return result(
            "CORPUS_REVIEW_PENDING", False,
            [f'stage_completions["{k}"]["status"] = {v!r}, not "COMPLETED" -- a gating stage is open, so '
             f'the corpus_pipeline_completed milestone no longer holds.' for k, v in sorted(open_gates.items())],
            "Re-run the open gating stage(s) to COMPLETED (and every stage after them) before certification.",
        )

    if corpus_completed and gate_pass:
        # v2.6.6 (Fail-Closed Finalization): every evidence field checked in
        # this branch is now MANDATORY — None or malformed means "missing,"
        # never "not considered." This is the systemic fix for the Chapter 11
        # defect (a genuinely missing stage_completions["4.7"]
        # ["unresolved_completeness_clusters"] key used to be silently
        # skipped). Checked in the order the task's evidence-requirement list
        # gives: Stage 4.6 status, Stage 4.6 counts, Stage 4.7, Stage 8.

        # --- Stage 4.6 status: must be explicitly present and == "COMPLETED".
        if stage_4_6_review_status != "COMPLETED":
            reasons = [
                "Stage 6 passed and Stage 4.5d gate verdict == PASS, but mandatory Stage 4.6 "
                "semantic-type review evidence is missing or incomplete: "
                f'stage_completions["4.6"]["status"] = {stage_4_6_review_status!r} (expected the '
                'string "COMPLETED", explicitly present). Trust cannot be granted until this '
                "evidence is recorded."
            ]
            return result(
                "CORPUS_REVIEW_PENDING", False, reasons,
                "Complete Stage 4.6 review of every regex-flagged candidate (see that stage's "
                "review_completeness_ratio), record status==\"COMPLETED\" in the checkpoint, then "
                "re-run trust classification.",
            )

        # --- Stage 4.6 counts: chunks_reviewed and total_flagged must both be
        # explicitly present, well-formed non-negative ints, with
        # chunks_reviewed >= total_flagged (a partial review must not pass
        # merely because status says "COMPLETED").
        if _bad_count(stage_4_6_chunks_reviewed) or _bad_count(stage_4_6_total_flagged):
            missing = []
            if _bad_count(stage_4_6_chunks_reviewed):
                missing.append(f'stage_completions["4.6"]["chunks_reviewed"] '
                                f'(got {stage_4_6_chunks_reviewed!r})')
            if _bad_count(stage_4_6_total_flagged):
                missing.append(f'stage_completions["4.6"]["total_flagged"] '
                                f'(got {stage_4_6_total_flagged!r})')
            reasons = [
                "Stage 6 passed and Stage 4.5d gate verdict == PASS, but mandatory Stage 4.6 "
                "completeness-count evidence is missing or malformed: " + "; ".join(missing) +
                ". Trust cannot be granted until this evidence is recorded."
            ]
            return result(
                "CORPUS_REVIEW_PENDING", False, reasons,
                "Record well-formed non-negative int chunks_reviewed and total_flagged counts in "
                "stage_completions[\"4.6\"], then re-run trust classification.",
            )
        if stage_4_6_chunks_reviewed < stage_4_6_total_flagged:
            reasons = [
                "Stage 6 passed and Stage 4.5d gate verdict == PASS, but Stage 4.6 review is "
                f"incomplete: chunks_reviewed ({stage_4_6_chunks_reviewed}) < total_flagged "
                f"({stage_4_6_total_flagged}) — a chapter must not be marked trusted while "
                "regex-flagged candidates remain unreviewed."
            ]
            return result(
                "CORPUS_REVIEW_PENDING", False, reasons,
                "Review every remaining regex-flagged candidate until chunks_reviewed >= "
                "total_flagged, then re-run trust classification.",
            )

        # --- Stage 4.7: unresolved_completeness_clusters must be explicitly
        # present, a well-formed non-negative int, and == 0.
        if _bad_count(unresolved_completeness_clusters):
            reasons = [
                'Mandatory Stage 4.7 evidence is missing: stage_completions["4.7"]'
                f'["unresolved_completeness_clusters"] (got {unresolved_completeness_clusters!r}). '
                "Trust cannot be granted until this evidence is recorded."
            ]
            return result(
                "CORPUS_REVIEW_PENDING", False, reasons,
                "Record a well-formed non-negative int unresolved_completeness_clusters count in "
                "stage_completions[\"4.7\"] (see Stage 4.7's Rule L triage), then re-run trust "
                "classification.",
            )
        if unresolved_completeness_clusters != 0:
            return result(
                "CORPUS_REVIEW_PENDING", False,
                ["Stage 6 passed and Stage 4.5d gate verdict == PASS, but "
                 f"{unresolved_completeness_clusters} Stage 4.7 completeness cluster(s) have "
                 "undetermined genuine-gap-vs-artifact status — a chapter must not be marked "
                 "trusted while mandatory completeness review remains outstanding."],
                "Resolve every undetermined SCATTERED cluster (confirm genuine gap requiring "
                "Tier 2/3 follow-up, or confirm non-issue) per Stage 4.7's Rule L, then re-run "
                "trust classification.",
            )

        # --- Stage 8: source_lines_precision_summary must be an explicitly
        # supplied dict with tested==True and a well-formed unresolved_count
        # == 0.
        precision_is_dict = isinstance(source_lines_precision_summary, dict)
        tested = bool(source_lines_precision_summary.get("tested", False)) if precision_is_dict else False
        unresolved = source_lines_precision_summary.get("unresolved_count", None) if precision_is_dict else None
        precision_evidence_missing = (not precision_is_dict) or (not tested) or _bad_count(unresolved)
        if precision_evidence_missing:
            reasons = [
                "Mandatory Stage 8 (source-lines precision) evidence is missing or incomplete: "
                f"source_lines_precision_summary={source_lines_precision_summary!r}. Trust cannot "
                "be granted until this evidence is recorded (Stage 8 has not run, tested==False, "
                "or unresolved_count is missing/malformed)."
            ]
            return result(
                "CORPUS_REVIEW_PENDING", False, reasons,
                "Run Stage 8 (source_lines precision) if not yet run, then adjudicate every "
                "non-PRECISE finding (CHECKER_FALSE_POSITIVE or HUMAN_CONFIRMED_METADATA_DEFECT "
                "+ correction/recheck) before this chapter can reach CORPUS_TESTING_READY.",
            )
        if unresolved != 0:
            reasons = [
                "Stage 6 passed and Stage 4.5d gate verdict == PASS, but source-lines precision "
                "review is not yet clean — an unresolved source-line mapping cannot receive "
                "CORPUS_TESTING_READY.",
                f"{unresolved} source-lines finding(s) remain unresolved (no adjudication decision "
                "recorded, or a confirmed metadata defect not yet corrected and rechecked).",
            ]
            return result(
                "CORPUS_REVIEW_PENDING", False, reasons,
                "Adjudicate every non-PRECISE finding (CHECKER_FALSE_POSITIVE or "
                "HUMAN_CONFIRMED_METADATA_DEFECT + correction/recheck) before this chapter can "
                "reach CORPUS_TESTING_READY.",
            )

        return result(
            "CORPUS_TESTING_READY", True,
            ["Stage 6 passed (pipeline_state.corpus_pipeline_completed == True).",
             "Stage 4.5d ClinicalFidelityGate.json verdict == PASS.",
             "Stage 4.6 semantic-type review complete (status==\"COMPLETED\", "
             f"chunks_reviewed={stage_4_6_chunks_reviewed} >= total_flagged={stage_4_6_total_flagged}).",
             "Stage 4.7 completeness review complete (unresolved_completeness_clusters == 0).",
             "Stage 8 source-lines precision tested and fully resolved (0 unresolved findings)."],
            "None — eligible for corpus-testing-level trusted use. Not equivalent to "
            "CORPUS_PRODUCTION_READY or any retrieval/generation/clinical/educational "
            "readiness claim.",
        )

    reasons = []
    if not corpus_completed:
        reasons.append("pipeline_state.corpus_pipeline_completed is not True.")
    if not gate_pass:
        reasons.append(
            "Stage 4.5d ClinicalFidelityGate.json is missing or its verdict is not PASS."
        )
    return result(
        "IN_PROGRESS", False, reasons,
        "Complete remaining stages and/or adjudicate outstanding Stage 4.5d candidates, "
        "then re-run Stage 6.",
    )
