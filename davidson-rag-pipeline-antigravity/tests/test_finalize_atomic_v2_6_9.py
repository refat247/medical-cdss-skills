"""v2.6.9 -- RED/regression tests for atomic dual-write finalization
(Atomic Finalizer Repair). Written BEFORE the fix to capture the exact
defect: `finalize_trusted_chapter.py --write --authorize` computed a single
`args.in_place` flag from whether the CHAPTER MARKER existed before the run
started, then reused that same flag for the CORPUS-WIDE LEDGER write -- a
completely separate file with its own, independent pre-existence state. A
first-ever finalization (marker absent) into a corpus whose root
CORPUS_TRUST_STATUS.md already exists (the normal case after even one prior
chapter has been finalized) writes the marker successfully, then refuses the
ledger write with "Refusing to modify ... without --in-place", leaving the
chapter's marker written but the ledger not regenerated -- requiring the
operator to run the identical command a second time.

Independently reproduced against the real corpus (see
V2_6_9_ATOMIC_FINALIZER_REPORT.md) using an isolated copy of Chapter 15,
never the real corpus directory.

These tests build small synthetic multi-chapter corpora in tmp_path --
never the real 02-15 corpus -- and never delete a real chapter's marker.
"""
import json
import os
import shutil

import pytest

from pipeline import finalize_trusted_chapter as fin
from pipeline.stages import trust_ledger
from pipeline.stages.mutation_guard import PROTECTION_MARKER_FILENAME


def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _base_checkpoint(reviewed=5, flagged=5):
    return {
        "chapter_info": {"checkpoint_schema_version": "2.0"},
        "pipeline_state": {"corpus_pipeline_completed": True},
        "stage_completions": {
            "4.5c": {"status": "COMPLETED"},
            "4.5d": {"status": "COMPLETED"},
            "4.6": {"status": "COMPLETED", "chunks_reviewed": reviewed, "total_flagged": flagged},
            "4.7": {"status": "COMPLETED", "unresolved_completeness_clusters": 0},
            "8": {"status": "COMPLETED"},
        },
    }


def _build_chapter(corpus_root, chapter_dir_name, prefix, *, checkpoint=None,
                    finalized=False, rag_body="# x\n", chunks_body="chunk\n"):
    """Builds one chapter directory under an existing corpus_root (Path).
    `finalized=True` also runs a real successful finalization for it first
    (used to seed a corpus where OTHER chapters, or this one on a re-run
    test, are already trusted+protected -- i.e. a root ledger that already
    exists, the exact precondition the defect requires)."""
    ch_dir = corpus_root / chapter_dir_name
    ch_dir.mkdir(parents=True)
    cp = checkpoint if checkpoint is not None else _base_checkpoint()
    _write_json(ch_dir / f"{prefix}_CHECKPOINT.json", cp)
    _write_json(ch_dir / f"{prefix}_ClinicalFidelityGate.json", {"verdict": "PASS"})
    _write_json(ch_dir / f"{prefix}_SourceLinesPrecision.json", {"results": []})
    (ch_dir / f"{prefix}_RAG_Optimised.md").write_text(rag_body, encoding="utf-8")
    (ch_dir / f"{prefix}_chunks.md").write_text(chunks_body, encoding="utf-8")
    if finalized:
        result = fin.run(str(ch_dir), write=True, authorize=True)
        assert result["written"] is True
    return ch_dir


# --------------------------------------------------------------------------
# 1. First-ever finalization: marker absent, ledger present -- THE bug case.
# --------------------------------------------------------------------------

def test_first_ever_finalization_with_preexisting_ledger_succeeds_in_one_call(tmp_path):
    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir()
    # Seed the corpus with an already-finalized chapter so CORPUS_TRUST_STATUS.md
    # already exists on disk before we finalize the NEW chapter -- reproduces
    # the exact precondition of the defect.
    _build_chapter(corpus_root, "01", "SeedCh", finalized=True)
    assert (corpus_root / "CORPUS_TRUST_STATUS.md").exists()

    new_ch = _build_chapter(corpus_root, "02", "NewCh")
    marker_path = new_ch / PROTECTION_MARKER_FILENAME
    assert not marker_path.exists()

    result = fin.run(str(new_ch), write=True, authorize=True)

    assert result["written"] is True, "must succeed in ONE invocation, not require a re-run"
    assert marker_path.exists()
    ledger_text = (corpus_root / "CORPUS_TRUST_STATUS.md").read_text(encoding="utf-8")
    assert "NewCh" in ledger_text or "02" in ledger_text
    ledger = trust_ledger.build_corpus_trust_ledger(str(corpus_root))
    row = next(r for r in ledger["chapters"] if r["chapter_dir"] == "02")
    assert row["trusted_for_downstream_use"] is True
    assert row["protection_marker_present"] is True


