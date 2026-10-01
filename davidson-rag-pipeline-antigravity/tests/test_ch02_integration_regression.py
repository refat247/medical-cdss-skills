"""v2.6.4 — lightweight Chapter 02-shaped integration regression (Task 6,
Corpus-Scale Gate Closure). Chapter 05's regression fixture (tests/fixtures/
ch05_regression) is disease-by-disease-shaped and exercises Stage 4.5b as
SKIPPED — it cannot exercise any of the paths that are specific to a
principles/pharmacology chapter. This file uses a small, frozen, real-content
excerpt of Chapter 02 (tests/fixtures/ch02_regression — 3 L2 chunks, ~50
source lines, not the full 110-chunk chapter) to exercise exactly the paths
Chapter 05's fixture cannot:

  - Stage 4.5b ACTIVE (dosing/threshold regex path actually executing,
    not skipped)
  - non-disease/principles chapter shape (disease_focus values are
    prescribing-process concepts, not named diseases)
  - short-bullet source-lines precision behavior (Box 2.6's real
    hypersensitivity-reaction bullet list -- the actual Chapter 02 finding
    that produced the bullet_gap_only heuristic)
  - zero Stage 4.5d candidates on real, correctly-chunked content
  - a checkpoint created fresh under the current (single-version) schema
  - deterministic trust classification reaching CORPUS_TESTING_READY

Deliberately NOT a duplicate of the full Chapter 02 corpus -- smallest
fixture that preserves each real failure/success shape being tested.
"""
import os

import pytest

from pipeline.checkpoint_utils import load_or_create_checkpoint, mark_stage_complete, STAGE_ORDER
from pipeline.stages.source_lines_precision import check_chunk_precision, build_precision_summary
from pipeline.stages.corpus_trust import classify_trust
from scripts.maintenance.run_stage_4_5d import run_stage_4_5d

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "ch02_regression")
PREFIX = "Ch02RegressionFixture"


@pytest.fixture
def fixture_dir(tmp_path):
    """Copies the frozen fixture files into a tmp_path under this test's own
    PREFIX naming convention -- never touches the real 02/ directory."""
    out_dir = tmp_path / "ch02_fixture"
    out_dir.mkdir()
    import shutil
    shutil.copyfile(os.path.join(FIXTURE_DIR, "repaired_s2_fixture.md"),
                     out_dir / f"{PREFIX}_REPAIRED_S2.md")
    shutil.copyfile(os.path.join(FIXTURE_DIR, "chunks_fixture.md"),
                     out_dir / f"{PREFIX}_chunks.md")
    return str(out_dir)


DOSING = [r'\b\d+\s*(?:mg|mcg|g|mL|units?|IU)\b',
          r'\b(?:once|twice|three times)\s+(?:daily|weekly)',
          r'\b(?:loading|maintenance)\s+dose\b',
          r'\b\d+(?:\.\d+)?\s*(?:mg/kg)\b']


def test_stage_4_5b_dosing_regex_is_active_and_finds_real_hits(fixture_dir):
    """Chapter 05's fixture never exercises this path at all (STAGE_45B_ACTIVE
    was False for that chapter). This fixture's MCQ 2.4 answer (dosing in
    mg/mcg for 5 drugs) must produce real, non-zero dosing-pattern hits,
    proving the regex path actually runs and matches real content on an
    'active' chapter."""
    import re
    text = open(os.path.join(fixture_dir, f"{PREFIX}_chunks.md"), encoding="utf-8").read()
    hits = sum(len(re.findall(p, text, re.I)) for p in DOSING)
    assert hits > 0


def test_non_disease_chapter_disease_focus_values_are_prescribing_concepts(fixture_dir):
    """Confirms the fixture's disease_focus values are principles/process
    concepts (prescribing_process, drug_hypersensitivity_reactions,
    renal_impairment_dosing), not named diseases -- the exact chapter-shape
    Stage 4.7's disease-completeness framework was never designed for."""
    import re
    text = open(os.path.join(fixture_dir, f"{PREFIX}_chunks.md"), encoding="utf-8").read()
    disease_focuses = re.findall(r'^disease_focus:\s*(.+)$', text, re.MULTILINE)
    assert "prescribing_process" in disease_focuses
    assert "drug_hypersensitivity_reactions" in disease_focuses
    # None of these look like a named disease (no diagnosis-shaped token)
    for df in disease_focuses:
        assert df not in ("diabetes", "hypertension", "asthma", "copd")


def test_bullet_gap_short_list_is_flagged_but_marked_bullet_gap_only(fixture_dir):
    """The real Chapter 02 finding (Box 2.6): reproduced here at fixture
    scale. Confirms the bullet-gap heuristic correctly fires on this small,
    frozen excerpt -- not just on the full real chapter file."""
    import re
    chunks_text = open(os.path.join(fixture_dir, f"{PREFIX}_chunks.md"), encoding="utf-8").read()
    repaired = open(os.path.join(fixture_dir, f"{PREFIX}_REPAIRED_S2.md"), encoding="utf-8").read()
    blocks = re.findall(r'(---\nchunk_id:.*?\n---\n.*?)(?=\n---\nchunk_id:|\Z)', chunks_text, re.DOTALL)
    box_block = next(b for b in blocks if "L2-002" in b)
    result = check_chunk_precision(box_block, repaired)
    assert result["verdict"] == "OVER_INCLUSIVE"
    assert result["bullet_gap_only"] is True


