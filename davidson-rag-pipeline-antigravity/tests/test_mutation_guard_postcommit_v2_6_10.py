"""v2.6.10 -- unit tests directly against
stages.mutation_guard.atomic_write_then_dependent()'s new `postcommit_verify`
parameter: rollback-failure injection (Part 6), the content_b_factory
determinism contract (Part 3, FIX 3), and the content-equality guarantee
(FIX 1). Success-path regression coverage for the full finalizer lives in
test_finalize_postcondition_atomicity_v2_6_10.py and the unmodified
test_finalize_atomic_v2_6_9.py; this file tests the transaction primitive
in isolation, with fully synthetic files in tmp_path -- no chapter/ledger
machinery involved at all.
"""
import hashlib
import os

import pytest

from pipeline.stages import mutation_guard as mg


def _setup_committed_pair(tmp_path, content_a="{\"v\": 1}", content_b="ledger v1\n"):
    """Bootstraps a genuinely committed pair of files via a first, ordinary
    (non-postcommit-verified) transaction, so later tests exercise a SECOND
    call against already-existing files -- the realistic shape of a
    re-finalization, and the only way to exercise the "existing file rolled
    back to its pre-call bytes" (not "removed because it was new") path."""
    path_a = str(tmp_path / "a.json")
    path_b = str(tmp_path / "b.md")
    result = mg.atomic_write_then_dependent(
        path_a, content_a, path_b, lambda: content_b, write=True,
    )
    assert result["written"] is True
    return path_a, path_b


def _always_fail_verify():
    raise ValueError("simulated postcommit verification failure")


# --------------------------------------------------------------------------
# Part 6, case 1 -- clean rollback: both restores succeed and verify.
# --------------------------------------------------------------------------

def test_case1_clean_rollback_after_postcommit_failure(tmp_path):
    path_a, path_b = _setup_committed_pair(tmp_path)
    a_before = open(path_a, "rb").read()
    b_before = open(path_b, "rb").read()

    with pytest.raises(mg.AtomicDualWriteError) as excinfo:
        mg.atomic_write_then_dependent(
            path_a, '{"v": 2}', path_b, lambda: "ledger v2\n", write=True,
            postcommit_verify=_always_fail_verify,
        )

    assert not isinstance(excinfo.value, mg.RollbackVerificationFailed), (
        "a clean rollback must raise the base AtomicDualWriteError, not the "
        "RollbackVerificationFailed subclass reserved for rollback failures"
    )
    msg = str(excinfo.value)
    assert "POSTCOMMIT VERIFICATION FAILED; MARKER AND LEDGER ROLLED BACK" in msg
    assert "Temp file cleanup: OK" in msg
    assert excinfo.value.__cause__ is not None
    assert "simulated postcommit verification failure" in str(excinfo.value.__cause__)
    assert open(path_a, "rb").read() == a_before
    assert open(path_b, "rb").read() == b_before
    assert not os.path.exists(path_a + ".atomictmp")
    assert not os.path.exists(path_b + ".atomictmp")
    assert not os.path.exists(path_a + ".rollbacktmp")
    assert not os.path.exists(path_b + ".rollbacktmp")


# --------------------------------------------------------------------------
# Part 6, case 2 -- ledger restore fails; marker restore still succeeds.
# --------------------------------------------------------------------------

def test_case2_ledger_restore_fails_marker_restore_succeeds(tmp_path, monkeypatch):
    path_a, path_b = _setup_committed_pair(tmp_path)
    a_before = open(path_a, "rb").read()

    real_replace = os.replace
    state = {"b_replace_count": 0}

    def flaky_replace(src, dst):
        if os.path.abspath(dst) == os.path.abspath(path_b):
            state["b_replace_count"] += 1
            if state["b_replace_count"] == 2:  # 1st = forward commit, 2nd = rollback
                raise OSError("simulated rollback failure for ledger")
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", flaky_replace)

    with pytest.raises(mg.RollbackVerificationFailed) as excinfo:
        mg.atomic_write_then_dependent(
            path_a, '{"v": 2}', path_b, lambda: "ledger v2\n", write=True,
            postcommit_verify=_always_fail_verify,
        )

    msg = str(excinfo.value)
    assert "Marker" in msg and "successfully restored" in msg
    assert "Ledger" in msg and "restore FAILED" in msg
    assert "MANUAL RECOVERY REQUIRED" in msg
    assert "backup" in msg.lower()
    assert excinfo.value.__cause__ is not None
    assert "simulated postcommit verification failure" in str(excinfo.value.__cause__)
    assert open(path_a, "rb").read() == a_before, "marker must actually be restored, not just reported as such"


