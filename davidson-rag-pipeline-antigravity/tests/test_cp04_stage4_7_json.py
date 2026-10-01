"""CP-04 + correction G — desired behavior: Stage 4.7 writes all three JSON
outputs (SCATTERED, SUSPECTED_GAP, COMPLETE_DISEASES) with a stable envelope
(schema_version/pipeline_version/chapter/generated_at), written atomically.
"""
import json
import os

from pipeline.stages.stage_4_7_serialize import write_stage_4_7_outputs, SCHEMA_VERSION


def test_stage4_7_writes_all_three_json_outputs(tmp_path):
    scattered = {"disease_a": {"chunk_ids": ["L2-001"], "missing": ["treatment"]}}
    suspected_gap = {"disease_b": {"missing": ["complication_or_safety"], "reason": "box implies it"}}
    complete = ["disease_c"]

    written = write_stage_4_7_outputs(
        str(tmp_path), "Ch99", scattered, suspected_gap, complete,
        pipeline_version="2.6.0", chapter="Ch99",
    )

    assert set(written) == {"Ch99_SCATTERED.json", "Ch99_SUSPECTED_GAP.json", "Ch99_COMPLETE_DISEASES.json"}
    for fname in written:
        assert os.path.exists(os.path.join(str(tmp_path), fname))


def test_stage4_7_json_envelope_has_required_fields(tmp_path):
    write_stage_4_7_outputs(str(tmp_path), "Ch99", {"d": {}}, {}, [],
                             pipeline_version="2.6.0", chapter="Ch99")
    payload = json.load(open(os.path.join(str(tmp_path), "Ch99_SCATTERED.json"), encoding="utf-8"))
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["pipeline_version"] == "2.6.0"
    assert payload["chapter"] == "Ch99"
    assert "generated_at" in payload and payload["generated_at"]
    assert payload["data"] == {"d": {}}


def test_stage4_7_scattered_json_matches_in_memory_dict_used_for_markdown():
    """No drift between the .md report and the .json output -- both must be
    built from the exact same SCATTERED dict, never independently derived."""
    from pipeline.stages.stage_4_7_serialize import build_stage_4_7_outputs
    scattered = {"rheumatoid_arthritis": {"chunk_ids": ["L2-01", "L2-02"], "missing": ["causes"]}}
    outputs = build_stage_4_7_outputs(scattered, {}, [], "2.6.0", "Ch25")
    assert outputs["{PREFIX}_SCATTERED.json"]["data"] == scattered


def test_stage5_2_can_load_scattered_json_produced_by_stage4_7(tmp_path):
    """Closes the self-consistency gap found while writing
    IMPLEMENTATION_MAP.md: Stage 5.2's code already assumes this file
    exists -- confirm it now does, without needing an out-of-band process."""
    scattered = {"gout": {"chunk_ids": ["L2-05"], "missing": ["investigation"]}}
    write_stage_4_7_outputs(str(tmp_path), "Ch99", scattered, {}, [],
                             pipeline_version="2.6.0", chapter="Ch99")
    loaded = json.load(open(os.path.join(str(tmp_path), "Ch99_SCATTERED.json"), encoding="utf-8"))
    assert loaded["data"] == scattered  # Stage 5.2 reads payload["data"] after this fix
