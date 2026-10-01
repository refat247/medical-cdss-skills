"""v2.6.3 — Safety Guardrails, requirements 2 & 3: non-mutating-by-default
direct runners, and the production-output protection marker.

Every direct runner script capable of writing into a chapter's output
directory should route its writes through this module rather than calling
`open(path, 'w')` directly. The contract this module enforces:

- No file is written unless the caller explicitly passed `--write` (or the
  equivalent `write=True` when called as a library).
- A file that is a MODIFICATION of an existing, already-written output
  (not a brand-new file) additionally requires `--in-place`.
- A chapter carrying a `CORPUS_OUTPUT_PROTECTED.json` marker additionally
  requires `--backup` on top of `--write --in-place` before any existing
  file may be modified — refused otherwise, with a clear error naming the
  missing flag(s).
- An in-place mutation of a protected chapter always takes a timestamped
  backup, records pre-mutation hashes, writes to a temp file first,
  validates the result, replaces atomically, then verifies final hashes —
  rolling back automatically if validation fails at any step.

`CORPUS_OUTPUT_PROTECTED.json` is a claim about corpus-gate history only:
"this output passed the current corpus gates and must not be casually
overwritten." It is NOT a regulatory, clinical, or deployment-readiness
claim — see PROTECTION_MARKER_DISCLAIMER below, which every marker embeds
verbatim so the claim can't drift from its written meaning over time.
"""
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone

PROTECTION_MARKER_FILENAME = "CORPUS_OUTPUT_PROTECTED.json"

PROTECTION_MARKER_DISCLAIMER = (
    "This marker means the chapter's output passed the current CORPUS "
    "PIPELINE gates (Stage 6 hard-fail validation + Stage 4.5d clinical "
    "fidelity gate) as of protection_timestamp, and must not be casually "
    "overwritten. It does NOT mean retrieval-validated, answer-validated, "
    "clinically safety-validated, educationally validated, or deployment-"
    "ready. See CORPUS_TRUST_STATUS.md for the chapter's actual readiness "
    "classification."
)


def unique_backup_path(bdir, base_name):
    """Backup file name that can never overwrite an earlier backup (the old one-second timestamp let two mutations
    within the same second clobber the first backup, losing the original)."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    candidate = os.path.join(bdir, f"{base_name}.pre-mutation-{ts}.bak")
    n = 1
    while os.path.exists(candidate):
        n += 1
        candidate = os.path.join(bdir, f"{base_name}.pre-mutation-{ts}-{n}.bak")
    return candidate


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_of_file(path):
    """Read-only. Raises FileNotFoundError if path doesn't exist -- callers
    that need an optional hash (file may legitimately not exist yet) should
    catch that themselves; this function never silently returns None."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def sha256_of_file_or_none(path):
    if not os.path.exists(path):
        return None
    return sha256_of_file(path)


def protection_marker_path(out_dir, prefix=None):
    """Marker is one per chapter DIRECTORY (not per-prefix-scoped like a
    checkpoint), matching the spec's "adjacent marker" framing -- a chapter
    output directory holds exactly one chapter's outputs in this pipeline's
    layout, so a bare filename in that directory is unambiguous. `prefix`
    is accepted but unused (kept for call-site symmetry with
    checkpoint_path_for) -- do not key the marker by prefix, only by
    directory, or a chapter renamed between runs could end up with two
    stale markers instead of one authoritative one."""
    return os.path.join(out_dir, PROTECTION_MARKER_FILENAME)


def read_protection_marker(out_dir, prefix=None):
    """Read-only. Returns the marker dict, or None if this chapter isn't
    (yet) protected. Never mutates, never migrates -- same discipline as
    checkpoint_utils.read_checkpoint()."""
    path = protection_marker_path(out_dir, prefix)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def is_protected(out_dir, prefix=None):
    return read_protection_marker(out_dir, prefix) is not None


def build_protection_marker(out_dir, prefix, *, chapter, stage6_verdict,
                             pipeline_version, checkpoint_schema_version,
                             source_path=None, chunks_path=None,
                             rag_optimised_path=None, clinical_fidelity_gate_path=None):
    """Builds (but does not write) the marker dict. Hash fields are None
    when the corresponding file doesn't exist rather than raising -- a
    marker documents what evidence WAS available at protection time, and a
    missing input file is itself meaningful evidence, not an error to hide
    behind a crash.
    """
    return {
        "chapter": chapter,
        "corpus_pipeline_completed": True,
        "production_output_protected": True,
        "stage_6_verdict": stage6_verdict,
        "pipeline_version": pipeline_version,
        "checkpoint_schema_version": checkpoint_schema_version,
        "source_sha256": sha256_of_file_or_none(source_path) if source_path else None,
        "chunks_sha256": sha256_of_file_or_none(chunks_path) if chunks_path else None,
        "rag_optimised_sha256": sha256_of_file_or_none(rag_optimised_path) if rag_optimised_path else None,
        "clinical_fidelity_gate_sha256": (
            sha256_of_file_or_none(clinical_fidelity_gate_path) if clinical_fidelity_gate_path else None
        ),
        "protection_timestamp": _now(),
        "disclaimer": PROTECTION_MARKER_DISCLAIMER,
    }


