"""v2.6.6 -- tests for verify_trusted_corpus_invariants.py (Fail-Closed
Finalization, task item 7/11). Read-only script; tests build synthetic
tmp_path corpora and confirm each named violation class is caught, plus
confirm a genuinely clean chapter passes with zero violations.

v2.6.7 addition: tests for `_check_stage6_chunk_count()` / the
[STAGE-6-CHUNK-COUNT-DEFECT] violation class, added per
REPOSITORY_PRODUCTION_READINESS_AUDIT.md Blocker 2 / Part C of the v2.6.7
task -- the invariant checker now independently re-derives Stage 6's chunk
count from `RAG_Optimised.md` (via the v2.6.7-fixed check_6_1_6_2 parser)
and cross-checks it against Stage6_Validation.md and the checkpoint's own
`chunks_checked` field. The `_build()` fixture below was extended (not
rewritten) to emit one real chunk in `RAG_Optimised.md` plus a matching
Stage6_Validation.md and checkpoint `chunks_checked=1`, so every
PRE-EXISTING clean/violation-class test below still gets a clean Stage-6
cross-check by default and continues to assert only the violation class it
was written for.
"""
import json

from pipeline import verify_trusted_corpus_invariants as vtci
from pipeline.stages.mutation_guard import PROTECTION_MARKER_FILENAME

_ONE_CHUNK_RAG_OPTIMISED = (
    "---\n"
    "chunk_id: L2-001\n"
    "semantic_type: clinical_feature\n"
    "disease_focus: test_disease\n"
    "coverage_status: complete\n"
    "---\n"
    "Body text.\n"
)


def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _base_checkpoint(chunks_checked=1):
    return {
        "chapter_info": {"checkpoint_schema_version": "2.0"},
        "pipeline_state": {"corpus_pipeline_completed": True},
        "stage_completions": {
            "4.5c": {"status": "COMPLETED"},
            "4.5d": {"status": "COMPLETED"},
            "4.6": {"status": "COMPLETED", "chunks_reviewed": 5, "total_flagged": 5},
            "4.7": {"status": "COMPLETED", "unresolved_completeness_clusters": 0},
            "6": {"status": "COMPLETED", "chunks_checked": chunks_checked, "verdict": "PASS"},
            "8": {"status": "COMPLETED"},
        },
    }


def _build(tmp_path, chapter_dir_name, prefix="TestCh", checkpoint=None,
           with_prefixed_marker=False, with_canonical_marker=True,
           rag_optimised_text=_ONE_CHUNK_RAG_OPTIMISED, stage6_report_chunks_checked=1,
           with_stage6_report=True):
    corpus_root = tmp_path / "corpus"
    ch_dir = corpus_root / chapter_dir_name
    ch_dir.mkdir(parents=True)
    cp = checkpoint if checkpoint is not None else _base_checkpoint()
    _write_json(ch_dir / f"{prefix}_CHECKPOINT.json", cp)
    _write_json(ch_dir / f"{prefix}_ClinicalFidelityGate.json", {"verdict": "PASS"})
    _write_json(ch_dir / f"{prefix}_SourceLinesPrecision.json", {"results": []})
    (ch_dir / f"{prefix}_RAG_Optimised.md").write_text(rag_optimised_text, encoding="utf-8")
    (ch_dir / f"{prefix}_chunks.md").write_text("chunk\n", encoding="utf-8")
    if with_stage6_report:
        (ch_dir / f"{prefix}_Stage6_Validation.md").write_text(
            f"# Stage 6 Validation -- {prefix}\n"
            f"Chunks checked: {stage6_report_chunks_checked}\n"
            "VERDICT: PASS\n",
            encoding="utf-8",
        )
    if with_prefixed_marker:
        _write_json(ch_dir / f"{prefix}_{PROTECTION_MARKER_FILENAME}", {"chapter": prefix})
    if with_canonical_marker:
        _write_json(ch_dir / PROTECTION_MARKER_FILENAME, {"chapter": prefix,
                                                            "production_output_protected": True})
    return str(corpus_root), str(ch_dir)


