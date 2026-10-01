"""v2.6.6 -- tests for finalize_trusted_chapter.py (Fail-Closed
Finalization, task item 6/11). Builds small synthetic chapter directories
in tmp_path (never touches the real 02-15 corpus) covering: refusal when
mandatory evidence is missing, refusal on a Chapter-03-style prefixed
marker conflict, and successful dry-run + --write --authorize finalization
of a fully-evidenced chapter.
"""
import json
import os

import pytest

from pipeline import finalize_trusted_chapter as fin
from pipeline.stages.mutation_guard import PROTECTION_MARKER_FILENAME


def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _base_checkpoint():
    return {
        "chapter_info": {"checkpoint_schema_version": "2.0"},
        "pipeline_state": {"corpus_pipeline_completed": True},
        "stage_completions": {
            "4.5c": {"status": "COMPLETED"},
            "4.5d": {"status": "COMPLETED"},
            "4.6": {"status": "COMPLETED", "chunks_reviewed": 5, "total_flagged": 5},
            "4.7": {"status": "COMPLETED", "unresolved_completeness_clusters": 0},
            "8": {"status": "COMPLETED"},
        },
    }


def _build_fixture_chapter(tmp_path, chapter_dir_name="99", prefix="TestCh",
                            checkpoint=None, with_prefixed_marker=False):
    corpus_root = tmp_path / "corpus"
    ch_dir = corpus_root / chapter_dir_name
    ch_dir.mkdir(parents=True)
    cp = checkpoint if checkpoint is not None else _base_checkpoint()
    _write_json(ch_dir / f"{prefix}_CHECKPOINT.json", cp)
    _write_json(ch_dir / f"{prefix}_ClinicalFidelityGate.json", {"verdict": "PASS"})
    _write_json(ch_dir / f"{prefix}_SourceLinesPrecision.json", {"results": []})
    (ch_dir / f"{prefix}_RAG_Optimised.md").write_text("# x\n", encoding="utf-8")
    (ch_dir / f"{prefix}_chunks.md").write_text("chunk\n", encoding="utf-8")
    if with_prefixed_marker:
        _write_json(ch_dir / f"{prefix}_{PROTECTION_MARKER_FILENAME}", {"chapter": prefix})
    return str(corpus_root), str(ch_dir), prefix


def test_refuses_when_mandatory_stage_4_7_evidence_missing(tmp_path):
    cp = _base_checkpoint()
    del cp["stage_completions"]["4.7"]["unresolved_completeness_clusters"]
    _, ch_dir, _ = _build_fixture_chapter(tmp_path, checkpoint=cp)
    with pytest.raises(fin.FinalizationRefused, match="CORPUS_REVIEW_PENDING"):
        fin.run(ch_dir, write=False, authorize=False)


def test_refuses_on_prefixed_marker_conflict_without_canonical(tmp_path):
    """The exact Chapter 03 shape -- must refuse and must NOT auto-rename."""
    _, ch_dir, prefix = _build_fixture_chapter(tmp_path, with_prefixed_marker=True)
    with pytest.raises(fin.FinalizationRefused, match="Chapter 03 defect shape"):
        fin.run(ch_dir, write=False, authorize=False)
    # Confirm nothing was renamed/deleted/created.
    assert os.path.exists(os.path.join(ch_dir, f"{prefix}_{PROTECTION_MARKER_FILENAME}"))
    assert not os.path.exists(os.path.join(ch_dir, PROTECTION_MARKER_FILENAME))


def test_dry_run_does_not_write_anything(tmp_path):
    _, ch_dir, prefix = _build_fixture_chapter(tmp_path)
    result = fin.run(ch_dir, write=False, authorize=False)
    assert result["written"] is False
    assert not os.path.exists(os.path.join(ch_dir, PROTECTION_MARKER_FILENAME))


def test_write_without_authorize_is_still_a_dry_run(tmp_path):
    """Both --write and --authorize are required -- either alone is a no-op."""
    _, ch_dir, prefix = _build_fixture_chapter(tmp_path)
    result = fin.run(ch_dir, write=True, authorize=False)
    assert result["written"] is False
    assert not os.path.exists(os.path.join(ch_dir, PROTECTION_MARKER_FILENAME))


def test_successful_finalization_writes_canonical_marker_and_ledger(tmp_path):
    corpus_root, ch_dir, prefix = _build_fixture_chapter(tmp_path)
    result = fin.run(ch_dir, write=True, authorize=True)
    assert result["written"] is True
    marker_path = os.path.join(ch_dir, PROTECTION_MARKER_FILENAME)
    assert os.path.exists(marker_path)
    with open(marker_path, encoding="utf-8") as f:
        marker = json.load(f)
    assert marker["production_output_protected"] is True
    assert os.path.exists(os.path.join(corpus_root, "CORPUS_TRUST_STATUS.md"))
    with open(os.path.join(corpus_root, "CORPUS_TRUST_STATUS.md"), encoding="utf-8") as f:
        content = f.read()
    assert "CORPUS_TESTING_READY" in content


def test_refuses_when_no_checkpoint_exists(tmp_path):
    corpus_root = tmp_path / "corpus"
    ch_dir = corpus_root / "01"
    ch_dir.mkdir(parents=True)
    (ch_dir / "SomeOtherFile.md").write_text("x\n", encoding="utf-8")
    with pytest.raises(fin.FinalizationRefused, match="no recognizable pipeline output"):
        fin.run(str(ch_dir), write=False, authorize=False)