def write_protection_marker(out_dir, prefix, marker):
    """Explicit, deliberate write -- never called implicitly by a read path.
    Overwrites any existing marker (re-protecting after a legitimate
    re-certification is expected to replace the old marker, not append)."""
    path = protection_marker_path(out_dir, prefix)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(marker, f, indent=2)
    os.replace(tmp_path, path)
    return path


class MutationRefused(SystemExit):
    """Raised (as a SystemExit subclass, code 1) when a script refuses to
    perform a requested mutation because required flags/authorization are
    missing. A subclass of SystemExit rather than a plain exception so a
    CLI script's `raise MutationRefused(msg)` at top level behaves exactly
    like `print(msg); sys.exit(1)` without needing a try/except wrapper at
    every call site, while still being catchable by name in tests."""

    def __init__(self, message):
        super().__init__(1)
        self.message = message
        print(f"ERROR: {message}")


def add_mutation_cli_args(parser):
    """Adds the standard --output-dir/--dry-run/--write/--in-place/--backup
    flags to an argparse.ArgumentParser. `--output-dir` is added here as an
    optional override; scripts with a required positional output-dir arg
    should add that separately and treat this flag as unused, or omit
    calling this for --output-dir and add the other four individually --
    both patterns coexist in this codebase's scripts."""
    parser.add_argument("--output-dir", default=None,
                         help="Override the chapter output directory (rarely needed; "
                              "most scripts take it as a positional argument instead).")
    parser.add_argument("--dry-run", action="store_true",
                         help="Compute and report what would change; write nothing. Default "
                              "behavior even without this flag for any mutating script.")
    parser.add_argument("--write", action="store_true",
                         help="Actually write output. Required for any script that would "
                              "otherwise only report/write to a temporary location.")
    parser.add_argument("--in-place", action="store_true",
                         help="Required in addition to --write when overwriting an EXISTING "
                              "chapter output file (not just creating a new one).")
    parser.add_argument("--backup", action="store_true",
                         help="Required in addition to --write --in-place when the target "
                              "chapter is corpus-output-protected (CORPUS_OUTPUT_PROTECTED.json "
                              "present). Takes a timestamped backup before mutating.")
    return parser


def require_authorization_for_in_place_mutation(out_dir, prefix, args, *, target_description):
    """Call before any script overwrites an EXISTING chapter output file.
    Refuses (raises MutationRefused, which exits the process) unless the
    caller supplied the flags this specific situation requires:

    - Unprotected chapter: --write and --in-place.
    - Protected chapter (CORPUS_OUTPUT_PROTECTED.json present): --write,
      --in-place, AND --backup.

    Never silently downgrades a refusal to a warning -- the whole point of
    this function is that a missing flag is a hard stop, not a suggestion.
    """
    protected = is_protected(out_dir, prefix)
    missing = []
    if not getattr(args, "write", False):
        missing.append("--write")
    if not getattr(args, "in_place", False):
        missing.append("--in-place")
    if protected and not getattr(args, "backup", False):
        missing.append("--backup")

    if missing:
        marker_note = (
            " This chapter is corpus-output-protected "
            f"({PROTECTION_MARKER_FILENAME} present)." if protected else ""
        )
        raise MutationRefused(
            f"Refusing to modify {target_description} without {', '.join(missing)}."
            f"{marker_note} Re-run with the missing flag(s) to proceed, "
            f"or omit --write entirely for a read-only/report-only run."
        )
    return protected