# --------------------------------------------------------------------------
# 2. First-ever finalization: marker absent, ledger absent.
# --------------------------------------------------------------------------

def test_first_ever_finalization_with_no_preexisting_ledger_creates_both(tmp_path):
    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir()
    assert not (corpus_root / "CORPUS_TRUST_STATUS.md").exists()

    ch_dir = _build_chapter(corpus_root, "01", "OnlyCh")
    result = fin.run(str(ch_dir), write=True, authorize=True)

    assert result["written"] is True
    assert (ch_dir / PROTECTION_MARKER_FILENAME).exists()
    assert (corpus_root / "CORPUS_TRUST_STATUS.md").exists()


# --------------------------------------------------------------------------
# 3. Existing chapter re-finalization: marker present, ledger present.
# --------------------------------------------------------------------------

def test_existing_chapter_refinalization_succeeds_in_one_call(tmp_path):
    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir()
    ch_dir = _build_chapter(corpus_root, "01", "Ch", finalized=True)
    assert (ch_dir / PROTECTION_MARKER_FILENAME).exists()
    assert (corpus_root / "CORPUS_TRUST_STATUS.md").exists()

    result = fin.run(str(ch_dir), write=True, authorize=True)
    assert result["written"] is True


# --------------------------------------------------------------------------
# 4. Dry run: no files created or modified (both with and without a
#    pre-existing ledger -- the bug only manifests on --write --authorize,
#    but the dry-run path must never touch disk regardless of ledger state).
# --------------------------------------------------------------------------

def test_dry_run_is_read_only_even_when_ledger_preexists(tmp_path):
    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir()
    _build_chapter(corpus_root, "01", "SeedCh", finalized=True)
    ledger_before = (corpus_root / "CORPUS_TRUST_STATUS.md").read_bytes()

    new_ch = _build_chapter(corpus_root, "02", "NewCh")
    result = fin.run(str(new_ch), write=False, authorize=False)

    assert result["written"] is False
    assert not (new_ch / PROTECTION_MARKER_FILENAME).exists()
    assert (corpus_root / "CORPUS_TRUST_STATUS.md").read_bytes() == ledger_before
    # No stray temp/dryrun-report files left inside the chapter dir either.
    leftover = [p for p in os.listdir(new_ch) if p.endswith(".tmp")]
    assert leftover == []


# --------------------------------------------------------------------------
# 5. Marker write failure: ledger remains unchanged.
# --------------------------------------------------------------------------

def test_marker_write_failure_leaves_ledger_unchanged(tmp_path, monkeypatch):
    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir()
    _build_chapter(corpus_root, "01", "SeedCh", finalized=True)
    ledger_before = (corpus_root / "CORPUS_TRUST_STATUS.md").read_bytes()

    new_ch = _build_chapter(corpus_root, "02", "NewCh")
    marker_path = str(new_ch / PROTECTION_MARKER_FILENAME)

    real_replace = os.replace

    def failing_replace(src, dst):
        if os.path.abspath(dst) == os.path.abspath(marker_path):
            raise OSError("simulated disk failure writing the chapter marker")
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", failing_replace)

    with pytest.raises(Exception):
        fin.run(str(new_ch), write=True, authorize=True)

    assert not os.path.exists(marker_path), "marker must not exist after a failed write"
    assert (corpus_root / "CORPUS_TRUST_STATUS.md").read_bytes() == ledger_before


# --------------------------------------------------------------------------
# 6. Ledger write failure: marker remains unchanged or is rolled back.
#    This is the core atomicity requirement and the direct fix for the
#    reproduced defect.
# --------------------------------------------------------------------------