def test_clean_chapter_has_zero_violations(tmp_path):
    corpus_root, _ = _build(tmp_path, "01")
    violations = vtci.check_chapter(corpus_root, "01", "CORPUS_TESTING_READY")
    assert violations == []


def test_ch03_style_prefixed_marker_without_canonical_is_flagged(tmp_path):
    corpus_root, _ = _build(tmp_path, "03", with_prefixed_marker=True, with_canonical_marker=False)
    violations = vtci.check_chapter(corpus_root, "03", "CORPUS_TESTING_READY")
    assert any("CHAPTER-03-STYLE" in v for v in violations)
    assert any("no canonical" in v for v in violations)


def test_ch11_style_missing_stage_4_7_evidence_is_flagged(tmp_path):
    cp = _base_checkpoint()
    del cp["stage_completions"]["4.7"]["unresolved_completeness_clusters"]
    corpus_root, _ = _build(tmp_path, "11", checkpoint=cp)
    violations = vtci.check_chapter(corpus_root, "11", "CORPUS_TESTING_READY")
    assert any("CHAPTER-11-STYLE" in v for v in violations)
    assert any("LEDGER/RECOMPUTED MISMATCH" in v for v in violations)


def test_trusted_but_unprotected_is_flagged(tmp_path):
    corpus_root, _ = _build(tmp_path, "99", with_canonical_marker=False)
    violations = vtci.check_chapter(corpus_root, "99", "CORPUS_TESTING_READY")
    assert any("protection_marker_present is False" in v for v in violations)


def test_main_returns_nonzero_when_violations_exist(tmp_path, capsys):
    corpus_root, _ = _build(tmp_path, "03", with_prefixed_marker=True, with_canonical_marker=False)
    status_content = (
        "| Chapter | Checkpoint? | Classification | Trusted? | Protected? | Reasons |\n"
        "|---|---|---|---|---|---|\n"
        "| 03 | Yes | **CORPUS_TESTING_READY** | Yes | Yes | ok |\n"
    )
    (tmp_path / "corpus" / "CORPUS_TRUST_STATUS.md").write_text(status_content, encoding="utf-8")
    exit_code = vtci.main([corpus_root])
    assert exit_code == 1
    out = capsys.readouterr().out
    assert "CHAPTER-03-STYLE" in out


def test_main_returns_zero_when_clean(tmp_path, capsys):
    corpus_root, _ = _build(tmp_path, "01")
    status_content = (
        "| Chapter | Checkpoint? | Classification | Trusted? | Protected? | Reasons |\n"
        "|---|---|---|---|---|---|\n"
        "| 01 | Yes | **CORPUS_TESTING_READY** | Yes | Yes | ok |\n"
    )
    (tmp_path / "corpus" / "CORPUS_TRUST_STATUS.md").write_text(status_content, encoding="utf-8")
    exit_code = vtci.main([corpus_root])
    assert exit_code == 0


# --- v2.6.7 Part C: Stage 6 chunk-count cross-check -------------------------

def test_stage6_all_three_counts_equal_is_clean(tmp_path):
    """Clean pass: fresh re-derived count, Stage6_Validation.md, and the
    checkpoint's chunks_checked field all agree (the default _build() shape)."""
    corpus_root, _ = _build(tmp_path, "20")
    violations = vtci.check_chapter(corpus_root, "20", "CORPUS_TESTING_READY")
    assert violations == []


def test_stage6_checkpoint_stale_is_flagged(tmp_path):
    """Checkpoint says N-1 chunks_checked, but RAG_Optimised.md and
    Stage6_Validation.md both genuinely have N (checkpoint never updated
    after a chunk was added -- exactly the kind of staleness this cross-
    check exists to catch)."""
    cp = _base_checkpoint(chunks_checked=0)  # stale: file/report both say 1
    corpus_root, _ = _build(tmp_path, "21", checkpoint=cp)
    violations = vtci.check_chapter(corpus_root, "21", "CORPUS_TESTING_READY")
    assert any("STAGE-6-CHUNK-COUNT-DEFECT" in v for v in violations)


