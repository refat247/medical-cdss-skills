"""v2.6.10 -- permanent regression tests converting the 8 audit reproductions
in V2_6_9_POSTCONDITION_ATOMICITY_AUDIT.md into automated tests.

V2_6_9_POSTCONDITION_ATOMICITY_AUDIT.md (read-only) proved that
`finalize_trusted_chapter.py::run()`'s postcondition checks (Part 5 of the
v2.6.9 task) run AFTER `atomic_write_then_dependent()` has already returned
and committed both the chapter marker and the corpus-wide trust ledger.
None of the 9 `raise FinalizationRefused(...)` sites in that block triggers
any rollback -- a postcondition failure leaves both files committed on disk
while the command reports non-zero exit, for all 8 injected failure
scenarios (Part 2 of that audit).

These tests inject each of the 8 failures so that the bad state is only
detectable AFTER a genuinely successful two-file commit (mirroring the
audit's own reproduction method: real writes land first, then the injected
corruption/mismatch happens, then verification runs) -- never via
`os.replace` monkeypatching at the write layer itself (that is the existing,
separate write-phase failure coverage in test_finalize_atomic_v2_6_9.py).

Run against the UNMODIFIED v2.6.9 implementation, all 8 cases are expected
to FAIL (RED) -- this file's own docstring update, once the v2.6.10 fix
lands, documents that RED result in V2_6_10_POSTCONDITION_TRANSACTION_REPAIR_REPORT.md
rather than in this file (this file only ever asserts the REQUIRED, post-fix
behavior).

Complete isolated corpus fixtures only (tmp_path) -- never the real corpus,
never a real chapter's marker or ledger.
"""
import json
import os

import pytest

from pipeline import finalize_trusted_chapter as fin
from pipeline.stages import mutation_guard, trust_ledger
from pipeline.stages.mutation_guard import PROTECTION_MARKER_FILENAME

from tests.test_finalize_atomic_v2_6_9 import _build_chapter, _base_checkpoint  # noqa: F401


def _no_stray_temp_files(*dirs):
    stray = []
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            if name.endswith((".tmp", ".atomictmp", ".rollbacktmp", ".DRYRUN.report")):
                stray.append(os.path.join(d, name))
    return stray