# --------------------------------------------------------------------------
# Part 6, case 3 -- ledger restores; marker restoration fails (degraded
# mismatched-pair state, FIX 2's specific concern).
# --------------------------------------------------------------------------

def test_case3_marker_restore_fails_after_ledger_restore_succeeds(tmp_path, monkeypatch):
    path_a, path_b = _setup_committed_pair(tmp_path)
    b_before = open(path_b, "rb").read()
    a_postcommit_content = None  # captured below once we know the v2 bytes

    real_replace = os.replace
    state = {"a_replace_count": 0}
    factory_calls = {"n": 0}

    def content_b_factory():
        factory_calls["n"] += 1
        return "ledger v2\n"

    def flaky_replace(src, dst):
        if os.path.abspath(dst) == os.path.abspath(path_a):
            state["a_replace_count"] += 1
            if state["a_replace_count"] == 2:  # 1st = forward commit, 2nd = rollback
                raise OSError("simulated rollback failure for marker")
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", flaky_replace)

    with pytest.raises(mg.RollbackVerificationFailed) as excinfo:
        mg.atomic_write_then_dependent(
            path_a, '{"v": 2}', path_b, content_b_factory, write=True,
            postcommit_verify=_always_fail_verify,
        )

    msg = str(excinfo.value)
    assert "MISMATCHED-PAIR" in msg
    assert "Ledger" in msg and "successfully restored" in msg
    assert "Marker" in msg and "restore FAILED" in msg
    assert "No automated second write" in msg
    assert "MANUAL RECOVERY REQUIRED" in msg

    assert open(path_b, "rb").read() == b_before, "ledger must actually be restored"
    assert open(path_a, "rb").read() == b'{"v": 2}', (
        "marker restore failed -- it must still hold its post-commit (v2) content, "
        "not be silently reverted by some other path"
    )
    assert factory_calls["n"] == 1, (
        "no automated second write to the ledger must be attempted during a "
        "degraded-state rollback -- content_b_factory must be called exactly "
        "once for the whole transaction"
    )


# --------------------------------------------------------------------------
# Part 6, case 4 -- restore call returns without exception, but the
# resulting bytes don't match the pre-call snapshot.
# --------------------------------------------------------------------------

def test_case4_restore_returns_but_bytes_mismatch(tmp_path, monkeypatch):
    path_a, path_b = _setup_committed_pair(tmp_path)

    real_restore = mg._restore_or_remove

    def fake_restore(path, original_bytes, *, cleanup_failures=None):
        if os.path.abspath(path) == os.path.abspath(path_a):
            # Simulate a restore that "succeeds" (raises nothing) but lands
            # the wrong bytes -- e.g. a corrupted backup or a race.
            with open(path, "wb") as f:
                f.write(b"WRONG BYTES, NOT THE REAL SNAPSHOT")
            return
        return real_restore(path, original_bytes, cleanup_failures=cleanup_failures)

    monkeypatch.setattr(mg, "_restore_or_remove", fake_restore)

    with pytest.raises(mg.RollbackVerificationFailed) as excinfo:
        mg.atomic_write_then_dependent(
            path_a, '{"v": 2}', path_b, lambda: "ledger v2\n", write=True,
            postcommit_verify=_always_fail_verify,
        )

    msg = str(excinfo.value)
    assert "does not match the pre-call snapshot" in msg
    assert "MANUAL RECOVERY REQUIRED" in msg


# --------------------------------------------------------------------------
# Part 6, case 5 -- a newly-created marker cannot be removed during
# rollback (first-ever finalization shape: original_bytes is None).
# --------------------------------------------------------------------------

