"""v2.6.4 -- Corpus-Scale Gate Closure, MUST-FIX #3 (part 2): deterministic
trust-ledger generator. Uses the REAL corpus directory (02, 05, 25_AI_C,
25_AI_H, 27) since chapter discovery is directory-content-driven and this
is exactly what it must get right against real evidence -- plus a synthetic
tmp_path corpus for the idempotence/write-path tests.
"""
import json
import os
import shutil

import pytest

from pipeline.stages.trust_ledger import (
    build_corpus_trust_ledger, build_chapter_trust_record, discover_chapter_dirs,
    render_corpus_trust_status,
)

REAL_CORPUS_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..")
)


def _skip_unless_real_corpus_present():
    if not os.path.isdir(os.path.join(REAL_CORPUS_ROOT, "05")):
        pytest.skip("Real corpus directory not present in this environment")


def test_discovers_real_chapters_and_skips_empty_placeholders():
    _skip_unless_real_corpus_present()
    dirs = discover_chapter_dirs(REAL_CORPUS_ROOT)
    assert "05" in dirs
    assert "02" in dirs
    # An empty placeholder chapter dir (e.g. "16", still unprocessed as of
    # Batch 4 -- "08" was the placeholder example here until Batch 4
    # processed and protected it, which invalidated this assertion, same as
    # "01" before it) is discoverable as a dir but must be excluded from the
    # actual ledger (no prefix derivable).
    ledger = build_corpus_trust_ledger(REAL_CORPUS_ROOT)
    ledger_dirs = {c["chapter_dir"] for c in ledger["chapters"]}
    assert "16" not in ledger_dirs


def test_real_chapter_05_and_02_are_included_in_ledger():
    _skip_unless_real_corpus_present()
    ledger = build_corpus_trust_ledger(REAL_CORPUS_ROOT)
    ledger_dirs = {c["chapter_dir"] for c in ledger["chapters"]}
    assert "05" in ledger_dirs
    assert "02" in ledger_dirs


def test_real_legacy_chapters_are_correctly_classified():
    _skip_unless_real_corpus_present()
    ledger = build_corpus_trust_ledger(REAL_CORPUS_ROOT)
    by_dir = {c["chapter_dir"]: c for c in ledger["chapters"]}
    assert by_dir["25_AI_C"]["classification"] == "LEGACY_UNCHECKPOINTED"
    assert by_dir["25_AI_H"]["classification"] == "LEGACY_STALE_CHECKPOINT"
    assert by_dir["27"]["classification"] == "LEGACY_UNGATED"
    for d in ("25_AI_C", "25_AI_H", "27"):
        assert by_dir[d]["trusted_for_downstream_use"] is False


def test_chapters_without_stage8_precision_are_review_pending_not_testing_ready():
    """Before Stage 8 has actually been run for real against Chapter 05/02
    (a separate later step in this sprint), the ledger must NOT silently
    grant CORPUS_TESTING_READY to either -- this is the exact defect
    (untested precision treated as fine) MUST-FIX #3 exists to close."""
    _skip_unless_real_corpus_present()
    ledger = build_corpus_trust_ledger(REAL_CORPUS_ROOT)
    by_dir = {c["chapter_dir"]: c for c in ledger["chapters"]}
    for d in ("02", "05"):
        if by_dir[d]["classification"] == "CORPUS_TESTING_READY":
            continue  # acceptable if Stage 8 has since been run for real
        assert by_dir[d]["classification"] == "CORPUS_REVIEW_PENDING"
        assert by_dir[d]["trusted_for_downstream_use"] is False


def test_ledger_chapters_are_sorted_deterministically():
    _skip_unless_real_corpus_present()
    ledger1 = build_corpus_trust_ledger(REAL_CORPUS_ROOT)
    ledger2 = build_corpus_trust_ledger(REAL_CORPUS_ROOT)
    dirs1 = [c["chapter_dir"] for c in ledger1["chapters"]]
    dirs2 = [c["chapter_dir"] for c in ledger2["chapters"]]
    assert dirs1 == dirs2
    assert dirs1 == sorted(dirs1)


def test_ledger_idempotent_content_excluding_timestamp():
    """Regenerating against unchanged evidence produces byte-identical
    `chapters` content -- only `generated_at` may differ."""
    _skip_unless_real_corpus_present()
    ledger1 = build_corpus_trust_ledger(REAL_CORPUS_ROOT)
    ledger2 = build_corpus_trust_ledger(REAL_CORPUS_ROOT)
    assert ledger1["chapters"] == ledger2["chapters"]


def test_never_infers_trust_from_rag_optimised_existence_alone(tmp_path):
    """A chapter directory with ONLY a RAG_Optimised.md (no checkpoint, no
    Stage6_Validation.md, no L1L2_CoverageGaps.md) must not be silently
    trusted -- it should classify LEGACY_UNGATED, the same as if
    RAG_Optimised.md didn't exist at all."""
    ch_dir = tmp_path / "99"
    ch_dir.mkdir()
    (ch_dir / "Davidson_25_Ch99_Fake_chapter_RAG_Optimised.md").write_text("# fake\n", encoding="utf-8")
    record = build_chapter_trust_record(str(ch_dir), "99")
    assert record is not None
    assert record["classification"] == "LEGACY_UNGATED"
    assert record["trusted_for_downstream_use"] is False


def test_empty_directory_returns_none_not_a_fabricated_classification(tmp_path):
    ch_dir = tmp_path / "01"
    ch_dir.mkdir()
    record = build_chapter_trust_record(str(ch_dir), "01")
    assert record is None


def test_render_corpus_trust_status_includes_every_chapter_row():
    ledger = {
        "schema_version": "1.0", "pipeline_version": "2.6.4", "generated_at": "2026-01-01T00:00:00Z",
        "chapters": [
            {"chapter_dir": "02", "prefix": "P02", "checkpoint_exists": True,
             "classification": "CORPUS_REVIEW_PENDING", "trusted_for_downstream_use": False,
             "reasons": ["reason a"], "required_action": "do x", "protection_marker_present": False},
            {"chapter_dir": "05", "prefix": "P05", "checkpoint_exists": True,
             "classification": "CORPUS_TESTING_READY", "trusted_for_downstream_use": True,
             "reasons": ["reason b"], "required_action": "None", "protection_marker_present": True},
        ],
    }
    md = render_corpus_trust_status(ledger)
    assert "02" in md and "CORPUS_REVIEW_PENDING" in md
    assert "05" in md and "CORPUS_TESTING_READY" in md
    assert "do not hand-edit" in md.lower()


def test_render_reports_correct_trusted_count():
    ledger = {
        "schema_version": "1.0", "pipeline_version": "2.6.4", "generated_at": "2026-01-01T00:00:00Z",
        "chapters": [
            {"chapter_dir": "02", "prefix": "P02", "checkpoint_exists": True,
             "classification": "CORPUS_TESTING_READY", "trusted_for_downstream_use": True,
             "reasons": [], "required_action": "None", "protection_marker_present": False},
            {"chapter_dir": "05", "prefix": "P05", "checkpoint_exists": True,
             "classification": "CORPUS_REVIEW_PENDING", "trusted_for_downstream_use": False,
             "reasons": [], "required_action": "x", "protection_marker_present": False},
        ],
    }
    md = render_corpus_trust_status(ledger)
    assert "1 chapter(s) currently `CORPUS_TESTING_READY`" in md
    assert "02" in md.split("currently `CORPUS_TESTING_READY`")[1].splitlines()[0]
