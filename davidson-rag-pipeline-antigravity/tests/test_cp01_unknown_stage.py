"""CP-01 — desired behavior: an unknown stage_key raises, and never silently
completes the pipeline. Per correction B, this file asserts the DESIRED
behavior only. RED/GREEN evidence is captured by running this suite against
the pre-fix backup of checkpoint_utils.py and then against the fixed
version — see PHASE0_PHASE1_REPORT.md for both runs' captured output.
"""
import json
import pytest

from pipeline.checkpoint_utils import mark_stage_complete


def test_unknown_stage_key_raises_value_error(fresh_checkpoint):
    checkpoint, checkpoint_path = fresh_checkpoint
    before_bytes = open(checkpoint_path, "rb").read()

    with pytest.raises(ValueError, match="Unknown stage key"):
        mark_stage_complete(checkpoint, checkpoint_path, "9.9.9-typo")

    after_bytes = open(checkpoint_path, "rb").read()
    assert before_bytes == after_bytes, "a rejected call must not write anything to disk"


def test_unknown_stage_key_does_not_mutate_in_memory_checkpoint(fresh_checkpoint):
    checkpoint, checkpoint_path = fresh_checkpoint
    before = json.loads(json.dumps(checkpoint))  # deep copy for comparison

    with pytest.raises(ValueError):
        mark_stage_complete(checkpoint, checkpoint_path, "9.9.9-typo")

    assert checkpoint == before, "a rejected call must not mutate the in-memory dict either"


def test_unknown_stage_key_pipeline_status_never_becomes_completed(fresh_checkpoint):
    """The specific historical bug: an unknown key used to be caught by a
    bare ValueError handler and silently produce pipeline_status=COMPLETED,
    next_stage_to_run=None -- indistinguishable from a legitimately finished
    chapter. Confirm that shape is now unreachable via this code path."""
    checkpoint, checkpoint_path = fresh_checkpoint
    try:
        mark_stage_complete(checkpoint, checkpoint_path, "not-a-real-stage")
    except ValueError:
        pass
    assert checkpoint["pipeline_state"]["pipeline_status"] == "STARTING"  # unchanged
    assert checkpoint["pipeline_state"]["next_stage_to_run"] == "1"       # unchanged