def guarded_write_file(path, content, *, args, is_new_file, out_dir=None, prefix=None,
                        target_description=None, backup_dir=None):
    """Single entry point every mutating script should call instead of
    `open(path, 'w').write(content)`.

    - `is_new_file=True` (file does not yet exist, or the script's contract
      treats it as always-fresh output, e.g. a first-time report): requires
      only --write. No --in-place needed -- there is nothing to protect yet.
    - `is_new_file=False` (overwriting an existing file): requires
      --write --in-place (and --backup too if the chapter is protected),
      enforced via require_authorization_for_in_place_mutation().

    Without --write at all (regardless of is_new_file), performs the full
    would-be write in a *_DRYRUN.report file next to the real target instead
    of touching the real path -- so a default invocation is always provably
    non-mutating while still producing inspectable output.

    Implements the 7-step in-place protocol for existing-file mutation:
    1. timestamped backup (if protected or --backup passed)
    2. record pre-mutation hash
    3. write to a temp file
    4. validate (content is non-empty and, if JSON, parses)
    5. atomic replace (os.replace)
    6. verify post-mutation hash matches the temp file's hash (i.e. the
       replace didn't corrupt anything)
    7. automatic rollback from the backup if any step above fails

    Returns a dict describing what happened:
    {"written": bool, "path": str, "backup_path": str|None, "mode": str}
    """
    write = bool(getattr(args, "write", False))

    if not write:
        report_path = path + ".DRYRUN.report"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[DRY RUN] Would write {path} ({len(content)} bytes) -- "
              f"wrote preview to {report_path} instead. Re-run with --write to apply.")
        return {"written": False, "path": path, "backup_path": None, "mode": "dry_run"}

    if is_new_file and not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Wrote new file: {path}")
        return {"written": True, "path": path, "backup_path": None, "mode": "new_file"}

    # Existing-file mutation from here on -- full authorization + protocol.
    desc = target_description or os.path.basename(path)
    protected = require_authorization_for_in_place_mutation(out_dir, prefix, args, target_description=desc)

    backup_path = None
    pre_hash = sha256_of_file_or_none(path)
    if protected or getattr(args, "backup", False):
        bdir = backup_dir or os.path.dirname(path)
        os.makedirs(bdir, exist_ok=True)
        backup_path = unique_backup_path(bdir, os.path.basename(path))
        if os.path.exists(path):
            shutil.copyfile(path, backup_path)

    tmp_path = path + ".tmp"
    try:
        if not content.strip():
            raise ValueError(f"validation failed: new content for {path} is empty")
        if path.endswith(".json"):
            json.loads(content)  # raises if malformed

        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(content)
        tmp_hash = sha256_of_file(tmp_path)

        os.replace(tmp_path, path)

        post_hash = sha256_of_file(path)
        if post_hash != tmp_hash:
            raise RuntimeError(
                f"post-mutation hash mismatch for {path} -- atomic replace may not have "
                f"landed correctly (expected {tmp_hash}, got {post_hash})"
            )
    except Exception as e:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        if backup_path and os.path.exists(backup_path):
            shutil.copyfile(backup_path, path)
            print(f"ROLLED BACK {path} from {backup_path} after validation failure: {e}")
        raise

    print(f"Mutated existing file: {path}" + (f" (backup: {backup_path})" if backup_path else "")
          + f" | pre_hash={pre_hash} post_hash={post_hash}")
    return {"written": True, "path": path, "backup_path": backup_path, "mode": "in_place_mutation"}


# --------------------------------------------------------------------------
# v2.6.9 -- Atomic Finalizer Repair
# --------------------------------------------------------------------------
#
# Root cause of the pre-v2.6.9 defect: finalize_trusted_chapter.py wrote a
# chapter's CORPUS_OUTPUT_PROTECTED.json marker and the corpus-wide
# CORPUS_TRUST_STATUS.md ledger as two independent guarded_write_file()
# calls sharing ONE `args.in_place` flag computed from only the MARKER's
# pre-existence (`args.in_place = os.path.exists(canonical_path)`). A
# first-ever finalization (marker absent) into a corpus whose root ledger
# already existed -- the normal case after even one prior chapter was
# finalized -- wrote the marker successfully (new-file path, no in_place
# check), then had that same `in_place=False` flag incorrectly applied to
# the ledger write, which IS an existing-file mutation and therefore
# required `in_place=True` -- refused, leaving the marker written but the
# ledger stale until the operator re-ran the identical command.
#
# atomic_dual_write() replaces that two-call, shared-flag pattern with a
# single transaction over two independently-tracked targets: each target's
# new-vs-existing state is derived from ITS OWN on-disk presence, both
# contents are validated before either destination is touched, and a
# failure writing the second target rolls back the first to its exact
# pre-call state (restored from an in-memory snapshot, or removed if it was
# a brand-new file) before raising -- so a failed invocation never leaves
# "new marker + old ledger" or "old marker + new ledger" on disk.