def test_ledger_write_failure_rolls_back_marker_on_first_ever_finalization(tmp_path, monkeypatch):
    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir()
    _build_chapter(corpus_root, "01", "SeedCh", finalized=True)
    ledger_path = str(corpus_root / "CORPUS_TRUST_STATUS.md")
    ledger_before = open(ledger_path, "rb").read()

    new_ch = _build_chapter(corpus_root, "02", "NewCh")
    marker_path = str(new_ch / PROTECTION_MARKER_FILENAME)
    assert not os.path.exists(marker_path)

    real_replace = os.replace

    def failing_replace(src, dst):
        if os.path.abspath(dst) == os.path.abspath(ledger_path):
            raise OSError("simulated disk failure writing the trust ledger")
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", failing_replace)

    with pytest.raises(Exception):
        fin.run(str(new_ch), write=True, authorize=True)

    assert not os.path.exists(marker_path), (
        "marker did not exist before this run -- it must be rolled back (removed) "
        "if the ledger write subsequently fails, never left behind as an orphan"
    )
    assert open(ledger_path, "rb").read() == ledger_before


def test_ledger_write_failure_restores_marker_on_refinalization(tmp_path, monkeypatch):
    """Same failure-injection, but for a chapter that was ALREADY finalized --
    the marker existed before this run with specific content; if the ledger
    write then fails, the marker must be restored to its pre-run content,
    not left as whatever the (now-orphaned) new marker was."""
    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir()
    ch_dir = _build_chapter(corpus_root, "01", "Ch", finalized=True)
    marker_path = str(ch_dir / PROTECTION_MARKER_FILENAME)
    ledger_path = str(corpus_root / "CORPUS_TRUST_STATUS.md")
    marker_before = open(marker_path, "rb").read()

    real_replace = os.replace

    def failing_replace(src, dst):
        if os.path.abspath(dst) == os.path.abspath(ledger_path):
            raise OSError("simulated disk failure writing the trust ledger")
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", failing_replace)

    with pytest.raises(Exception):
        fin.run(str(ch_dir), write=True, authorize=True)

    assert open(marker_path, "rb").read() == marker_before, (
        "an existing marker must be restored to its exact pre-run bytes if the "
        "paired ledger write fails -- never left holding the new, unpaired content"
    )


# --------------------------------------------------------------------------
# 7. Validation failure before write: neither artifact changes.
# --------------------------------------------------------------------------

def test_validation_failure_before_write_touches_neither_artifact(tmp_path):
    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir()
    _build_chapter(corpus_root, "01", "SeedCh", finalized=True)
    ledger_before = (corpus_root / "CORPUS_TRUST_STATUS.md").read_bytes()

    # Missing mandatory Stage 4.7 evidence -> classify_trust() must refuse
    # before either write is even attempted.
    cp = _base_checkpoint()
    del cp["stage_completions"]["4.7"]["unresolved_completeness_clusters"]
    new_ch = _build_chapter(corpus_root, "02", "NewCh", checkpoint=cp)

    with pytest.raises(fin.FinalizationRefused):
        fin.run(str(new_ch), write=True, authorize=True)

    assert not (new_ch / PROTECTION_MARKER_FILENAME).exists()
    assert (corpus_root / "CORPUS_TRUST_STATUS.md").read_bytes() == ledger_before


# --------------------------------------------------------------------------
# 8. Trust classification changes during preparation: write refused safely.
# --------------------------------------------------------------------------

def test_classification_drift_during_preparation_refuses_write(tmp_path, monkeypatch):
    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir()
    ch_dir = _build_chapter(corpus_root, "01", "Ch")

    # classify_trust() (the first check) passes, but the independent
    # trust_ledger.build_chapter_trust_record() re-check (simulating what the
    # ledger would show right before commit) reports NOT trusted -- e.g. a
    # concurrent process changed the checkpoint mid-run. Must refuse, not
    # write either file.
    real_build_record = trust_ledger.build_chapter_trust_record

    def drifted_record(output_dir, chapter_dir_name, **kwargs):
        rec = real_build_record(output_dir, chapter_dir_name, **kwargs)
        rec = dict(rec)
        rec["trusted_for_downstream_use"] = False
        rec["reasons"] = ["simulated classification drift mid-finalization"]
        return rec

    monkeypatch.setattr(trust_ledger, "build_chapter_trust_record", drifted_record)

    with pytest.raises(fin.FinalizationRefused):
        fin.run(str(ch_dir), write=True, authorize=True)

    assert not (ch_dir / PROTECTION_MARKER_FILENAME).exists()
    assert not (corpus_root / "CORPUS_TRUST_STATUS.md").exists()


# --------------------------------------------------------------------------
# 9. Existing malformed marker: explicit failure, no partial mutation.
# --------------------------------------------------------------------------

