"""v2.6.2 — repeatable Chapter 05 integration regression (audit finding:
previously only one-off scripts, no repeatable pytest coverage).

Two explicit, separately-scoped levels — read both docstrings before
trusting either as "the" end-to-end test:

Level A (TestLevelADeterministicPostChunkPipeline) proves the deterministic
post-chunk pipeline — Stage 4.5c through Stage 6 — genuinely passes against
frozen, approved Chapter 05 artifacts, using a temporary copy so the real
`05/` output directory is never touched. It does NOT prove Stage 4B's
chunking (an LLM subagent call) produced correct chunks in the first place
-- that step is not reproduced here at all, by design (irreducibly
non-deterministic, not something pytest should be asserting about).

Level B (TestLevelBCheckpointOrchestration) proves the checkpoint state
machine's CONTROL FLOW across the full STAGE_ORDER sequence using synthetic
stage results — valid transitions, blocked/failed stages never advance,
milestone-flag timing. It does NOT re-verify any stage's own clinical or
structural correctness (that's Level A's and the unit tests' job) — it
only proves the orchestration layer wires stages together correctly.

Neither level calls the Stage 4B subagent / any LLM. No test in this file
makes a network call.
"""
import hashlib
import json
import os
import re
import shutil

import pytest

from pipeline.checkpoint_utils import (
    load_or_create_checkpoint, load_checkpoint, mark_stage_complete,
    mark_stage_blocked, mark_stage_failed, should_run_stage, STAGE_ORDER,
    PIPELINE_VERSION,
)
from pipeline.stages.stage_4_5c_coverage import compute_coverage_gaps
from pipeline.stages.stage_4_5d_clinical_fidelity import (
    build_clinical_fidelity_gate, apply_adjudication_decisions,
    REQUIRED_DETECTORS, decide_checkpoint_action as s45d_decide,
)
from pipeline.stages.stage_6_validation import run_stage_6, decide_checkpoint_action as s6_decide
from pipeline.stages.adjudication_manifest import apply_validated_manifest

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "ch05_regression")
PREFIX = "Davidson_25_Ch05_Nutritional_factors_in_disease"
REAL_CH05_DIR = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "05"))
ADJUDICATION_MANIFEST_PATH = os.path.join(FIXTURE_DIR, "clinical_fidelity_adjudication_manifest.json")


def _apply_real_ch05_manifest(candidates):
    """v2.6.3 — replays the immutable, independently auditable adjudication
    manifest (tests/fixtures/ch05_regression/clinical_fidelity_adjudication_manifest.json)
    instead of the pre-v2.6.3 hardcoded blanket
    `{c["candidate_id"]: "false_positive" for c in candidates}` comprehension.
    Every decision now carries its own recorded rationale and is validated
    (schema/hash/candidate-set integrity) before being applied -- see
    pipeline/stages/adjudication_manifest.py. Fails loudly (assertion) if the
    manifest doesn't validate against this run's candidate set, rather than
    silently falling back to a blanket decision."""
    manifest = json.load(open(ADJUDICATION_MANIFEST_PATH, encoding="utf-8"))
    updated, result = apply_validated_manifest(
        manifest, candidates,
        source_sha256=manifest["source_sha256"], chunks_sha256=manifest["chunks_sha256"],
    )
    assert result["valid"], f"adjudication manifest failed validation: {result['errors']}"
    return updated


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


@pytest.fixture(scope="module")
def fixture_manifest():
    with open(os.path.join(FIXTURE_DIR, "fixture_manifest.json"), encoding="utf-8") as f:
        return json.load(f)


def test_fixture_files_match_manifest_hashes(fixture_manifest):
    """Drift guard: if someone edits a fixture file without regenerating
    the manifest (generate_manifest.py), this fails loudly instead of
    silently changing what Level A tests against."""
    for filename, info in fixture_manifest["files"].items():
        path = os.path.join(FIXTURE_DIR, filename)
        assert os.path.exists(path), f"fixture file missing: {filename}"
        actual = _sha256(path)
        assert actual == info["sha256"], (
            f"{filename} does not match fixture_manifest.json's recorded hash — "
            f"either the fixture drifted unintentionally, or generate_manifest.py "
            f"needs to be re-run after a deliberate fixture update."
        )