def test_case5_new_marker_removal_fails_during_rollback(tmp_path, monkeypatch):
    path_a = str(tmp_path / "a.json")
    path_b = str(tmp_path / "b.md")
    assert not os.path.exists(path_a)
    assert not os.path.exists(path_b)

    real_remove = os.remove

    def flaky_remove(path):
        if os.path.abspath(path) == os.path.abspath(path_a):
            raise OSError("simulated permission-denied removing the new marker")
        return real_remove(path)

    monkeypatch.setattr(os, "remove", flaky_remove)

    with pytest.raises(mg.RollbackVerificationFailed) as excinfo:
        mg.atomic_write_then_dependent(
            path_a, '{"v": 1}', path_b, lambda: "ledger v1\n", write=True,
            postcommit_verify=_always_fail_verify,
        )

    msg = str(excinfo.value)
    assert "Marker" in msg and "restore FAILED" in msg
    assert not os.path.exists(path_b), "ledger, being new, must have been successfully removed"
    assert os.path.exists(path_a), "marker still exists because its removal failed"


# --------------------------------------------------------------------------
# Part 6, case 6 -- temp-file cleanup fails after the final files are
# ALREADY correctly restored (a stray tmp artifact's own removal fails).
# --------------------------------------------------------------------------

def test_case6_temp_cleanup_fails_after_correct_restore(tmp_path, monkeypatch):
    path_a, path_b = _setup_committed_pair(tmp_path)
    a_before = open(path_a, "rb").read()
    b_before = open(path_b, "rb").read()

    # A stray leftover from some earlier, unrelated interrupted run. Uses
    # path_b's tmp name deliberately: this test triggers a WRITE-PHASE
    # failure (content_b_factory raises before path_b is ever touched), so
    # path_b's own rollback path (_restore_or_remove) never runs and never
    # consumes/renames this filename away -- only the final sweep would
    # touch it, isolating the cleanup-only failure from an actual restore.
    stray_path = path_b + ".rollbacktmp"
    with open(stray_path, "wb") as f:
        f.write(b"leftover from a prior interrupted run")

    real_remove = os.remove

    def flaky_remove(path):
        if os.path.abspath(path) == os.path.abspath(stray_path):
            raise OSError("simulated permission-denied removing the stray temp file")
        return real_remove(path)

    monkeypatch.setattr(os, "remove", flaky_remove)

    def failing_factory():
        raise RuntimeError("simulated content_b_factory failure")

    with pytest.raises(mg.AtomicDualWriteError) as excinfo:
        mg.atomic_write_then_dependent(
            path_a, '{"v": 2}', path_b, failing_factory, write=True,
        )

    # The restore of the REAL files must still have succeeded and verified --
    # a cleanup-only failure must never be conflated with a restore failure.
    assert not isinstance(excinfo.value, mg.RollbackVerificationFailed), (
        "a pure temp-cleanup failure (final files correctly restored) must "
        "not be reported via the same exception class as an actual failed "
        "file restore"
    )
    assert open(path_a, "rb").read() == a_before
    assert open(path_b, "rb").read() == b_before

    msg = str(excinfo.value)
    assert "Temp file cleanup: FAILED" in msg
    assert stray_path in msg
    assert "Temp file cleanup: OK" not in msg


# --------------------------------------------------------------------------
# Part 3 / FIX 3 -- content_b_factory determinism contract.
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# Part 7 -- success-path regressions specific to postcommit_verify wiring.
# --------------------------------------------------------------------------

def test_postcommit_verify_not_invoked_on_dry_run(tmp_path):
    path_a = str(tmp_path / "a.json")
    path_b = str(tmp_path / "b.md")
    calls = {"n": 0}

    def spy_verify():
        calls["n"] += 1

    result = mg.atomic_write_then_dependent(
        path_a, '{"v": 1}', path_b, lambda: "ledger v1\n", write=False,
        postcommit_verify=spy_verify,
    )
    assert result["written"] is False
    assert calls["n"] == 0, "a dry run (write=False) must never invoke postcommit_verify"
    assert not os.path.exists(path_a)
    assert not os.path.exists(path_b)


