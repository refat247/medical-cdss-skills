"""SECOND_SWEEP 1.26 / B12: the Ch05 adjudication script must not blanket-resolve or hard-code gate evidence."""
import importlib.util
import json
import os

from pipeline.stages import stage_4_5d_clinical_fidelity as s45d

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "scripts", "chapter_repairs", "apply_ch05_adjudication.py")


def _load():
    spec = importlib.util.spec_from_file_location("apply_ch05_adjudication", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _setup(tmp_path, chunk_ids, gate=None):
    mod = _load()
    cands = [{"candidate_id": f"C{i}", "chunk_id": cid, "status_label": "UNVERIFIED",
              "severity": "NEEDS_REVIEW", "decision": None} for i, cid in enumerate(chunk_ids)]
    (tmp_path / f"{mod.PREFIX}_ClinicalFidelity.json").write_text(json.dumps({"candidates": cands}), encoding="utf-8")
    if gate is not None:
        (tmp_path / f"{mod.PREFIX}_ClinicalFidelityGate.json").write_text(json.dumps(gate), encoding="utf-8")
    return mod


def test_candidates_outside_the_documented_chunks_stay_unresolved(tmp_path):
    mod = _setup(tmp_path, ["L2-097", "L2-999"], gate={
        "detectors_run": list(s45d.REQUIRED_DETECTORS), "pipeline_version": "9.9.9", "l2_chunks_scanned": 7})
    gate, updated = mod.main(["--out-dir", str(tmp_path)])
    by_chunk = {c["chunk_id"]: c for c in updated}
    assert by_chunk["L2-097"]["decision"] == "false_positive"
    assert by_chunk["L2-999"]["status_label"] != "VERIFIED"
    assert gate["verdict"] == "BLOCKED" and gate["unresolved_candidates"] == 1


def test_gate_evidence_comes_from_the_existing_gate_not_constants(tmp_path):
    mod = _setup(tmp_path, ["L2-097"], gate={
        "detectors_run": list(s45d.REQUIRED_DETECTORS), "pipeline_version": "9.9.9", "l2_chunks_scanned": 7})
    gate, _ = mod.main(["--out-dir", str(tmp_path)])
    assert gate["l2_chunks_scanned"] == 7 and gate["pipeline_version"] == "9.9.9" and gate["verdict"] == "PASS"


def test_no_existing_gate_means_detectors_not_tested_not_a_pass(tmp_path):
    mod = _setup(tmp_path, ["L2-097"], gate=None)
    gate, _ = mod.main(["--out-dir", str(tmp_path)])
    assert gate["verdict"] == "NOT_TESTED" and "l2_chunks_scanned" not in gate