def _read_or_none(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return f.read()


# --------------------------------------------------------------------------
# Case 1 -- marker hash postcondition mismatch.
# --------------------------------------------------------------------------

def test_case1_marker_hash_mismatch_rolls_back_both_files(tmp_path, monkeypatch, capsys):
    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir()
    ch_dir = _build_chapter(corpus_root, "01", "Ch")
    marker_path = str(ch_dir / PROTECTION_MARKER_FILENAME)
    ledger_path = str(corpus_root / "CORPUS_TRUST_STATUS.md")

    marker_before = _read_or_none(marker_path)
    ledger_before = _read_or_none(ledger_path)

    real_read = fin.read_protection_marker

    def corrupt_hash(output_dir, prefix=None):
        marker = real_read(output_dir, prefix)
        if marker is not None:
            marker = dict(marker)
            marker["rag_optimised_sha256"] = "deadbeef" * 8
        return marker

    monkeypatch.setattr(fin, "read_protection_marker", corrupt_hash)

    with pytest.raises(fin.FinalizationRefused):
        fin.run(str(ch_dir), write=True, authorize=True)

    assert _read_or_none(marker_path) == marker_before, "marker must be rolled back to pre-call bytes"
    assert _read_or_none(ledger_path) == ledger_before, "ledger must be rolled back to pre-call bytes"
    assert _no_stray_temp_files(str(ch_dir), str(corpus_root)) == []
    assert "Finalization complete" not in capsys.readouterr().out


# --------------------------------------------------------------------------
# Case 2 -- finalized chapter row missing from committed ledger.
# --------------------------------------------------------------------------

def test_case2_finalized_row_missing_rolls_back_both_files(tmp_path, monkeypatch, capsys):
    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir()
    ch_dir = _build_chapter(corpus_root, "01", "Ch")
    marker_path = str(ch_dir / PROTECTION_MARKER_FILENAME)
    ledger_path = str(corpus_root / "CORPUS_TRUST_STATUS.md")

    marker_before = _read_or_none(marker_path)
    ledger_before = _read_or_none(ledger_path)

    real_render = trust_ledger.render_corpus_trust_status

    def drop_row(ledger):
        text = real_render(ledger)
        lines = [ln for ln in text.splitlines() if not ln.startswith("| 01 |")]
        return "\n".join(lines) + "\n"

    monkeypatch.setattr(trust_ledger, "render_corpus_trust_status", drop_row)

    with pytest.raises(fin.FinalizationRefused):
        fin.run(str(ch_dir), write=True, authorize=True)

    assert _read_or_none(marker_path) == marker_before
    assert _read_or_none(ledger_path) == ledger_before
    assert _no_stray_temp_files(str(ch_dir), str(corpus_root)) == []
    assert "Finalization complete" not in capsys.readouterr().out


# --------------------------------------------------------------------------
# Case 3 -- finalized chapter row duplicated in committed ledger.
# --------------------------------------------------------------------------

def test_case3_finalized_row_duplicated_rolls_back_both_files(tmp_path, monkeypatch, capsys):
    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir()
    ch_dir = _build_chapter(corpus_root, "01", "Ch")
    marker_path = str(ch_dir / PROTECTION_MARKER_FILENAME)
    ledger_path = str(corpus_root / "CORPUS_TRUST_STATUS.md")

    marker_before = _read_or_none(marker_path)
    ledger_before = _read_or_none(ledger_path)

    real_render = trust_ledger.render_corpus_trust_status

    def duplicate_row(ledger):
        text = real_render(ledger)
        row = next(ln for ln in text.splitlines() if ln.startswith("| 01 |"))
        return text + row + "\n"

    monkeypatch.setattr(trust_ledger, "render_corpus_trust_status", duplicate_row)

    with pytest.raises(fin.FinalizationRefused):
        fin.run(str(ch_dir), write=True, authorize=True)

    assert _read_or_none(marker_path) == marker_before
    assert _read_or_none(ledger_path) == ledger_before
    assert _no_stray_temp_files(str(ch_dir), str(corpus_root)) == []
    assert "Finalization complete" not in capsys.readouterr().out


# --------------------------------------------------------------------------
# Shared helper: call-counted monkeypatch of build_chapter_trust_record that
# behaves normally for the first N "setup" calls (pre-commit sanity check +
# in-ledger classification) and only corrupts the record on the call that
# happens AFTER both files are already committed (the postcondition reread).
# --------------------------------------------------------------------------

def _drift_record_after_commit(mutate_fn, calls_before_drift=2):
    real_build = trust_ledger.build_chapter_trust_record
    state = {"n": 0}

    def wrapper(output_dir, chapter_dir_name, **kwargs):
        rec = real_build(output_dir, chapter_dir_name, **kwargs)
        state["n"] += 1
        if state["n"] > calls_before_drift and rec is not None:
            rec = dict(rec)
            mutate_fn(rec)
        return rec

    return wrapper


# --------------------------------------------------------------------------
# Case 4 -- ledger classification differs from fresh reclassification.
# --------------------------------------------------------------------------

def test_case4_classification_drift_after_commit_rolls_back_both_files(tmp_path, monkeypatch, capsys):
    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir()
    ch_dir = _build_chapter(corpus_root, "01", "Ch")
    marker_path = str(ch_dir / PROTECTION_MARKER_FILENAME)
    ledger_path = str(corpus_root / "CORPUS_TRUST_STATUS.md")

    marker_before = _read_or_none(marker_path)
    ledger_before = _read_or_none(ledger_path)

    def mutate(rec):
        rec["classification"] = "CORPUS_REVIEW_PENDING"

    monkeypatch.setattr(trust_ledger, "build_chapter_trust_record",
                         _drift_record_after_commit(mutate))

    with pytest.raises(fin.FinalizationRefused):
        fin.run(str(ch_dir), write=True, authorize=True)

    assert _read_or_none(marker_path) == marker_before
    assert _read_or_none(ledger_path) == ledger_before
    assert _no_stray_temp_files(str(ch_dir), str(corpus_root)) == []
    assert "Finalization complete" not in capsys.readouterr().out


# --------------------------------------------------------------------------
# Case 5 -- protection_marker_present differs from marker state.
# --------------------------------------------------------------------------

def test_case5_protection_marker_present_mismatch_rolls_back_both_files(tmp_path, monkeypatch, capsys):
    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir()
    ch_dir = _build_chapter(corpus_root, "01", "Ch")
    marker_path = str(ch_dir / PROTECTION_MARKER_FILENAME)
    ledger_path = str(corpus_root / "CORPUS_TRUST_STATUS.md")

    marker_before = _read_or_none(marker_path)
    ledger_before = _read_or_none(ledger_path)

    def mutate(rec):
        rec["protection_marker_present"] = False

    monkeypatch.setattr(trust_ledger, "build_chapter_trust_record",
                         _drift_record_after_commit(mutate))

    with pytest.raises(fin.FinalizationRefused):
        fin.run(str(ch_dir), write=True, authorize=True)

    assert _read_or_none(marker_path) == marker_before
    assert _read_or_none(ledger_path) == ledger_before
    assert _no_stray_temp_files(str(ch_dir), str(corpus_root)) == []
    assert "Finalization complete" not in capsys.readouterr().out


# --------------------------------------------------------------------------
# Case 6 -- retrieval_ready incorrectly True.
# --------------------------------------------------------------------------

def test_case6_retrieval_ready_true_rolls_back_both_files(tmp_path, monkeypatch, capsys):
    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir()
    ch_dir = _build_chapter(corpus_root, "01", "Ch")
    marker_path = str(ch_dir / PROTECTION_MARKER_FILENAME)
    ledger_path = str(corpus_root / "CORPUS_TRUST_STATUS.md")

    marker_before = _read_or_none(marker_path)
    ledger_before = _read_or_none(ledger_path)

    def mutate(rec):
        rec["retrieval_ready"] = True

    monkeypatch.setattr(trust_ledger, "build_chapter_trust_record",
                         _drift_record_after_commit(mutate))

    with pytest.raises(fin.FinalizationRefused):
        fin.run(str(ch_dir), write=True, authorize=True)

    assert _read_or_none(marker_path) == marker_before
    assert _read_or_none(ledger_path) == ledger_before
    assert _no_stray_temp_files(str(ch_dir), str(corpus_root)) == []
    assert "Finalization complete" not in capsys.readouterr().out


# --------------------------------------------------------------------------
# Case 7 -- an unrelated chapter's ledger row changes.
# --------------------------------------------------------------------------

def test_case7_unrelated_chapter_row_changes_rolls_back_both_files(tmp_path, monkeypatch, capsys):
    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir()
    _build_chapter(corpus_root, "01", "ChA", finalized=True)
    ledger_path = str(corpus_root / "CORPUS_TRUST_STATUS.md")
    ledger_before_target_run = _read_or_none(ledger_path)
    a_row_before = next(
        ln for ln in ledger_before_target_run.decode("utf-8").splitlines()
        if ln.startswith("| 01 |")
    )

    ch_b = _build_chapter(corpus_root, "02", "ChB")
    marker_b_path = str(ch_b / PROTECTION_MARKER_FILENAME)
    marker_b_before = _read_or_none(marker_b_path)

    real_render = trust_ledger.render_corpus_trust_status

    def corrupt_sibling_row(ledger):
        text = real_render(ledger)
        lines = text.splitlines()
        out = []
        for ln in lines:
            if ln.startswith("| 01 |"):
                out.append(ln.replace("CORPUS_TESTING_READY", "CORPUS_REVIEW_PENDING"))
            else:
                out.append(ln)
        return "\n".join(out) + "\n"

    monkeypatch.setattr(trust_ledger, "render_corpus_trust_status", corrupt_sibling_row)
    capsys.readouterr()  # discard setup output (chapter A's own legitimate finalization)

    with pytest.raises(fin.FinalizationRefused):
        fin.run(str(ch_b), write=True, authorize=True)

    assert _read_or_none(marker_b_path) == marker_b_before, "chapter B's marker must be rolled back"
    ledger_after = _read_or_none(ledger_path)
    assert ledger_after == ledger_before_target_run, "ledger must be rolled back byte-for-byte"
    a_row_after = next(
        ln for ln in ledger_after.decode("utf-8").splitlines() if ln.startswith("| 01 |")
    )
    assert a_row_after == a_row_before
    assert _no_stray_temp_files(str(ch_b), str(corpus_root)) == []
    assert "Finalization complete" not in capsys.readouterr().out


# --------------------------------------------------------------------------
# Case 8 -- marker becomes malformed between commit and post-write reread.
# --------------------------------------------------------------------------

def test_case8_marker_malformed_before_reread_produces_controlled_error(tmp_path, monkeypatch, capsys):
    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir()
    ch_dir = _build_chapter(corpus_root, "01", "Ch")
    marker_path = str(ch_dir / PROTECTION_MARKER_FILENAME)
    ledger_path = str(corpus_root / "CORPUS_TRUST_STATUS.md")

    marker_before = _read_or_none(marker_path)
    ledger_before = _read_or_none(ledger_path)

    real_atomic_replace = mutation_guard._atomic_replace_file

    def corrupt_after_ledger_commit(path, content):
        result = real_atomic_replace(path, content)
        if os.path.abspath(path) == os.path.abspath(ledger_path):
            # Ledger just committed -- both transaction files are now durably
            # on disk. Corrupt the marker in-place, simulating it going bad
            # in the window between commit and the postcondition reread.
            with open(marker_path, "w", encoding="utf-8") as f:
                f.write("{not valid json")
        return result

    monkeypatch.setattr(mutation_guard, "_atomic_replace_file", corrupt_after_ledger_commit)

    with pytest.raises(fin.FinalizationRefused) as excinfo:
        fin.run(str(ch_dir), write=True, authorize=True)

    assert not isinstance(excinfo.value, json.JSONDecodeError)

    # Rollback must restore the marker to its pre-call state (it did not
    # exist before this call -- first-ever finalization -- so rollback means
    # removed, not left malformed) and the ledger to its pre-call state.
    assert _read_or_none(marker_path) == marker_before
    assert _read_or_none(ledger_path) == ledger_before
    assert _no_stray_temp_files(str(ch_dir), str(corpus_root)) == []
    assert "Finalization complete" not in capsys.readouterr().out