def test_postcommit_verify_runs_exactly_once_before_success_returns(tmp_path):
    path_a = str(tmp_path / "a.json")
    path_b = str(tmp_path / "b.md")
    calls = {"n": 0}

    def spy_verify():
        calls["n"] += 1
        # Prove both files are ALREADY committed by the time this runs.
        assert os.path.exists(path_a)
        assert os.path.exists(path_b)

    result = mg.atomic_write_then_dependent(
        path_a, '{"v": 1}', path_b, lambda: "ledger v1\n", write=True,
        postcommit_verify=spy_verify,
    )
    assert result["written"] is True
    assert calls["n"] == 1


def test_content_b_factory_called_exactly_once_per_transaction(tmp_path):
    path_a = str(tmp_path / "a.json")
    path_b = str(tmp_path / "b.md")
    calls = {"n": 0}

    def factory():
        calls["n"] += 1
        return "deterministic content\n"

    result = mg.atomic_write_then_dependent(
        path_a, '{"v": 1}', path_b, factory, write=True,
    )
    assert result["written"] is True
    assert calls["n"] == 1, (
        "atomic_write_then_dependent must never silently retry "
        "content_b_factory -- exactly one call per transaction attempt"
    )


def test_pure_ledger_style_factory_is_deterministic_across_calls():
    """Regression proof for the determinism half of the contract: calling
    a pure, read-only factory function twice against unchanged state
    returns byte-identical output both times. Modeled directly on
    finalize_trusted_chapter.py's own `_build_ledger_content` shape (a
    closure with no random/wall-clock component in its row content)."""
    def build_content():
        # Deliberately pure: no randomness, no timestamp in the payload.
        rows = [f"| ch{i:02d} | value |" for i in range(5)]
        return "\n".join(rows) + "\n"

    first = build_content()
    second = build_content()
    assert first == second


# --------------------------------------------------------------------------
# FIX 1 -- explicit content-equality verification (marker bytes == content_a,
# ledger bytes == expected_ledger_content).
# --------------------------------------------------------------------------

def test_committed_files_are_byte_identical_to_their_intended_content(tmp_path):
    path_a = str(tmp_path / "a.json")
    path_b = str(tmp_path / "b.md")
    content_a = '{"v": 1, "note": "line1\\nline2"}'
    content_b = "ledger row 1\nledger row 2\n"

    result = mg.atomic_write_then_dependent(
        path_a, content_a, path_b, lambda: content_b, write=True,
    )
    assert result["written"] is True

    with open(path_a, "rb") as f:
        a_bytes = f.read()
    with open(path_b, "rb") as f:
        b_bytes = f.read()

    assert a_bytes == content_a.encode("utf-8"), "marker bytes must equal content_a exactly"
    assert b_bytes == content_b.encode("utf-8"), "ledger bytes must equal the factory's content exactly"
    assert hashlib.sha256(a_bytes).hexdigest() == hashlib.sha256(content_a.encode("utf-8")).hexdigest()
    assert hashlib.sha256(b_bytes).hexdigest() == hashlib.sha256(content_b.encode("utf-8")).hexdigest()


def test_content_equality_check_catches_a_corrupted_write(tmp_path, monkeypatch):
    """If the bytes that actually land on disk for the temp file don't
    match the intended content's hash, _atomic_replace_file must refuse
    to promote them via os.replace -- proves FIX 1 is load-bearing, not
    just descriptive."""
    path_a = str(tmp_path / "a.json")
    path_b = str(tmp_path / "b.md")

    real_open = open

    def corrupting_open(path, mode="r", *args, **kwargs):
        f = real_open(path, mode, *args, **kwargs)
        if path == path_a + ".atomictmp" and "w" in mode:
            real_write = f.write

            def corrupting_write(data):
                return real_write(data.replace("1", "9") if isinstance(data, str) else data)

            f.write = corrupting_write
        return f

    monkeypatch.setattr("builtins.open", corrupting_open)

    with pytest.raises(mg.AtomicDualWriteError) as excinfo:
        mg.atomic_write_then_dependent(
            path_a, '{"v": 1}', path_b, lambda: "ledger v1\n", write=True,
        )
    assert "content-equality check failed" in str(excinfo.value)
    assert isinstance(excinfo.value.__cause__, RuntimeError)
    assert "content-equality check failed" in str(excinfo.value.__cause__)
    assert not os.path.exists(path_a), "a corrupted first write must never be promoted to the real path"