class AtomicDualWriteError(Exception):
    """Raised when a two-file atomic transaction cannot complete with both
    files landing in a consistent, paired state. By the time this is
    raised, disk state is guaranteed to match either the pre-call state
    (both files rolled back) or a documented irrecoverable-rollback
    state named explicitly in the message -- never a silent partial update.
    Deliberately a plain Exception (not a SystemExit subclass like
    MutationRefused) -- this reports a failed TRANSACTION, not a missing
    authorization flag."""


class RollbackVerificationFailed(AtomicDualWriteError):
    """v2.6.10. Raised when a restore call returned without exception, but
    the post-rollback bytes still don't match the pre-call snapshot (or a
    file that should have been removed still exists) -- including the
    partial case where ONE of two files in a postcommit rollback restored
    correctly and the other did not, leaving a documented mismatched-pair
    degraded state (see `_rollback_dual_after_postcommit`). A subclass of
    `AtomicDualWriteError` so every existing `except AtomicDualWriteError`
    call site still catches it unchanged, while a caller that wants to
    distinguish "rollback happened cleanly" from "rollback itself needs
    manual intervention" can catch this specifically."""


def _read_bytes_or_none(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return f.read()


def _validate_write_content(path, content):
    if not content.strip():
        raise ValueError(f"validation failed: new content for {path} is empty")
    if path.endswith(".json"):
        json.loads(content)  # raises if malformed


def _remove_if_exists(path, cleanup_failures=None):
    """Best-effort tmp-file removal. Never raises -- a failure to clean up a
    stray temp file must never mask (or be conflated with) the real error
    that's already propagating, so it's recorded into `cleanup_failures`
    (a caller-supplied mutable list) instead, and surfaced explicitly in
    whatever message the caller ultimately raises (see `_cleanup_note()`).
    """
    if not os.path.exists(path):
        return
    try:
        os.remove(path)
    except Exception as e:
        if cleanup_failures is not None:
            cleanup_failures.append((path, e))


def _sweep_stray_temp_files(path_a, path_b, cleanup_failures):
    """v2.6.10. Best-effort final sweep for `.atomictmp`/`.rollbacktmp`
    artifacts of EITHER transaction file, run once at every transaction
    exit (success, write-phase failure, and postcommit-failure/rollback
    alike) -- not just the inline cleanup each low-level write/restore
    already does in its own except block. Catches the case where a tmp
    file survives from a moment this function's own inline cleanup didn't
    cover (e.g. a stray artifact left by an interrupted prior run in the
    same directory) so "no transaction temp file remains" is checked
    holistically, not only for the tmp file this specific call created.
    Failures are recorded into `cleanup_failures`, never raised -- see
    `_cleanup_note()`, which is what actually surfaces them."""
    for base in (path_a, path_b):
        for suffix in (".atomictmp", ".rollbacktmp"):
            stray = base + suffix
            if os.path.exists(stray):
                try:
                    os.remove(stray)
                except Exception as e:
                    cleanup_failures.append((stray, e))


def _cleanup_note(cleanup_failures):
    """Always-present, explicit temp-file-cleanup status line for every
    message this module raises after a write/rollback attempt -- never
    silently omitted, whether cleanup succeeded or not (v2.6.10 requirement:
    temp-file cleanup failures must be reported, not swallowed just because
    the more important restore/verify step already succeeded)."""
    if not cleanup_failures:
        return "Temp file cleanup: OK."
    parts = "; ".join(f"{p} ({e})" for p, e in cleanup_failures)
    return f"Temp file cleanup: FAILED for {parts}."


def _describe_bytes(b):
    if b is None:
        return "absent"
    return f"{len(b)} bytes (sha256={hashlib.sha256(b).hexdigest()})"


def _atomic_replace_file(path, content, *, cleanup_failures=None):
    """Write `content` to `path` via temp-file + fsync + os.replace, never a
    direct in-place open('w'). Applies to BOTH brand-new and existing
    targets -- unlike guarded_write_file()'s new-file path (a direct
    open('w').write(), acceptable there since that function's callers only
    ever mutate one target at a time), a participant in a two-file
    transaction must be crash-safe and hash-verified even on first write,
    since this function's caller may need to roll it back a moment later.

    v2.6.10: the verification hash is now computed from `content` itself
    (`expected_hash`), not merely from the temp file post-write
    (`tmp_hash == post_hash`, the pre-v2.6.10 check). The old check only
    proved `os.replace()` didn't corrupt anything IN TRANSIT between the
    temp file and the destination -- it never tied either hash back to the
    content the caller actually asked to write, so a hypothetical write-path
    bug (wrong encoding, a truncated write) upstream of the temp file would
    have gone undetected. Both the temp-file write and the final destination
    are now checked against `expected_hash` independently: "marker bytes ==
    content_a" / "ledger bytes == expected_ledger_content" is an explicit,
    machine-checked invariant, not an assumption.
    """
    tmp_path = path + ".atomictmp"
    expected_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    try:
        # newline="" disables universal-newline translation -- without it,
        # Python's text-mode write silently rewrites "\n" -> "\r\n" on
        # Windows, so the on-disk bytes would never match a hash computed
        # directly from `content.encode("utf-8")" (discovered while adding
        # this content-equality check in v2.6.10: it false-failed on every
        # write on this platform until this was added).
        with open(tmp_path, "w", encoding="utf-8", newline="") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        tmp_hash = sha256_of_file(tmp_path)
        if tmp_hash != expected_hash:
            raise RuntimeError(
                f"content-equality check failed writing {tmp_path} -- temp file bytes do not "
                f"match the intended content (expected sha256={expected_hash}, got {tmp_hash}); "
                "refusing to replace the real target with unverified content."
            )
        os.replace(tmp_path, path)
    except Exception:
        _remove_if_exists(tmp_path, cleanup_failures)
        raise

    post_hash = sha256_of_file(path)
    if post_hash != expected_hash:
        raise RuntimeError(
            f"post-mutation hash mismatch for {path} -- atomic replace may not have "
            f"landed correctly (expected {expected_hash}, got {post_hash})"
        )
    return post_hash


def _restore_or_remove(path, original_bytes, *, cleanup_failures=None):
    """Rollback primitive: put `path` back exactly how it was before this
    transaction touched it. `original_bytes is None` means the file did not
    exist before the transaction -- rollback means removing it, not writing
    an empty file. Uses the same temp+fsync+replace discipline as a forward
    write so the rollback itself is crash-safe. Does NOT itself verify the
    restore landed correctly -- see `_restore_and_verify()`, which wraps
    this with an explicit post-restore byte comparison; this function is
    the mechanical "do the restore" half only."""
    if original_bytes is None:
        if os.path.exists(path):
            os.remove(path)
        return
    tmp_path = path + ".rollbacktmp"
    try:
        with open(tmp_path, "wb") as f:
            f.write(original_bytes)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        _remove_if_exists(tmp_path, cleanup_failures)
        raise


def _restore_and_verify(path, original_bytes, *, backup_path=None, cleanup_failures=None):
    """v2.6.10. `_restore_or_remove()` plus an explicit post-restore read-back
    and byte comparison against `original_bytes` -- a restore call returning
    without exception is NOT treated as proof the restore actually worked.
    On mismatch (or the file still existing when it should have been
    removed, or vice versa), raises `RollbackVerificationFailed` naming the
    file, its expected state, its actual state, and the timestamped backup
    path for manual recovery -- this is the "hash check" (implemented as a
    stronger direct byte comparison, since `original_bytes` is already in
    memory) that guarantees rollback correctness is verified, not assumed.
    """
    _restore_or_remove(path, original_bytes, cleanup_failures=cleanup_failures)
    current = _read_bytes_or_none(path)
    if current != original_bytes:
        raise RollbackVerificationFailed(
            f"ROLLBACK VERIFICATION FAILED for {path}: restore call returned without exception "
            "but post-rollback state does not match the pre-call snapshot. "
            f"Expected: {_describe_bytes(original_bytes)}. Actual: {_describe_bytes(current)}. "
            f"Timestamped backup (if any): {backup_path!r}. MANUAL RECOVERY REQUIRED: compare "
            "the current file against the backup path above (or reconstruct from version "
            "control) and restore by hand; do not trust this file's current on-disk content "
            "until manually verified."
        )


def _timestamped_backup(path, original_bytes, backup_dir=None):
    if original_bytes is None:
        return None
    bdir = backup_dir or os.path.dirname(path)
    os.makedirs(bdir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = os.path.join(bdir, f"{os.path.basename(path)}.pre-mutation-{ts}.bak")
    with open(backup_path, "wb") as f:
        f.write(original_bytes)
    return backup_path


def _rollback_single(path, original_bytes, was_new, backup_path, *,
                      failing_path, original_error, cleanup_failures):
    """Write-phase rollback: `path` (path_a) is the only file that was ever
    committed when `failing_path` (path_b)'s write/preparation failed --
    path_b's real target was never touched (os.replace() is atomic; a
    failure before it runs leaves the destination untouched, and a failure
    during/after it would have already raised). v2.6.10: the restore is now
    verified (`_restore_and_verify`, not the old unverified
    `_restore_or_remove`), so a rollback that silently didn't take effect is
    no longer possible here either -- always raises."""
    try:
        _restore_and_verify(path, original_bytes, backup_path=backup_path,
                             cleanup_failures=cleanup_failures)
    except RollbackVerificationFailed as e:
        _sweep_stray_temp_files(path, failing_path, cleanup_failures)
        raise RollbackVerificationFailed(
            f"failed preparing/writing {failing_path}: {original_error}. "
            f"ROLLBACK OF {path} ALSO FAILED VERIFICATION: {e} "
            f"{_cleanup_note(cleanup_failures)}"
        ) from original_error
    except Exception as e:
        _sweep_stray_temp_files(path, failing_path, cleanup_failures)
        raise AtomicDualWriteError(
            f"failed preparing/writing {failing_path}: {original_error}. ROLLBACK OF {path} "
            f"ALSO FAILED ({e}) -- repository may be in an inconsistent state; "
            f"manual intervention required: compare against the timestamped backup "
            f"{backup_path!r} and restore by hand. {_cleanup_note(cleanup_failures)}"
        ) from original_error

    _sweep_stray_temp_files(path, failing_path, cleanup_failures)
    raise AtomicDualWriteError(
        f"failed preparing/writing {failing_path}: {original_error}. Rolled back {path} to its"
        f"pre-call state ({'removed (was new)' if was_new else 'restored from snapshot, byte-verified'}); "
        f"no partial update was left on disk. {_cleanup_note(cleanup_failures)}"
    ) from original_error


def _rollback_dual_after_postcommit(path_b, original_b, backup_path_b,
                                     path_a, original_a, backup_path_a,
                                     *, original_error, cleanup_failures):
    """v2.6.10. Both `path_a` (marker) and `path_b` (ledger) are ALREADY
    durably committed when this is called -- `postcommit_verify()` raised
    after a genuinely successful two-file commit. Restores `path_b` FIRST,
    then `path_a` SECOND -- reverse commit order, per the task's explicit
    requirement, minimizing how long an observer could see a mismatched
    pair. Both restores are always attempted regardless of whether the
    first one fails, so neither file is ever left un-tried.

    FIX 2 (partial-failure handling): if the ledger restore succeeds but the
    marker restore then fails, this code deliberately does NOT attempt to
    re-run `content_b_factory()` and re-write the ledger to "match" the
    still-new, un-rolled-back marker. Automated recovery after one restore
    has already failed is exactly the "no automated recovery is safe to
    attempt blind" scenario the v2.6.9 report's own limitations section
    already declined to automate -- compounding a failed rollback with a
    second, unattempted write only multiplies what could be wrong. Instead
    the raised error explicitly documents the resulting degraded state:
    which file is restored, which is not, and that manual reconciliation
    (not further automated writes) is required.
    """
    b_failure = None
    a_failure = None
    try:
        _restore_and_verify(path_b, original_b, backup_path=backup_path_b,
                             cleanup_failures=cleanup_failures)
    except Exception as e:
        b_failure = e
    try:
        _restore_and_verify(path_a, original_a, backup_path=backup_path_a,
                             cleanup_failures=cleanup_failures)
    except Exception as e:
        a_failure = e

    _sweep_stray_temp_files(path_a, path_b, cleanup_failures)

    if b_failure is None and a_failure is None:
        raise AtomicDualWriteError(
            "POSTCOMMIT VERIFICATION FAILED; MARKER AND LEDGER ROLLED BACK. "
            f"Original verification failure: {original_error!r}. Both {path_a} and {path_b} "
            "were restored to their exact pre-call state (byte-verified) in reverse commit "
            f"order (ledger first, marker second). {_cleanup_note(cleanup_failures)}"
        ) from original_error

    if b_failure is not None and a_failure is None:
        raise RollbackVerificationFailed(
            "POSTCOMMIT VERIFICATION FAILED and ROLLBACK PARTIALLY FAILED. "
            f"Original verification failure: {original_error!r}. "
            f"Marker ({path_a}) WAS successfully restored to its pre-call state (byte-verified). "
            f"Ledger ({path_b}) restore FAILED: {b_failure}. Backup: {backup_path_b!r}. "
            "MANUAL RECOVERY REQUIRED for the ledger only -- compare against its backup and "
            f"restore by hand. {_cleanup_note(cleanup_failures)}"
        ) from original_error

    if a_failure is not None and b_failure is None:
        raise RollbackVerificationFailed(
            "POSTCOMMIT VERIFICATION FAILED and ROLLBACK PARTIALLY FAILED -- MISMATCHED-PAIR "
            "DEGRADED STATE. "
            f"Original verification failure: {original_error!r}. "
            f"Ledger ({path_b}) WAS successfully restored to its pre-call state (byte-verified). "
            f"Marker ({path_a}) restore FAILED: {a_failure} -- it still holds its POST-COMMIT "
            "(new) content, NOT its pre-call state. The repository is now in a state "
            "structurally similar to the original pre-v2.6.9 defect pattern (old ledger + new "
            "marker). No automated second write to the ledger was attempted to reconcile this -- "
            "see this function's docstring for why. "
            f"Marker backup: {backup_path_a!r}. MANUAL RECOVERY REQUIRED: reconcile the marker "
            f"by hand against its backup, then re-run finalization. {_cleanup_note(cleanup_failures)}"
        ) from original_error

    raise RollbackVerificationFailed(
        "POSTCOMMIT VERIFICATION FAILED and ROLLBACK FAILED FOR BOTH FILES. "
        f"Original verification failure: {original_error!r}. "
        f"Ledger ({path_b}) restore FAILED: {b_failure}. Backup: {backup_path_b!r}. "
        f"Marker ({path_a}) restore FAILED: {a_failure}. Backup: {backup_path_a!r}. "
        f"MANUAL RECOVERY REQUIRED for both files. {_cleanup_note(cleanup_failures)}"
    ) from original_error


def atomic_dual_write(path_a, content_a, path_b, content_b, *, write):
    """Writes two files as a single logical transaction: either BOTH land
    correctly, or NEITHER change is left on disk after this call returns.
    Use this overload when both files' content is already fully known
    up front and neither depends on the other's on-disk state.

    Whether each target is a brand-new file or an existing-file mutation is
    determined independently, per-target, from each target's OWN on-disk
    presence at call time -- `chapter_marker_exists` and `trust_ledger_exists`
    are never conflated into a single shared flag (see module-level note
    above for the defect this replaces).

    `write=False` runs the full content-validation pass (catching a
    malformed/empty payload before any write would happen) and returns
    without touching disk at all -- used by dry-run callers.

    Returns {"written": bool, "path_a": str, "path_b": str,
    "backup_path_a": str|None, "backup_path_b": str|None,
    "was_new_a": bool, "was_new_b": bool, "temp_cleanup_ok": bool}.

    Raises AtomicDualWriteError (or its subclass RollbackVerificationFailed;
    never a bare SystemExit) if the transaction could not complete. Never
    raises a raw OSError/ValueError/json.JSONDecodeError to the caller --
    every failure mode is wrapped with what was rolled back (or, in the
    documented worst case where the rollback write itself fails, an
    explicit statement that manual intervention is required -- this is
    reported, never silently masked).
    """
    return atomic_write_then_dependent(
        path_a, content_a, path_b, lambda: content_b, write=write,
    )


def atomic_write_then_dependent(path_a, content_a, path_b, content_b_factory, *, write,
                                 postcommit_verify=None):
    """Same contract and same rollback guarantee as atomic_dual_write(), for
    the case where `path_b`'s content genuinely cannot be computed until
    `path_a` is durably on disk -- e.g. the chapter trust ledger's own
    content depends on reading the just-finalized chapter's protection
    marker back off disk (pipeline/stages/trust_ledger.py classifies each chapter by
    re-reading its marker file, not from an in-memory value passed in).
    `content_b_factory` is a zero-argument callable invoked ONLY after
    `path_a`'s write has been committed and verified; its return value is
    validated exactly like a precomputed content string before `path_b` is
    written. This is the documented "impossible to prepare both up front,
    so write in order + roll back on failure" case Part 4 explicitly
    allows -- `path_a` is written first specifically because it's the
    dependency `content_b_factory` needs, never for convenience.

    `content_b_factory` CONTRACT (v2.6.10, now explicit and required, not
    merely implied): it MUST be deterministic, pure, and idempotent --
    calling it multiple times against the same on-disk state must return
    byte-identical output every time, and it must not itself mutate any
    filesystem state. This matters because (a) `postcommit_verify` (below)
    typically independently re-derives and cross-checks content built from
    the same underlying data the factory used, so a non-deterministic
    factory could make a correct commit look like a verification failure
    (or the reverse -- mask a real one); and (b) a factory with side effects
    would make the "roll back path_a only, path_b untouched" write-failure
    branch below unsound, since a partially-applied side effect would not
    be undone by any rollback path here. This function calls
    `content_b_factory()` exactly once per transaction attempt -- it is
    never retried, so even a non-deterministic factory wouldn't corrupt a
    single run, but downstream verification logic is written assuming
    determinism and may raise spurious failures without it.

    Failure of `content_b_factory()` itself (raises before any content_b
    string exists) rolls back `path_a` exactly like a `path_b` write
    failure would.

    `postcommit_verify` (v2.6.10, new, optional, default `None`): a
    zero-argument callable invoked ONLY after BOTH `path_a` and `path_b`
    are durably committed, while this function's pre-call byte snapshots
    (`original_a`/`original_b`) and backup paths are still in scope -- this
    is what lets a postcondition-verification failure reuse the exact same
    verified-rollback machinery a write-phase failure already uses, instead
    of the caller needing its own separate rollback logic (see
    `pipeline/finalize_trusted_chapter.py`, which used to run its postcondition
    checks entirely after this function had already returned, with no
    snapshots left to roll back to -- the exact defect this parameter
    closes). If `postcommit_verify()` raises ANY exception, both files are
    rolled back (path_b/ledger first, path_a/marker second -- reverse
    commit order) via `_rollback_dual_after_postcommit()`, which always
    raises either `AtomicDualWriteError` (clean rollback) or
    `RollbackVerificationFailed` (rollback itself did not fully succeed).
    Success is returned only once `postcommit_verify()` has returned
    normally -- "written" and "verified correct" are the same event from
    the caller's point of view once this function returns.

    The `except Exception` around the `postcommit_verify()` call is
    deliberately broad: the task contract this exists to satisfy requires
    that ANY exception during postcommit checks -- `json.JSONDecodeError`,
    `KeyError`, `TypeError`, `ValueError`, a caller-defined refusal
    exception, or a genuinely unanticipated runtime exception -- is treated
    as a verification failure that triggers rollback. A narrower catch
    (e.g. only a specific expected exception type) would let a bug in a
    verification check itself escape uncaught and leave both files
    committed with no rollback attempted -- the exact failure mode this
    release exists to close. The one deliberate exclusion is
    `BaseException` subclasses NOT covered by `Exception`
    (`KeyboardInterrupt`, `SystemExit`) -- an operator-initiated interrupt
    during verification is allowed to propagate uncaught rather than being
    silently reinterpreted as "verification failed, rolling back."
    """
    _validate_write_content(path_a, content_a)

    original_a = _read_bytes_or_none(path_a)
    original_b = _read_bytes_or_none(path_b)
    was_new_a = original_a is None
    was_new_b = original_b is None

    if not write:
        return {
            "written": False, "path_a": path_a, "path_b": path_b,
            "backup_path_a": None, "backup_path_b": None,
            "was_new_a": was_new_a, "was_new_b": was_new_b,
            "temp_cleanup_ok": True,
        }

    cleanup_failures = []
    backup_path_a = _timestamped_backup(path_a, original_a)

    try:
        _atomic_replace_file(path_a, content_a, cleanup_failures=cleanup_failures)
    except Exception as e:
        raise AtomicDualWriteError(
            f"failed writing {path_a}; no changes were committed to either target: {e}. "
            f"{_cleanup_note(cleanup_failures)}"
        ) from e

    backup_path_b = None
    try:
        content_b = content_b_factory()
        _validate_write_content(path_b, content_b)
        backup_path_b = _timestamped_backup(path_b, original_b)
        _atomic_replace_file(path_b, content_b, cleanup_failures=cleanup_failures)
    except Exception as e:
        _rollback_single(path_a, original_a, was_new_a, backup_path_a,
                          failing_path=path_b, original_error=e,
                          cleanup_failures=cleanup_failures)
        # _rollback_single() always raises.

    if postcommit_verify is not None:
        try:
            postcommit_verify()
        except Exception as e:
            # See this function's docstring: deliberately broad by design.
            _rollback_dual_after_postcommit(
                path_b, original_b, backup_path_b,
                path_a, original_a, backup_path_a,
                original_error=e, cleanup_failures=cleanup_failures,
            )
            # _rollback_dual_after_postcommit() always raises.

    _sweep_stray_temp_files(path_a, path_b, cleanup_failures)
    print(f"Atomic dual-write committed: {path_a} ({'new' if was_new_a else 'mutated'}) + "
          f"{path_b} ({'new' if was_new_b else 'mutated'})"
          + (" | postcommit_verify: OK" if postcommit_verify is not None else "")
          + f" | {_cleanup_note(cleanup_failures)}")
    return {
        "written": True, "path_a": path_a, "path_b": path_b,
        "backup_path_a": backup_path_a, "backup_path_b": backup_path_b,
        "was_new_a": was_new_a, "was_new_b": was_new_b,
        "temp_cleanup_ok": not cleanup_failures,
    }
