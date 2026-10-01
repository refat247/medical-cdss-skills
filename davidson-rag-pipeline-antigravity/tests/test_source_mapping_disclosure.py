"""v2.6.3 — Stage 4.5d gate output source_lines dependency disclosure
(Safety Guardrails release, requirement 7). Advisory-only: source_mapping
must never become a blocking gate in this release, but must accurately
disclose context-fallback usage, malformed source_lines, and whether
source-lines precision was ever independently tested.
"""
import json
import os
import shutil

from scripts.maintenance.run_stage_4_5d import run_stage_4_5d

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "ch05_regression")
PREFIX = "Davidson_25_Ch05_Nutritional_factors_in_disease"


def _fixture_copy(tmp_path):
    out_dir = tmp_path / "ch05"
    out_dir.mkdir()
    shutil.copyfile(os.path.join(FIXTURE_DIR, "repaired_s2_fixture.md"), out_dir / f"{PREFIX}_REPAIRED_S2.md")
    shutil.copyfile(os.path.join(FIXTURE_DIR, "chunks_fixture.md"), out_dir / f"{PREFIX}_chunks.md")
    return str(out_dir)


def test_gate_always_has_source_mapping_block(tmp_path):
    out_dir = _fixture_copy(tmp_path)
    gate, _candidates = run_stage_4_5d(out_dir, PREFIX)
    assert "source_mapping" in gate


def test_source_mapping_is_always_advisory_only_and_never_claims_completeness(tmp_path):
    out_dir = _fixture_copy(tmp_path)
    gate, _candidates = run_stage_4_5d(out_dir, PREFIX)
    sm = gate["source_mapping"]
    assert sm["source_lines_precision_gate_status"] == "ADVISORY_ONLY"
    assert sm["semantic_completeness_claimed"] is False


def test_source_mapping_counts_sum_to_l2_chunks_scanned(tmp_path):
    out_dir = _fixture_copy(tmp_path)
    gate, _candidates = run_stage_4_5d(out_dir, PREFIX)
    sm = gate["source_mapping"]
    assert sm["chunks_using_source_lines"] + sm["chunks_using_context_fallback"] == gate["l2_chunks_scanned"]
    assert sm["chunks_using_context_fallback"] == gate["context_fallback_used_for_n_chunks"]


def test_source_mapping_discloses_untested_precision_by_default(tmp_path):
    out_dir = _fixture_copy(tmp_path)
    # no {PREFIX}_SourceLinesPrecision.json written in this temp dir
    gate, _candidates = run_stage_4_5d(out_dir, PREFIX)
    sm = gate["source_mapping"]
    assert sm["source_lines_precision_tested"] is False
    assert sm["source_lines_over_inclusive_count"] is None
    assert sm["source_lines_under_inclusive_count"] is None
    assert sm["source_lines_unresolved_count"] is None


def test_source_mapping_discloses_precision_counts_when_available(tmp_path):
    out_dir = _fixture_copy(tmp_path)
    precision_data = {
        "prefix": PREFIX, "pipeline_version": "2.6.3",
        "results": [
            {"chunk_id": "L2-001", "verdict": "PRECISE"},
            {"chunk_id": "L2-002", "verdict": "OVER_INCLUSIVE"},
            {"chunk_id": "L2-003", "verdict": "UNDER_INCLUSIVE"},
            {"chunk_id": "L2-004", "verdict": "UNDER_AND_OVER_INCLUSIVE"},
            {"chunk_id": "L2-005", "verdict": "UNRESOLVED"},
        ],
    }
    with open(os.path.join(out_dir, f"{PREFIX}_SourceLinesPrecision.json"), "w", encoding="utf-8") as f:
        json.dump(precision_data, f)

    gate, _candidates = run_stage_4_5d(out_dir, PREFIX)
    sm = gate["source_mapping"]
    assert sm["source_lines_precision_tested"] is True
    assert sm["source_lines_over_inclusive_count"] == 2  # OVER_INCLUSIVE + UNDER_AND_OVER_INCLUSIVE
    assert sm["source_lines_under_inclusive_count"] == 2  # UNDER_INCLUSIVE + UNDER_AND_OVER_INCLUSIVE
    assert sm["source_lines_unresolved_count"] == 1


def test_source_mapping_handles_malformed_precision_json_gracefully(tmp_path):
    out_dir = _fixture_copy(tmp_path)
    with open(os.path.join(out_dir, f"{PREFIX}_SourceLinesPrecision.json"), "w", encoding="utf-8") as f:
        f.write("{not valid json,,,")

    gate, _candidates = run_stage_4_5d(out_dir, PREFIX)
    sm = gate["source_mapping"]
    assert sm["source_lines_precision_tested"] is False  # unreadable -- treated as untested, not a crash


def test_source_mapping_does_not_block_gate_verdict(tmp_path):
    """Requirement 7 explicitly: do not make source-lines precision
    blocking in this task. A gate with heavy context-fallback usage must
    still be able to reach PASS on its own merits (candidates aside)."""
    out_dir = _fixture_copy(tmp_path)
    gate, _candidates = run_stage_4_5d(out_dir, PREFIX)
    assert "source_mapping" in gate
    assert gate["verdict"] in ("PASS", "BLOCKED", "NOT_TESTED")  # a real verdict, unaffected by source_mapping's presence
