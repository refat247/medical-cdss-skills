"""CP-06 + correction I — desired behavior: Stage 6 completion and Stage 7
completion must be distinguishable, both via the pipeline_status string AND
via independent monotonic boolean flags (never rely on the string alone).
"""
from pipeline.checkpoint_utils import mark_stage_complete, STAGE_ORDER


def _complete_through(checkpoint, checkpoint_path, upto_stage_key):
    for key in STAGE_ORDER:
        mark_stage_complete(checkpoint, checkpoint_path, key, output_file=None)
        if key == upto_stage_key:
            break


def test_stage6_completion_sets_corpus_pipeline_completed_flag(fresh_checkpoint):
    checkpoint, checkpoint_path = fresh_checkpoint
    _complete_through(checkpoint, checkpoint_path, "6")
    assert checkpoint["pipeline_state"]["corpus_pipeline_completed"] is True
    assert checkpoint["pipeline_state"]["advisory_scorecard_completed"] is False
    assert checkpoint["pipeline_state"]["pipeline_status"] == "CORPUS_PIPELINE_COMPLETED"


def test_stage7_completion_sets_advisory_scorecard_flag_without_losing_corpus_flag(fresh_checkpoint):
    checkpoint, checkpoint_path = fresh_checkpoint
    _complete_through(checkpoint, checkpoint_path, "7")
    assert checkpoint["pipeline_state"]["corpus_pipeline_completed"] is True
    assert checkpoint["pipeline_state"]["advisory_scorecard_completed"] is True
    assert checkpoint["pipeline_state"]["pipeline_status"] == "ADVISORY_SCORECARD_COMPLETED"


def test_stage6_and_stage7_completion_are_distinguishable(tmp_path):
    from pipeline.checkpoint_utils import load_or_create_checkpoint

    def _new(prefix):
        source = tmp_path / f"{prefix}.md"
        source.write_text("text\n", encoding="utf-8")
        out_dir = tmp_path / prefix
        out_dir.mkdir()
        return load_or_create_checkpoint(str(source), str(out_dir), prefix, "1", "slug")

    cp1, path1 = _new("stops_at_6")
    _complete_through(cp1, path1, "6")

    cp2, path2 = _new("stops_at_7")
    _complete_through(cp2, path2, "7")

    assert cp1["pipeline_state"]["pipeline_status"] == "CORPUS_PIPELINE_COMPLETED"
    assert cp2["pipeline_state"]["pipeline_status"] == "ADVISORY_SCORECARD_COMPLETED"


def test_rag_system_evaluation_completed_flag_exists_but_is_never_set_true(fresh_checkpoint):
    """Forward-compat placeholder for a future retrieval/generation
    evaluator (Phase 5+, not built now) -- must exist so future code has a
    stable field to write to, but nothing in Phase 0/1 ever sets it True."""
    checkpoint, checkpoint_path = fresh_checkpoint
    _complete_through(checkpoint, checkpoint_path, "7")
    assert checkpoint["pipeline_state"]["rag_system_evaluation_completed"] is False
