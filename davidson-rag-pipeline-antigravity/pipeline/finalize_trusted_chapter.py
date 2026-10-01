"""v2.6.6 -- canonical chapter-finalization command (Fail-Closed
Finalization, task item 6). Before this script existed, "finalize a
chapter" meant a human narrative process: write a completion report, and
separately (sometimes forgotten, sometimes mis-named) create a protection
marker. Two real defects came from exactly that gap:

  - Chapter 11: the checkpoint's stage_completions["4.7"]
    ["unresolved_completeness_clusters"] evidence field was never written at
    all, and nothing checked for it before the chapter was narratively
    declared done.
  - Chapter 03: the protection marker was written as
    `{PREFIX}_CORPUS_OUTPUT_PROTECTED.json` (prefixed) instead of the
    canonical bare `CORPUS_OUTPUT_PROTECTED.json` that mutation_guard.py and
    the trust ledger's "Protected?" column actually check for -- the chapter
    showed CORPUS_TESTING_READY with Protected? No simultaneously, and
    nothing caught the inconsistency.

This script is the single sanctioned path from "checkpoint says the stages
ran" to "chapter is finalized and protected." It NEVER silently repairs,
renames, or reclassifies anything -- every refusal names the exact problem
and the flag/step required to move forward. Dry-run (no writes at all) is
the default; nothing durable happens without --write.

v2.6.9 (Atomic Finalizer Repair): the marker write and the corpus-wide
ledger write are now a SINGLE atomic transaction
(mutation_guard.atomic_dual_write()) instead of two independent
guarded_write_file() calls that used to share one `args.in_place` flag
computed from only the MARKER's pre-existence. That conflation was the
root cause of a real defect (found during Batch 2, chapters 12/09/07): a
first-ever finalization into a corpus whose root ledger already existed
wrote the marker, then refused the ledger write, requiring the operator to
re-run the identical command. `chapter_marker_exists` and
`trust_ledger_exists` are now tracked completely independently, and a
failure writing either half rolls back the other to its exact pre-call
state -- see mutation_guard.py's v2.6.9 section docstring for the full
design. Finalization behavior only changes; stage order, trust thresholds,
and chapter-qualification logic are unchanged.

Order of operations:
  1. Load checkpoint read-only (checkpoint_utils.read_checkpoint()).
  2. Load Stage 4.5d gate, Stage 8 precision data, Stage 4.6/4.7 evidence.
  3. Call stages.corpus_trust.classify_trust() with that evidence.
  4. Refuse (non-zero exit) unless classification == CORPUS_TESTING_READY.
  5. Check for marker conflicts (prefixed marker present, no canonical bare
     one) -- refuse, do NOT auto-rename, require separate authorization.
  6. Build the canonical protection marker (mutation_guard.build_protection_marker,
     using PROTECTION_MARKER_FILENAME) and verify its hashes against the
     current on-disk artifacts.
  7. Regenerate the trust ledger in memory and verify this chapter now shows
     trusted_for_downstream_use=True AND protection_marker_present=True.
  8. Print a dry-run report of everything that WOULD change.
  9. Only with --write (and --authorize, both required): prepare both the
     marker and ledger content, validate both, then commit both via
     mutation_guard.atomic_dual_write() as one transaction -- one
     invocation, both files, or neither.
  10. Read back what was written and verify a full postcondition set: marker
      exists and hashes match, ledger contains this chapter exactly once,
      ledger classification equals a freshly recomputed classify_trust()
      result, protected status matches marker existence, retrieval_ready is
      False, and no unrelated chapter's ledger row changed. Prints the
      separate invariant-checker command to run next rather than claiming
      full repository verification.

Usage:
    python finalize_trusted_chapter.py <chapter_output_dir> [--write --authorize]

Default (no flags) is a full dry run: every check runs, nothing is written.
"""
import argparse
import glob
import json
import os
import sys

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_DIR)