@pytest.mark.integration
@pytest.mark.slow
class TestLevelADeterministicPostChunkPipeline:
    """Proves: approved chunks.md parses; Stage 4.5c passes; Stage 4.5d gate
    reaches PASS after adjudication with all 11 required detectors
    represented and zero unresolved candidates/corruptions; Stage 6 PASS;
    checkpoint milestone corpus_pipeline_completed becomes True; advisory
    completion is NOT falsely implied unless Stage 7 is actually run.

    Does NOT prove: that Stage 4B's original chunking was correct (not
    reproduced here), that the adjudication decisions applied below are
    clinically correct in some absolute sense (they replay the real,
    already-performed human/joint adjudication from the v2.6.1 session,
    documented in apply_ch05_adjudication.py — this test confirms the
    MECHANISM correctly reaches PASS given those decisions, not that the
    decisions themselves are unchallengeable).
    """

    @pytest.fixture
    def temp_chapter_dir(self, tmp_path):
        """Copies the frozen fixtures into an isolated temp directory named
        like a real chapter output dir. Never touches the real 05/ dir."""
        out_dir = tmp_path / "ch05_temp"
        out_dir.mkdir()
        shutil.copyfile(os.path.join(FIXTURE_DIR, "repaired_s2_fixture.md"),
                         out_dir / f"{PREFIX}_REPAIRED_S2.md")
        shutil.copyfile(os.path.join(FIXTURE_DIR, "chunks_fixture.md"),
                         out_dir / f"{PREFIX}_chunks.md")
        shutil.copyfile(os.path.join(FIXTURE_DIR, "rag_optimised_fixture.md"),
                         out_dir / f"{PREFIX}_RAG_Optimised.md")
        return str(out_dir)

    def test_chunks_fixture_parses_into_l1_and_l2_blocks(self, temp_chapter_dir):
        chunks_text = open(os.path.join(temp_chapter_dir, f"{PREFIX}_chunks.md"), encoding="utf-8").read()
        blocks = re.findall(r'(---\nchunk_id:.*?\n---\n.*?)(?=\n---\nchunk_id:|\Z)', chunks_text, re.DOTALL)
        assert len(blocks) > 0
        l2_count = sum(1 for b in blocks if re.search(r'chunk_level:\s*2', b))
        assert l2_count > 0

    def test_stage_4_5c_passes_on_fixture(self, temp_chapter_dir):
        chunks_text = open(os.path.join(temp_chapter_dir, f"{PREFIX}_chunks.md"), encoding="utf-8").read()
        result = compute_coverage_gaps(chunks_text)
        assert result["verdict"] == "PASS", f"gaps found: {result['gaps']}"

    def test_stage_4_5d_gate_reaches_pass_after_adjudication(self, temp_chapter_dir):
        # Import here (not at module scope) since run_stage_4_5d writes real
        # files -- confined entirely to temp_chapter_dir, never 05/.
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from scripts.maintenance.run_stage_4_5d import run_stage_4_5d

        gate, candidates = run_stage_4_5d(temp_chapter_dir, PREFIX)

        # v2.6.3: replay the immutable, independently auditable adjudication
        # manifest (each decision carries its own rationale and is validated
        # against this exact source/chunks/candidate-set before being
        # applied) instead of a hardcoded blanket "everything is a false
        # positive" comprehension. See pipeline/stages/adjudication_manifest.py and
        # tests/fixtures/ch05_regression/clinical_fidelity_adjudication_manifest.json.
        candidates = _apply_real_ch05_manifest(candidates)

        rebuilt_gate = build_clinical_fidelity_gate(
            candidates, gate["detectors_run"],
            PIPELINE_VERSION, PREFIX,
        )

        assert rebuilt_gate["verdict"] == "PASS"
        assert rebuilt_gate["unresolved_candidates"] == 0
        assert rebuilt_gate["unresolved_corruptions"] == 0
        assert set(REQUIRED_DETECTORS) <= set(rebuilt_gate["detectors_run"])
        assert rebuilt_gate["detectors_not_tested"] == []

        # Persist the rebuilt (adjudicated) gate for the Stage 6 test below.
        gate_path = os.path.join(temp_chapter_dir, f"{PREFIX}_ClinicalFidelityGate.json")
        json.dump(rebuilt_gate, open(gate_path, "w", encoding="utf-8"), indent=2)

    def test_stage_6_passes_given_adjudicated_gate(self, temp_chapter_dir):
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from scripts.maintenance.run_stage_4_5d import run_stage_4_5d

        gate, candidates = run_stage_4_5d(temp_chapter_dir, PREFIX)
        candidates = _apply_real_ch05_manifest(candidates)
        rebuilt_gate = build_clinical_fidelity_gate(
            candidates, gate["detectors_run"],
            PIPELINE_VERSION, PREFIX,
        )

        rag_text = open(os.path.join(temp_chapter_dir, f"{PREFIX}_RAG_Optimised.md"), encoding="utf-8").read()
        chunks_text = open(os.path.join(temp_chapter_dir, f"{PREFIX}_chunks.md"), encoding="utf-8").read()
        coverage = compute_coverage_gaps(chunks_text)
        coverage_gaps_text = "VERDICT: PASS" if coverage["verdict"] == "PASS" else "BLOCKING FAIL"

        result = run_stage_6(rag_text, coverage_gaps_text, rebuilt_gate)
        assert result["verdict"] == "PASS", f"failures: {result['failures']}"

    def test_checkpoint_milestone_flow_matches_real_pipeline(self, temp_chapter_dir, tmp_path):
        """Runs the actual checkpoint calls (not just the pure stage
        functions) to confirm corpus_pipeline_completed becomes True after
        Stage 6, and advisory_scorecard_completed stays False since Stage 7
        is deliberately never invoked in this test."""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from scripts.maintenance.run_stage_4_5d import run_stage_4_5d

        source = tmp_path / "source.md"
        source.write_text("frozen source placeholder\n", encoding="utf-8")
        checkpoint, checkpoint_path = load_or_create_checkpoint(
            str(source), temp_chapter_dir, PREFIX, "05", "Nutritional_factors_in_disease",
        )

        chunks_text = open(os.path.join(temp_chapter_dir, f"{PREFIX}_chunks.md"), encoding="utf-8").read()
        coverage = compute_coverage_gaps(chunks_text)
        assert coverage["verdict"] == "PASS"
        mark_stage_complete(checkpoint, checkpoint_path, "4.5c",
                             l1_checked=coverage["l1_checked"], gaps_found=0)

        gate, candidates = run_stage_4_5d(temp_chapter_dir, PREFIX)
        candidates = _apply_real_ch05_manifest(candidates)
        rebuilt_gate = build_clinical_fidelity_gate(
            candidates, gate["detectors_run"],
            PIPELINE_VERSION, PREFIX,
        )
        action, meta = s45d_decide(rebuilt_gate)
        assert action == "complete"
        mark_stage_complete(checkpoint, checkpoint_path, "4.5d", **meta)

        rag_text = open(os.path.join(temp_chapter_dir, f"{PREFIX}_RAG_Optimised.md"), encoding="utf-8").read()
        stage6_result = run_stage_6(rag_text, "VERDICT: PASS", rebuilt_gate)
        action6, meta6 = s6_decide(stage6_result)
        assert action6 == "complete"
        mark_stage_complete(checkpoint, checkpoint_path, "6", **meta6)

        assert checkpoint["pipeline_state"]["corpus_pipeline_completed"] is True
        assert checkpoint["pipeline_state"]["advisory_scorecard_completed"] is False, (
            "advisory completion must not be implied just because Stage 6 passed -- "
            "Stage 7 was never invoked in this test"
        )
        assert checkpoint["pipeline_state"]["pipeline_status"] == "CORPUS_PIPELINE_COMPLETED"
        assert checkpoint["stage_completions"]["6"]["executed_with_pipeline_version"] == PIPELINE_VERSION

    def test_real_chapter_05_directory_is_never_written_to(self, temp_chapter_dir):
        """Explicit isolation proof: snapshot every file's mtime in the
        real 05/ directory before and after running the fixture-based
        flow above, confirm nothing changed. (The flow above only ever
        touches temp_chapter_dir, so this should trivially hold -- this
        test exists to make that guarantee explicit and checked, not just
        asserted in a docstring.)"""
        if not os.path.isdir(REAL_CH05_DIR):
            pytest.skip("real Chapter 05 directory not present in standalone repository context")
        before = {f: os.path.getmtime(os.path.join(REAL_CH05_DIR, f))
                  for f in os.listdir(REAL_CH05_DIR) if os.path.isfile(os.path.join(REAL_CH05_DIR, f))}

        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from scripts.maintenance.run_stage_4_5d import run_stage_4_5d
        run_stage_4_5d(temp_chapter_dir, PREFIX)  # exercises the same code path again

        after = {f: os.path.getmtime(os.path.join(REAL_CH05_DIR, f))
                 for f in os.listdir(REAL_CH05_DIR) if os.path.isfile(os.path.join(REAL_CH05_DIR, f))}
        assert before == after, "real Chapter 05 output directory was modified by the test run"