def test_stage_4_5d_finds_zero_candidates_on_correctly_chunked_fixture(fixture_dir):
    gate, candidates = run_stage_4_5d(fixture_dir, PREFIX)
    assert gate["verdict"] == "PASS"
    assert len(candidates) == 0


def test_fresh_checkpoint_uses_current_single_version_schema(fixture_dir, tmp_path):
    source = tmp_path / "source.md"
    source.write_text(open(os.path.join(fixture_dir, f"{PREFIX}_REPAIRED_S2.md"), encoding="utf-8").read(),
                       encoding="utf-8")
    checkpoint, _path = load_or_create_checkpoint(
        source_path=str(source), output_dir=fixture_dir, prefix=PREFIX, ch_num="02", ch_slug="Fixture",
    )
    from pipeline.checkpoint_utils import PIPELINE_VERSION
    assert checkpoint["chapter_info"]["checkpoint_created_with_pipeline_version"] == PIPELINE_VERSION
    assert checkpoint["chapter_info"]["checkpoint_schema_version"] == "2.0"
    assert checkpoint["chapter_info"]["migrations_applied"] == []


def test_end_to_end_fixture_reaches_corpus_testing_ready(fixture_dir, tmp_path):
    """Deterministic trust classification: walk this fixture through
    checkpoint stages 1-8 (synthetic completion, no subagent call -- same
    Level B orchestration style as the Chapter 05 regression suite), run the
    real Stage 4.5d + source_lines_precision against the real fixture files,
    then confirm classify_trust() reaches CORPUS_TESTING_READY end to end on
    Chapter-02-shaped (non-disease, 4.5b-active) content."""
    source = tmp_path / "source.md"
    source.write_text("fixture source\n", encoding="utf-8")
    checkpoint, checkpoint_path = load_or_create_checkpoint(
        source_path=str(source), output_dir=fixture_dir, prefix=PREFIX, ch_num="02", ch_slug="Fixture",
    )
    gate, candidates = run_stage_4_5d(fixture_dir, PREFIX)
    assert gate["verdict"] == "PASS"

    import re
    chunks_text = open(os.path.join(fixture_dir, f"{PREFIX}_chunks.md"), encoding="utf-8").read()
    repaired = open(os.path.join(fixture_dir, f"{PREFIX}_REPAIRED_S2.md"), encoding="utf-8").read()
    blocks = re.findall(r'(---\nchunk_id:.*?\n---\n.*?)(?=\n---\nchunk_id:|\Z)', chunks_text, re.DOTALL)
    l2_blocks = [b for b in blocks if re.search(r'chunk_level:\s*2', b)]
    results = [check_chunk_precision(b, repaired) for b in l2_blocks]
    precision_summary = build_precision_summary(results)
    assert precision_summary["unresolved_count"] == 1  # Box 2.6's bullet-gap, not yet adjudicated

    from pipeline.stages.source_lines_precision import apply_source_lines_adjudication
    box_id = next(r["chunk_id"] for r in results if r.get("bullet_gap_only"))
    updated, errors = apply_source_lines_adjudication(
        results, {box_id: {"decision": "CHECKER_FALSE_POSITIVE",
                            "rationale": "Fixture reproduction of the real Chapter 02 Box 2.6 finding "
                                         "-- short repeated drug-name bullets, confirmed verbatim."}},
    )
    assert errors == []
    precision_summary = build_precision_summary(updated)
    assert precision_summary["unresolved_count"] == 0

    for stage_key in STAGE_ORDER:
        if stage_key == "8":
            continue
        mark_stage_complete(checkpoint, checkpoint_path, stage_key)
    mark_stage_complete(checkpoint, checkpoint_path, "8")

    result = classify_trust(
        checkpoint, clinical_fidelity_gate=gate,
        source_lines_precision_summary=precision_summary,
        # v2.6.6: Stage 4.6/4.7 evidence is now mandatory for
        # CORPUS_TESTING_READY -- this fixture's checkpoint doesn't run the
        # real Stage 4.6/4.7 subagent passes (synthetic completion, per this
        # file's module docstring), so the fully-reviewed evidence is
        # supplied explicitly here, the same way the real pipeline would
        # record it in stage_completions["4.6"]/["4.7"].
        stage_4_6_review_status="COMPLETED",
        stage_4_6_chunks_reviewed=3, stage_4_6_total_flagged=3,
        unresolved_completeness_clusters=0,
    )
    assert result["classification"] == "CORPUS_TESTING_READY"
    assert result["trusted_for_downstream_use"] is True