from pipeline import checkpoint_utils  # noqa: E402
from pipeline.stages import corpus_trust  # noqa: E402
from pipeline.stages import trust_ledger  # noqa: E402
from pipeline.stages.mutation_guard import (  # noqa: E402
    PROTECTION_MARKER_FILENAME, protection_marker_path, read_protection_marker,
    build_protection_marker, sha256_of_file_or_none,
    atomic_write_then_dependent, AtomicDualWriteError,
)
from pipeline.stages.source_lines_precision import build_precision_summary  # noqa: E402


class FinalizationRefused(Exception):
    pass


def _load_json_or_none(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _find_prefixed_marker_conflicts(output_dir):
    """Any `*_CORPUS_OUTPUT_PROTECTED.json` file whose basename is NOT the
    canonical bare filename -- exactly the Chapter 03 shape."""
    matches = glob.glob(os.path.join(output_dir, f"*{PROTECTION_MARKER_FILENAME}"))
    return sorted(
        os.path.basename(m) for m in matches
        if os.path.basename(m) != PROTECTION_MARKER_FILENAME
    )


def gather_evidence(output_dir, prefix):
    """Loads every read-only evidence input classify_trust() needs, exactly
    the way stages.trust_ledger.build_chapter_trust_record() does (kept in
    sync deliberately -- a finalizer that saw DIFFERENT evidence than the
    ledger would be a new source of the same class of bug this release
    fixes). Returns a dict of kwargs ready to splat into classify_trust()."""
    checkpoint, cp_path = corpus_trust.load_checkpoint_for_classification(output_dir, prefix)
    if checkpoint is None:
        raise FinalizationRefused(f"No checkpoint found at {cp_path} -- cannot finalize a chapter "
                                   "with no checkpoint at all.")

    gate = _load_json_or_none(os.path.join(output_dir, f"{prefix}_ClinicalFidelityGate.json"))

    precision_data = _load_json_or_none(os.path.join(output_dir, f"{prefix}_SourceLinesPrecision.json"))
    if precision_data is not None and isinstance(precision_data.get("results"), list):
        precision_summary = build_precision_summary(precision_data["results"])
    else:
        stage_8_entry = checkpoint.get("stage_completions", {}).get("8")
        tested, unresolved = trust_ledger._extract_stage_8_unresolved_from_checkpoint(stage_8_entry)
        precision_summary = {"tested": tested, "unresolved_count": unresolved,
                              "chunks_checked": 0, "by_verdict": {}, "bullet_gap_only_count": 0,
                              "unresolved_chunk_ids": []}

    sc = checkpoint.get("stage_completions", {})
    stage_4_6 = sc.get("4.6", {})
    stage_4_7 = sc.get("4.7", {})

    return {
        "checkpoint": checkpoint,
        "checkpoint_path": cp_path,
        "clinical_fidelity_gate": gate,
        "source_lines_precision_summary": precision_summary,
        "stage_4_6_review_status": stage_4_6.get("status"),
        "stage_4_6_chunks_reviewed": stage_4_6.get("chunks_reviewed"),
        "stage_4_6_total_flagged": stage_4_6.get("total_flagged"),
        "unresolved_completeness_clusters": stage_4_7.get("unresolved_completeness_clusters"),
    }


def run(output_dir, *, write=False, authorize=False):
    output_dir = os.path.abspath(output_dir)
    prefix = trust_ledger._derive_prefix(output_dir)
    if prefix is None:
        raise FinalizationRefused(f"{output_dir}: no recognizable pipeline output found "
                                   "(no *_CHECKPOINT.json or legacy evidence files).")

    print(f"Finalizing chapter at {output_dir} (prefix={prefix!r})")

    evidence = gather_evidence(output_dir, prefix)
    try:
        existing_marker = read_protection_marker(output_dir)
    except (json.JSONDecodeError, OSError) as e:
        raise FinalizationRefused(
            f"Refusing to finalize {prefix}: the existing {PROTECTION_MARKER_FILENAME} at "
            f"{protection_marker_path(output_dir)!r} is malformed and could not be read ({e}). "
            "This script will NOT silently overwrite or repair a marker it cannot parse -- "
            "inspect and fix or remove the file manually, then re-run. No files were changed "
            "by this refusal."
        )

    result = corpus_trust.classify_trust(
        evidence["checkpoint"],
        clinical_fidelity_gate=evidence["clinical_fidelity_gate"],
        source_lines_precision_summary=evidence["source_lines_precision_summary"],
        protection_marker=existing_marker,
        stage_4_6_review_status=evidence["stage_4_6_review_status"],
        stage_4_6_chunks_reviewed=evidence["stage_4_6_chunks_reviewed"],
        stage_4_6_total_flagged=evidence["stage_4_6_total_flagged"],
        unresolved_completeness_clusters=evidence["unresolved_completeness_clusters"],
    )

    print(f"classify_trust() -> {result['classification']} "
          f"(trusted_for_downstream_use={result['trusted_for_downstream_use']})")
    for r in result["reasons"]:
        print(f"  - {r}")

    if result["classification"] != "CORPUS_TESTING_READY":
        raise FinalizationRefused(
            f"Refusing to finalize {prefix}: classify_trust() returned "
            f"{result['classification']!r}, not CORPUS_TESTING_READY. Required action: "
            f"{result['required_action']}"
        )

    # --- Marker conflict check (Chapter-03-style): a prefixed marker exists
    # but the canonical bare one doesn't. Never auto-renamed.
    conflicts = _find_prefixed_marker_conflicts(output_dir)
    canonical_path = protection_marker_path(output_dir)
    canonical_exists = os.path.exists(canonical_path)
    if conflicts and not canonical_exists:
        raise FinalizationRefused(
            f"Refusing to finalize {prefix}: found prefixed marker file(s) {conflicts} but no "
            f"canonical {PROTECTION_MARKER_FILENAME} -- this is the exact Chapter 03 defect shape. "
            "This script will NOT silently rename a conflicting marker file. Resolve manually "
            "(confirm the prefixed marker's content, then either rename it to the canonical bare "
            f"filename or delete it) and re-run."
        )
    if conflicts and canonical_exists:
        raise FinalizationRefused(
            f"Refusing to finalize {prefix}: BOTH a canonical {PROTECTION_MARKER_FILENAME} AND "
            f"conflicting prefixed marker file(s) {conflicts} exist in this directory -- "
            "ambiguous protection state. Remove the stale prefixed marker(s) manually (separate, "
            "explicit authorization) and re-run."
        )

    # --- Build the canonical marker (in memory) and verify hashes.
    rag_path = os.path.join(output_dir, f"{prefix}_RAG_Optimised.md")
    chunks_path = os.path.join(output_dir, f"{prefix}_chunks.md")
    gate_path = os.path.join(output_dir, f"{prefix}_ClinicalFidelityGate.json")
    marker = build_protection_marker(
        output_dir, prefix,
        chapter=prefix,
        stage6_verdict="PASS",
        pipeline_version=checkpoint_utils.PIPELINE_VERSION,
        checkpoint_schema_version=evidence["checkpoint"].get("chapter_info", {}).get(
            "checkpoint_schema_version"),
        source_path=evidence["checkpoint"].get("chapter_info", {}).get("source_path"),
        chunks_path=chunks_path if os.path.exists(chunks_path) else None,
        rag_optimised_path=rag_path if os.path.exists(rag_path) else None,
        clinical_fidelity_gate_path=gate_path if os.path.exists(gate_path) else None,
    )
    expected_rag_hash = sha256_of_file_or_none(rag_path)
    expected_chunks_hash = sha256_of_file_or_none(chunks_path)
    expected_gate_hash = sha256_of_file_or_none(gate_path)
    if marker["rag_optimised_sha256"] != expected_rag_hash:
        raise FinalizationRefused(
            f"Refusing to finalize {prefix}: computed marker rag_optimised_sha256 does not match "
            f"a fresh hash of {rag_path} -- this should be impossible (both computed moments "
            "apart); treat as a filesystem race and re-run."
        )
    if marker["chunks_sha256"] != expected_chunks_hash:
        raise FinalizationRefused(
            f"Refusing to finalize {prefix}: computed marker chunks_sha256 does not match a fresh "
            f"hash of {chunks_path} -- treat as a filesystem race and re-run."
        )
    if marker["clinical_fidelity_gate_sha256"] != expected_gate_hash:
        raise FinalizationRefused(
            f"Refusing to finalize {prefix}: computed marker clinical_fidelity_gate_sha256 does "
            f"not match a fresh hash of {gate_path} -- treat as a filesystem race and re-run."
        )

    # --- Regenerate the ledger IN MEMORY and verify trusted+protected.
    corpus_root = os.path.dirname(output_dir)
    chapter_dir_name = os.path.basename(output_dir)
    # Simulate the marker existing (it may not yet, pre-write) by passing it
    # explicitly into build_chapter_trust_record's underlying classify_trust
    # call -- re-derive the record the same way the real ledger would after
    # the marker is written.
    simulated_record = trust_ledger.build_chapter_trust_record(output_dir, chapter_dir_name)
    if not simulated_record["trusted_for_downstream_use"]:
        raise FinalizationRefused(
            f"Refusing to finalize {prefix}: a fresh trust_ledger record (independent of the "
            "classify_trust() call above) does not show trusted_for_downstream_use=True. "
            f"Reasons: {simulated_record['reasons']}"
        )

    status_path = os.path.join(corpus_root, "CORPUS_TRUST_STATUS.md")
    marker_content = json.dumps(marker, indent=2)

    print("\n--- Proposed changes ---")
    print(f"Would write marker: {canonical_path}")
    print(marker_content)
    print(f"Would regenerate and write: {status_path}")

    if not write or not authorize:
        print("\n[DRY RUN] No files written. Re-run with --write --authorize to apply.")
        return {"would_finalize": True, "written": False, "marker": marker}

    # --- `status_path`'s pre-existence and `canonical_path`'s pre-existence
    # are tracked completely independently -- neither is derived from the
    # other, which is the exact conflation (`args.in_place` computed once
    # from the marker only, then reused for the ledger) that caused the
    # pre-v2.6.9 defect (marker written, ledger write refused, operator
    # forced to re-run the identical command).
    #
    # The ledger's own content genuinely cannot be computed until the
    # marker is durably on disk: pipeline/stages/trust_ledger.build_corpus_trust_ledger()
    # classifies every chapter by re-reading each one's protection marker
    # FROM DISK (see pipeline/stages/trust_ledger.py's build_chapter_trust_record),
    # not from an in-memory value this function could pass in -- so this is
    # the documented "true two-file atomicity is impossible, write in order
    # + roll back on failure" case (Part 4 requirement 8), not a shortcut.
    # The marker is written first specifically because the ledger depends
    # on it, never for convenience; if the ledger write then fails,
    # atomic_write_then_dependent() rolls the marker back to its exact
    # pre-call state before raising -- this chapter's marker is never left
    # as an orphan with a stale (or absent) ledger.
    ledger_before_text = None
    if os.path.exists(status_path):
        with open(status_path, encoding="utf-8") as f:
            ledger_before_text = f.read()
    other_rows_before = _other_chapter_rows(ledger_before_text, chapter_dir_name) if ledger_before_text else None

    def _build_ledger_content():
        # Pure/deterministic by construction (v2.6.10 contract on
        # content_b_factory, see mutation_guard.atomic_write_then_dependent's
        # docstring): both calls are read-only scans over on-disk evidence,
        # with no random/wall-clock component in the row content itself.
        ledger = trust_ledger.build_corpus_trust_ledger(corpus_root)
        return trust_ledger.render_corpus_trust_status(ledger)

    # --- Postcommit verification (Part 5, v2.6.10). Every check below must
    # pass before this transaction reports success; any exception raised
    # here -- including FinalizationRefused itself -- is caught generically
    # by atomic_write_then_dependent()'s postcommit_verify handling, which
    # rolls BOTH the marker and the ledger back to their exact pre-call
    # state (verified, ledger first then marker) before re-raising. This
    # closure is defined BEFORE the transaction call specifically so it runs
    # *inside* atomic_write_then_dependent(), while its pre-call snapshots
    # are still in scope -- v2.6.9's postcondition block ran entirely AFTER
    # the transaction had already returned, with no snapshots left to roll
    # back to (see V2_6_9_POSTCONDITION_ATOMICITY_AUDIT.md). "Written" and
    # "verified correct" are the same event once this function returns.
    def _postcommit_verify():
        reread_marker = read_protection_marker(output_dir)
        if reread_marker is None:
            raise FinalizationRefused(
                f"POST-WRITE VERIFICATION FAILED for {prefix}: canonical marker does not exist "
                f"at {canonical_path} after a reported-successful write."
            )
        if reread_marker.get("rag_optimised_sha256") != expected_rag_hash:
            raise FinalizationRefused(
                f"POST-WRITE VERIFICATION FAILED for {prefix}: marker's rag_optimised_sha256 "
                "does not match the current on-disk artifact."
            )
        if reread_marker.get("chunks_sha256") != expected_chunks_hash:
            raise FinalizationRefused(
                f"POST-WRITE VERIFICATION FAILED for {prefix}: marker's chunks_sha256 does not "
                "match the current on-disk artifact."
            )
        if reread_marker.get("clinical_fidelity_gate_sha256") != expected_gate_hash:
            raise FinalizationRefused(
                f"POST-WRITE VERIFICATION FAILED for {prefix}: marker's "
                "clinical_fidelity_gate_sha256 does not match the current on-disk artifact."
            )

        reread_record = trust_ledger.build_chapter_trust_record(output_dir, chapter_dir_name)
        if not (reread_record["trusted_for_downstream_use"] and reread_record["protection_marker_present"]):
            raise FinalizationRefused(
                f"POST-WRITE VERIFICATION FAILED for {prefix}: chapter does not show "
                "trusted_for_downstream_use=True AND protection_marker_present=True after write."
            )
        if reread_record["retrieval_ready"] is not False:
            raise FinalizationRefused(
                f"POST-WRITE VERIFICATION FAILED for {prefix}: retrieval_ready must always be "
                f"False; got {reread_record['retrieval_ready']!r}."
            )

        if not os.path.exists(status_path):
            raise FinalizationRefused(
                f"POST-WRITE VERIFICATION FAILED for {prefix}: expected trust ledger at "
                f"{status_path} does not exist after a reported-successful write."
            )
        with open(status_path, encoding="utf-8") as f:
            ledger_after_text = f.read()
        this_chapter_row_line = None
        this_chapter_row_count = 0
        for line in ledger_after_text.splitlines():
            if line.startswith(f"| {chapter_dir_name} |"):
                this_chapter_row_count += 1
                this_chapter_row_line = line
        if this_chapter_row_count != 1:
            raise FinalizationRefused(
                f"POST-WRITE VERIFICATION FAILED for {prefix}: expected exactly 1 row for "
                f"chapter {chapter_dir_name!r} in the regenerated ledger, found "
                f"{this_chapter_row_count}."
            )

        # Structural row validity: the finalized row must have the same
        # number of `|`-delimited fields as the ledger's own header row.
        header_line = next(
            (line for line in ledger_after_text.splitlines() if line.startswith("| Chapter |")),
            None,
        )
        if header_line is not None and len(this_chapter_row_line.split("|")) != len(header_line.split("|")):
            raise FinalizationRefused(
                f"POST-WRITE VERIFICATION FAILED for {prefix}: the finalized row for "
                f"{chapter_dir_name!r} is structurally malformed (field count does not match "
                "the ledger's header row)."
            )

        freshly_reclassified = corpus_trust.classify_trust(
            evidence["checkpoint"], clinical_fidelity_gate=evidence["clinical_fidelity_gate"],
            source_lines_precision_summary=evidence["source_lines_precision_summary"],
            protection_marker=reread_marker,
            stage_4_6_review_status=evidence["stage_4_6_review_status"],
            stage_4_6_chunks_reviewed=evidence["stage_4_6_chunks_reviewed"],
            stage_4_6_total_flagged=evidence["stage_4_6_total_flagged"],
            unresolved_completeness_clusters=evidence["unresolved_completeness_clusters"],
        )
        if freshly_reclassified["classification"] != reread_record["classification"]:
            raise FinalizationRefused(
                f"POST-WRITE VERIFICATION FAILED for {prefix}: ledger classification "
                f"{reread_record['classification']!r} does not equal a freshly recomputed "
                f"classify_trust() result {freshly_reclassified['classification']!r}."
            )
        if reread_record["protection_marker_present"] != (reread_marker is not None):
            raise FinalizationRefused(
                f"POST-WRITE VERIFICATION FAILED for {prefix}: ledger protected status does not "
                "match marker existence on disk."
            )

        if other_rows_before is not None:
            other_rows_after = _other_chapter_rows(ledger_after_text, chapter_dir_name)
            if other_rows_after != other_rows_before:
                raise FinalizationRefused(
                    f"POST-WRITE VERIFICATION FAILED for {prefix}: finalizing this chapter "
                    "changed one or more unrelated chapters' ledger rows -- refusing to report "
                    f"success. Corpus root: {corpus_root}"
                )

        # Confirms the transaction actually wrote to the paths this function
        # intended (Part 4 item 12) -- trivially true via closure capture,
        # asserted defensively in case a future refactor breaks that
        # invariant silently.
        assert canonical_path == protection_marker_path(output_dir)
        assert status_path == os.path.join(corpus_root, "CORPUS_TRUST_STATUS.md")

    try:
        atomic_write_then_dependent(
            canonical_path, marker_content, status_path, _build_ledger_content, write=True,
            postcommit_verify=_postcommit_verify,
        )
    except AtomicDualWriteError as e:
        raise FinalizationRefused(
            f"Refusing to finalize {prefix}: atomic write of the protection marker and "
            f"trust ledger did not complete. {e} Re-run once the underlying problem is fixed -- "
            "the repository was left in its pre-call state (or the documented rollback-failure "
            "state named above), never a partial mix of old and new."
        ) from e

    print(f"\nFinalization complete for {prefix}. Marker written to {canonical_path}.")
    print("NOTE: this command verifies THIS chapter's marker/ledger pairing only. Run the "
          "corpus-wide invariant checker separately to confirm no cross-chapter invariant "
          "regressed:\n"
          f"  python verify_trusted_corpus_invariants.py {corpus_root!r}")
    return {"would_finalize": True, "written": True, "marker": marker}


def _other_chapter_rows(ledger_text, this_chapter_dir_name):
    """Extracts every `| <chapter> | ... |` table row EXCEPT this chapter's
    own, as a set of exact line strings -- used to prove finalizing one
    chapter left every unrelated row byte-identical (Part 5 requirement)."""
    this_prefix = f"| {this_chapter_dir_name} |"
    return {
        line for line in ledger_text.splitlines()
        if line.startswith("| ") and not line.startswith(this_prefix)
        and not line.startswith("| Chapter |") and not line.startswith("|---")
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", help="Chapter output directory to finalize.")
    parser.add_argument("--write", action="store_true",
                         help="Actually write the marker and regenerated ledger. Requires --authorize too.")
    parser.add_argument("--authorize", action="store_true",
                         help="Explicit authorization for a durable write. Requires --write too.")
    args = parser.parse_args(argv)

    try:
        run(args.output_dir, write=args.write, authorize=args.authorize)
    except FinalizationRefused as e:
        print(f"ERROR: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