@pytest.mark.integration
class TestLevelBCheckpointOrchestration:
    """Proves: valid stage transitions across the FULL STAGE_ORDER sequence;
    no stage is skipped; blocked/failed stages do not advance
    next_stage_to_run; Stage 6 sets corpus completion; Stage 7 preserves it
    while adding advisory completion; final next_stage_to_run is None;
    every completion entry records executed_with_pipeline_version.

    Uses entirely SYNTHETIC stage results -- does not re-verify any stage's
    own clinical/structural correctness. That is Level A's job (for the
    stages Level A covers) and the individual unit test files' job (for
    every stage's own detection logic).
    """

    @pytest.fixture
    def orchestration_checkpoint(self, tmp_path):
        source = tmp_path / "source.md"
        source.write_text("synthetic source\n", encoding="utf-8")
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        return load_or_create_checkpoint(str(source), str(out_dir), "SynthCh", "99", "Synthetic")

    def test_full_stage_order_walk_with_all_synthetic_passes(self, orchestration_checkpoint):
        checkpoint, checkpoint_path = orchestration_checkpoint
        for stage_key in STAGE_ORDER:
            assert should_run_stage(checkpoint, stage_key) is True
            mark_stage_complete(checkpoint, checkpoint_path, stage_key, output_file=None)
            assert should_run_stage(checkpoint, stage_key) is False
            assert checkpoint["stage_completions"][stage_key]["executed_with_pipeline_version"] == PIPELINE_VERSION

        # v2.6.4: STAGE_ORDER now ends at "8" (Corpus Gate Closure), not "7" --
        # walking the full order now terminates one stage later.
        assert checkpoint["pipeline_state"]["next_stage_to_run"] is None
        assert checkpoint["pipeline_state"]["last_completed_stage"] == "8"
        assert checkpoint["pipeline_state"]["corpus_pipeline_completed"] is True
        assert checkpoint["pipeline_state"]["advisory_scorecard_completed"] is True
        assert checkpoint["pipeline_state"]["corpus_gate_closure_completed"] is True
        assert checkpoint["pipeline_state"]["pipeline_status"] == "CORPUS_GATE_CLOSURE_COMPLETED"

    def test_corpus_completed_true_before_advisory_completed_true(self, orchestration_checkpoint):
        """Order-sensitive: corpus_pipeline_completed must already be True
        the MOMENT Stage 6 completes, well before Stage 7 ever runs --
        proving the flag isn't accidentally coupled to Stage 7."""
        checkpoint, checkpoint_path = orchestration_checkpoint
        idx_6 = STAGE_ORDER.index("6")
        for stage_key in STAGE_ORDER[:idx_6 + 1]:
            mark_stage_complete(checkpoint, checkpoint_path, stage_key)
        assert checkpoint["pipeline_state"]["corpus_pipeline_completed"] is True
        assert checkpoint["pipeline_state"]["advisory_scorecard_completed"] is False
        assert checkpoint["pipeline_state"]["next_stage_to_run"] == "7"

    def test_blocked_stage_does_not_advance_next_stage_to_run(self, orchestration_checkpoint):
        checkpoint, checkpoint_path = orchestration_checkpoint
        for stage_key in STAGE_ORDER[:3]:  # walk to stage "3"
            mark_stage_complete(checkpoint, checkpoint_path, stage_key)
        mark_stage_blocked(checkpoint, checkpoint_path, "4a", reason="synthetic block")
        assert checkpoint["pipeline_state"]["next_stage_to_run"] == "4a"
        assert should_run_stage(checkpoint, "4a") is True
        assert checkpoint["pipeline_state"]["pipeline_status"] == "BLOCKED"

    def test_failed_stage_does_not_advance_next_stage_to_run(self, orchestration_checkpoint):
        checkpoint, checkpoint_path = orchestration_checkpoint
        for stage_key in STAGE_ORDER[:3]:
            mark_stage_complete(checkpoint, checkpoint_path, stage_key)
        mark_stage_failed(checkpoint, checkpoint_path, "4a", reason="synthetic crash")
        assert checkpoint["pipeline_state"]["next_stage_to_run"] == "4a"
        assert should_run_stage(checkpoint, "4a") is True

    def test_blocked_stage_can_recover_and_resume_normal_flow(self, orchestration_checkpoint):
        checkpoint, checkpoint_path = orchestration_checkpoint
        for stage_key in STAGE_ORDER[:3]:
            mark_stage_complete(checkpoint, checkpoint_path, stage_key)
        mark_stage_blocked(checkpoint, checkpoint_path, "4a")
        assert should_run_stage(checkpoint, "4a") is True
        # "Fix" and re-run -- resumes normal advancement.
        mark_stage_complete(checkpoint, checkpoint_path, "4a")
        assert checkpoint["pipeline_state"]["next_stage_to_run"] == "4b"
        assert checkpoint["pipeline_state"]["pipeline_status"] == "IN_PROGRESS"

    def test_reload_from_disk_reflects_same_state(self, orchestration_checkpoint):
        """Confirms the orchestration state is genuinely persisted, not
        just held in the in-memory dict the test happens to be using."""
        checkpoint, checkpoint_path = orchestration_checkpoint
        out_dir = os.path.dirname(checkpoint_path)
        for stage_key in STAGE_ORDER[:5]:
            mark_stage_complete(checkpoint, checkpoint_path, stage_key)
        reloaded, _ = load_checkpoint(out_dir, "SynthCh")
        assert reloaded["pipeline_state"]["next_stage_to_run"] == STAGE_ORDER[5]
        assert reloaded["stage_completions"]["1"]["status"] == "COMPLETED"