def test_stage6_report_stale_is_flagged(tmp_path):
    """Stage6_Validation.md itself declares a stale N-1 while
    RAG_Optimised.md and the checkpoint both genuinely have N."""
    corpus_root, _ = _build(tmp_path, "22", stage6_report_chunks_checked=0)
    violations = vtci.check_chapter(corpus_root, "22", "CORPUS_TESTING_READY")
    assert any("STAGE-6-CHUNK-COUNT-DEFECT" in v for v in violations)


def test_stage6_ch11_ch15_style_final_stub_omitted_scenario(tmp_path):
    """Reproduces the exact real-world defect class this cross-check was
    built for: the OLD (pre-v2.6.7) parser undercounted a file whose last
    chunk was an empty-body coverage_gap stub in a no-trailing-newline file
    by exactly 1 (105 vs 106 for Ch11; 86 vs 87 for Ch15). Simulated here by
    having the checkpoint/report both carry the OLD undercounted value (1)
    while RAG_Optimised.md genuinely has 2 real chunks -- the fresh
    re-derivation (using the now-fixed parser) must disagree with both and
    flag it, exactly as it would have caught the real Ch11/Ch15 defect
    automatically instead of requiring a manual audit."""
    two_chunk_no_trailing_newline = (
        "---\n"
        "chunk_id: L2-001\n"
        "semantic_type: clinical_feature\n"
        "disease_focus: test_disease\n"
        "coverage_status: complete\n"
        "---\n"
        "Body text.\n"
        "---\n"
        "chunk_id: L2-002-GAP\n"
        "semantic_type: coverage_gap\n"
        "disease_focus: test_disease_2\n"
        "coverage_status: gap\n"
        'gap_note: "no coverage found"\n'
        "---"  # no trailing newline, empty-body last chunk -- the real defect shape
    )
    cp = _base_checkpoint(chunks_checked=1)  # OLD undercounted value
    corpus_root, _ = _build(
        tmp_path, "23", checkpoint=cp,
        rag_optimised_text=two_chunk_no_trailing_newline,
        stage6_report_chunks_checked=1,  # OLD undercounted value, same staleness
    )
    violations = vtci.check_chapter(corpus_root, "23", "CORPUS_TESTING_READY")
    assert any("STAGE-6-CHUNK-COUNT-DEFECT" in v for v in violations)
    assert any("CHAPTER-11-15-STYLE" in v for v in violations)


def test_stage6_malformed_checkpoint_count_field_is_flagged(tmp_path):
    """A string where an int is expected must be flagged as malformed, not
    silently compared (which could produce a false-clean via Python's loose
    equality/str formatting)."""
    cp = _base_checkpoint()
    cp["stage_completions"]["6"]["chunks_checked"] = "one"
    corpus_root, _ = _build(tmp_path, "24", checkpoint=cp)
    violations = vtci.check_chapter(corpus_root, "24", "CORPUS_TESTING_READY")
    assert any("STAGE-6-CHUNK-COUNT-DEFECT" in v and "malformed" in v for v in violations)


def test_stage6_missing_checkpoint_count_field_is_flagged(tmp_path):
    """chunks_checked entirely absent from stage_completions["6"] must be
    flagged, not treated as an implicit zero or skipped silently."""
    cp = _base_checkpoint()
    del cp["stage_completions"]["6"]["chunks_checked"]
    corpus_root, _ = _build(tmp_path, "25", checkpoint=cp)
    violations = vtci.check_chapter(corpus_root, "25", "CORPUS_TESTING_READY")
    assert any("STAGE-6-CHUNK-COUNT-DEFECT" in v and "not present" in v for v in violations)


def test_real_corpus_currently_trusted_chapters_have_zero_violations():
    """Integration check against the REAL corpus (parent of this repo dir) --
    every chapter currently declared CORPUS_TESTING_READY in the committed
    CORPUS_TRUST_STATUS.md must have zero invariant violations after the
    v2.6.6 fail-closed fix and 9-chapter re-evaluation."""
    import os
    corpus_root = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), ".."))
    if not os.path.isdir(os.path.join(corpus_root, "06")):
        import pytest
        pytest.skip("Real corpus directory not present in this environment")
    exit_code = vtci.main([corpus_root])
    assert exit_code == 0