def test_malformed_existing_marker_fails_explicitly_without_partial_mutation(tmp_path):
    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir()
    _build_chapter(corpus_root, "01", "SeedCh", finalized=True)
    ledger_before = (corpus_root / "CORPUS_TRUST_STATUS.md").read_bytes()

    ch_dir = _build_chapter(corpus_root, "02", "Ch")
    marker_path = ch_dir / PROTECTION_MARKER_FILENAME
    marker_path.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(Exception):
        fin.run(str(ch_dir), write=True, authorize=True)

    # The malformed marker must not have been silently "fixed" into a valid
    # one, nor should the ledger have been regenerated against it.
    assert marker_path.read_text(encoding="utf-8") == "{not valid json"
    assert (corpus_root / "CORPUS_TRUST_STATUS.md").read_bytes() == ledger_before


# --------------------------------------------------------------------------
# 10. Stale trust ledger: correctly regenerated in one authorized invocation.
# --------------------------------------------------------------------------

def test_stale_ledger_regenerated_in_one_invocation(tmp_path):
    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir()
    ch_dir = _build_chapter(corpus_root, "01", "Ch", finalized=True)

    # Hand-corrupt the committed ledger to look stale (as if generated before
    # this chapter existed) -- but the marker is already correctly written.
    (corpus_root / "CORPUS_TRUST_STATUS.md").write_text(
        "# Corpus Trust Status\n\nstale placeholder, chapter 01 not listed\n",
        encoding="utf-8",
    )

    result = fin.run(str(ch_dir), write=True, authorize=True)
    assert result["written"] is True
    regenerated = (corpus_root / "CORPUS_TRUST_STATUS.md").read_text(encoding="utf-8")
    assert "01" in regenerated
    assert "CORPUS_TESTING_READY" in regenerated


# --------------------------------------------------------------------------
# 11. Repeated authorized invocation: idempotent final state.
# --------------------------------------------------------------------------

def test_repeated_authorized_invocation_is_idempotent(tmp_path):
    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir()
    ch_dir = _build_chapter(corpus_root, "01", "Ch", finalized=True)
    marker_path = ch_dir / PROTECTION_MARKER_FILENAME

    marker_1 = json.loads(marker_path.read_text(encoding="utf-8"))
    ledger_1 = (corpus_root / "CORPUS_TRUST_STATUS.md").read_text(encoding="utf-8")

    result = fin.run(str(ch_dir), write=True, authorize=True)
    assert result["written"] is True

    marker_2 = json.loads(marker_path.read_text(encoding="utf-8"))
    ledger_2 = (corpus_root / "CORPUS_TRUST_STATUS.md").read_text(encoding="utf-8")

    # Every field except the explicitly-permitted protection_timestamp must
    # be identical across the two authorized runs.
    for key in marker_1:
        if key == "protection_timestamp":
            continue
        assert marker_2[key] == marker_1[key], f"field {key!r} changed on idempotent re-run"

    # Ledger content is deterministic from evidence + marker, modulo the
    # "Generated <timestamp>" line and the marker's own timestamp appearing
    # nowhere in the rendered table -- classification/protected columns must
    # be stable.
    assert ledger_1.count("| 01 |") == ledger_2.count("| 01 |") == 1


# --------------------------------------------------------------------------
# 12. Multiple chapter rows: updating one chapter does not alter unrelated
#     ledger rows incorrectly.
# --------------------------------------------------------------------------

def test_finalizing_one_chapter_does_not_alter_other_chapter_rows(tmp_path):
    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir()
    _build_chapter(corpus_root, "01", "ChA", finalized=True)
    ledger_after_a = (corpus_root / "CORPUS_TRUST_STATUS.md").read_text(encoding="utf-8")
    a_row = next(l for l in ledger_after_a.splitlines() if l.startswith("| 01 |"))

    ch_b = _build_chapter(corpus_root, "02", "ChB")
    fin.run(str(ch_b), write=True, authorize=True)

    ledger_after_b = (corpus_root / "CORPUS_TRUST_STATUS.md").read_text(encoding="utf-8")
    a_row_after = next(l for l in ledger_after_b.splitlines() if l.startswith("| 01 |"))
    b_row_after = next(l for l in ledger_after_b.splitlines() if l.startswith("| 02 |"))

    assert a_row_after == a_row, "chapter 01's row must be byte-identical after finalizing chapter 02"
    assert "CORPUS_TESTING_READY" in b_row_after
