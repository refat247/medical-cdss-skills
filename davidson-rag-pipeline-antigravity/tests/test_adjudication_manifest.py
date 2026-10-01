"""v2.6.3 — adjudication manifest validation (Safety Guardrails release,
requirements 4 & 5). Covers every validation category the spec names:
valid manifest, wrong source hash, wrong chunks hash, missing candidate,
extra candidate, duplicate ID, blank rationale, invalid decision, stale
legacy ID, candidate-set mismatch, confirmed corruption without
re-verification -- plus the real Chapter 05 manifest against a fresh
Stage 4.5d run on the frozen fixtures.
"""
import copy
import hashlib
import json
import os

import pytest

from pipeline.stages.adjudication_manifest import (
    build_candidate_set_hash, validate_manifest, apply_validated_manifest,
)

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "ch05_regression")
REAL_MANIFEST_PATH = os.path.join(FIXTURE_DIR, "clinical_fidelity_adjudication_manifest.json")
PREFIX = "Davidson_25_Ch05_Nutritional_factors_in_disease"


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def _raw_candidates():
    return [
        {"candidate_id": "c1", "check": "numeric", "chunk_id": "L2-001", "kind": "missing",
         "source_value": "5", "chunk_value": None},
        {"candidate_id": "c2", "check": "range", "chunk_id": "L2-002", "kind": "added",
         "source_value": None, "chunk_value": "2-4"},
    ]


def _valid_manifest_for(candidates, *, source_sha="SRC", chunks_sha="CHUNKS"):
    return {
        "schema_version": "1.0",
        "chapter": "99",
        "pipeline_version": "2.6.3",
        "source_sha256": source_sha,
        "chunks_sha256": chunks_sha,
        "candidate_set_sha256": build_candidate_set_hash(candidates),
        "review_status": "COMPLETE",
        "reviewed_at": "2026-07-29T00:00:00Z",
        "reviewer_role": "test_reviewer",
        "candidates": [
            {
                "candidate_id": c["candidate_id"], "detector": c["check"], "chunk_id": c["chunk_id"],
                "mismatch_kind": c["kind"], "source_value": c["source_value"], "chunk_value": c["chunk_value"],
                "source_context": "ctx", "chunk_context": "ctx",
                "decision": "false_positive", "rationale": "test rationale", "re_verified": False,
            }
            for c in candidates
        ],
    }


# --------------------------------------------------------------------------
# Real Chapter 05 manifest, validated against a fresh Stage 4.5d run.
# --------------------------------------------------------------------------

def test_real_ch05_manifest_is_valid_json_with_all_required_fields():
    manifest = json.load(open(REAL_MANIFEST_PATH, encoding="utf-8"))
    for field in ("schema_version", "chapter", "pipeline_version", "source_sha256",
                  "chunks_sha256", "candidate_set_sha256", "review_status", "reviewed_at",
                  "reviewer_role", "candidates"):
        assert field in manifest
    assert manifest["chapter"] == "05"
    assert len(manifest["candidates"]) == 7
    for c in manifest["candidates"]:
        assert c["rationale"].strip()
        assert c["decision"] in ("false_positive", "legitimate_paraphrase", "confirmed_corruption")


def test_real_ch05_manifest_validates_against_fresh_stage_4_5d_run(tmp_path):
    import shutil
    from scripts.maintenance.run_stage_4_5d import run_stage_4_5d

    out_dir = tmp_path / "ch05"
    out_dir.mkdir()
    shutil.copyfile(os.path.join(FIXTURE_DIR, "repaired_s2_fixture.md"), out_dir / f"{PREFIX}_REPAIRED_S2.md")
    shutil.copyfile(os.path.join(FIXTURE_DIR, "chunks_fixture.md"), out_dir / f"{PREFIX}_chunks.md")

    _gate, candidates = run_stage_4_5d(str(out_dir), PREFIX)
    manifest = json.load(open(REAL_MANIFEST_PATH, encoding="utf-8"))

    chunks_sha = _sha256_file(os.path.join(FIXTURE_DIR, "chunks_fixture.md"))
    assert manifest["chunks_sha256"] == chunks_sha

    result = validate_manifest(manifest, source_sha256=manifest["source_sha256"],
                                chunks_sha256=manifest["chunks_sha256"], current_candidates=candidates)
    assert result["valid"] is True, result["errors"]
    assert result["errors"] == []


def test_real_ch05_manifest_applies_cleanly_and_reaches_pass(tmp_path):
    import shutil
    from scripts.maintenance.run_stage_4_5d import run_stage_4_5d
    from pipeline.stages.stage_4_5d_clinical_fidelity import build_clinical_fidelity_gate

    out_dir = tmp_path / "ch05"
    out_dir.mkdir()
    shutil.copyfile(os.path.join(FIXTURE_DIR, "repaired_s2_fixture.md"), out_dir / f"{PREFIX}_REPAIRED_S2.md")
    shutil.copyfile(os.path.join(FIXTURE_DIR, "chunks_fixture.md"), out_dir / f"{PREFIX}_chunks.md")

    gate, candidates = run_stage_4_5d(str(out_dir), PREFIX)
    manifest = json.load(open(REAL_MANIFEST_PATH, encoding="utf-8"))

    updated, result = apply_validated_manifest(
        manifest, candidates, source_sha256=manifest["source_sha256"],
        chunks_sha256=manifest["chunks_sha256"],
    )
    assert result["valid"] is True
    rebuilt = build_clinical_fidelity_gate(updated, gate["detectors_run"], "2.6.3", PREFIX)
    assert rebuilt["verdict"] == "PASS"
    assert rebuilt["unresolved_candidates"] == 0


# --------------------------------------------------------------------------
# Synthetic validation-category coverage.
# --------------------------------------------------------------------------

def test_valid_manifest_passes():
    candidates = _raw_candidates()
    manifest = _valid_manifest_for(candidates)
    result = validate_manifest(manifest, source_sha256="SRC", chunks_sha256="CHUNKS",
                                current_candidates=candidates)
    assert result["valid"] is True
    assert result["errors"] == []


def test_wrong_source_hash_fails():
    candidates = _raw_candidates()
    manifest = _valid_manifest_for(candidates)
    result = validate_manifest(manifest, source_sha256="DIFFERENT_SRC", chunks_sha256="CHUNKS",
                                current_candidates=candidates)
    assert result["valid"] is False
    assert any("source_sha256 mismatch" in e for e in result["errors"])


def test_wrong_chunks_hash_fails():
    candidates = _raw_candidates()
    manifest = _valid_manifest_for(candidates)
    result = validate_manifest(manifest, source_sha256="SRC", chunks_sha256="DIFFERENT_CHUNKS",
                                current_candidates=candidates)
    assert result["valid"] is False
    assert any("chunks_sha256 mismatch" in e for e in result["errors"])


def test_missing_candidate_decision_fails():
    candidates = _raw_candidates()
    manifest = _valid_manifest_for(candidates)
    manifest["candidates"] = manifest["candidates"][:1]  # drop c2's decision
    # candidate_set_sha256 still matches the CURRENT scan (both candidates) --
    # only the manifest's own candidate list is short one entry.
    result = validate_manifest(manifest, source_sha256="SRC", chunks_sha256="CHUNKS",
                                current_candidates=candidates)
    assert result["valid"] is False
    assert any("no decision in the manifest" in e for e in result["errors"])


def test_extra_unknown_candidate_fails():
    candidates = _raw_candidates()
    manifest = _valid_manifest_for(candidates)
    manifest["candidates"].append({
        "candidate_id": "c999-does-not-exist", "detector": "numeric", "chunk_id": "L2-999",
        "mismatch_kind": "missing", "source_value": "1", "chunk_value": None,
        "source_context": "ctx", "chunk_context": "ctx", "decision": "false_positive",
        "rationale": "bogus", "re_verified": False,
    })
    result = validate_manifest(manifest, source_sha256="SRC", chunks_sha256="CHUNKS",
                                current_candidates=candidates)
    assert result["valid"] is False
    assert any("does not match any candidate in the current scan" in e for e in result["errors"])


def test_duplicate_candidate_id_fails():
    candidates = _raw_candidates()
    manifest = _valid_manifest_for(candidates)
    manifest["candidates"].append(copy.deepcopy(manifest["candidates"][0]))  # duplicate c1
    result = validate_manifest(manifest, source_sha256="SRC", chunks_sha256="CHUNKS",
                                current_candidates=candidates)
    assert result["valid"] is False
    assert any("duplicate candidate_id" in e for e in result["errors"])


def test_blank_rationale_fails():
    candidates = _raw_candidates()
    manifest = _valid_manifest_for(candidates)
    manifest["candidates"][0]["rationale"] = "   "
    result = validate_manifest(manifest, source_sha256="SRC", chunks_sha256="CHUNKS",
                                current_candidates=candidates)
    assert result["valid"] is False
    assert any("blank/missing rationale" in e for e in result["errors"])


def test_invalid_decision_value_fails():
    candidates = _raw_candidates()
    manifest = _valid_manifest_for(candidates)
    manifest["candidates"][0]["decision"] = "not_a_real_decision"
    result = validate_manifest(manifest, source_sha256="SRC", chunks_sha256="CHUNKS",
                                current_candidates=candidates)
    assert result["valid"] is False
    assert any("invalid decision" in e for e in result["errors"])


def test_stale_legacy_id_without_map_fails():
    candidates = _raw_candidates()
    manifest = _valid_manifest_for(candidates)
    manifest["candidates"][0]["candidate_id"] = "OLD-LEGACY-ID"
    result = validate_manifest(manifest, source_sha256="SRC", chunks_sha256="CHUNKS",
                                current_candidates=candidates)
    assert result["valid"] is False
    assert any("does not match any candidate" in e or "no decision in the manifest" in e
               for e in result["errors"])


def test_stale_legacy_id_with_explicit_map_succeeds():
    candidates = _raw_candidates()
    manifest = _valid_manifest_for(candidates)
    manifest["candidates"][0]["candidate_id"] = "OLD-LEGACY-ID"
    result = validate_manifest(manifest, source_sha256="SRC", chunks_sha256="CHUNKS",
                                current_candidates=candidates,
                                legacy_id_map={"OLD-LEGACY-ID": "c1"})
    assert result["valid"] is True, result["errors"]
    assert result["legacy_ids_converted"] == [{"legacy_id": "OLD-LEGACY-ID", "converted_to": "c1"}]


def test_candidate_set_hash_mismatch_blocks_replay_onto_different_scan():
    candidates = _raw_candidates()
    manifest = _valid_manifest_for(candidates)
    different_scan = _raw_candidates()
    different_scan[0]["source_value"] = "999"  # different underlying content -> different hash
    result = validate_manifest(manifest, source_sha256="SRC", chunks_sha256="CHUNKS",
                                current_candidates=different_scan)
    assert result["valid"] is False
    assert any("candidate_set_sha256 mismatch" in e for e in result["errors"])


def test_confirmed_corruption_without_re_verified_field_fails():
    candidates = _raw_candidates()
    manifest = _valid_manifest_for(candidates)
    manifest["candidates"][0]["decision"] = "confirmed_corruption"
    del manifest["candidates"][0]["re_verified"]
    result = validate_manifest(manifest, source_sha256="SRC", chunks_sha256="CHUNKS",
                                current_candidates=candidates)
    assert result["valid"] is False
    assert any("no re_verified status recorded" in e for e in result["errors"])


def test_confirmed_corruption_with_re_verified_false_warns_but_is_structurally_valid():
    candidates = _raw_candidates()
    manifest = _valid_manifest_for(candidates)
    manifest["candidates"][0]["decision"] = "confirmed_corruption"
    manifest["candidates"][0]["re_verified"] = False
    result = validate_manifest(manifest, source_sha256="SRC", chunks_sha256="CHUNKS",
                                current_candidates=candidates)
    assert result["valid"] is True  # structurally complete -- an open corruption is a legitimate state
    assert any("NOT YET re-verified" in w for w in result["warnings"])


def test_apply_validated_manifest_never_partially_applies_invalid_manifest():
    candidates = _raw_candidates()
    manifest = _valid_manifest_for(candidates)
    manifest["candidates"][0]["decision"] = "not_a_real_decision"  # make invalid

    original = copy.deepcopy(candidates)
    updated, result = apply_validated_manifest(
        manifest, candidates, source_sha256="SRC", chunks_sha256="CHUNKS",
    )
    assert result["valid"] is False
    assert updated == original  # untouched -- zero decisions applied


def test_apply_validated_manifest_applies_all_decisions_when_valid():
    candidates = _raw_candidates()
    manifest = _valid_manifest_for(candidates)
    updated, result = apply_validated_manifest(
        manifest, candidates, source_sha256="SRC", chunks_sha256="CHUNKS",
    )
    assert result["valid"] is True
    for c in updated:
        assert c["decision"] == "false_positive"
        assert c["rationale"] == "test rationale"
        assert c["status_label"] == "VERIFIED"


def test_build_candidate_set_hash_ignores_decision_and_severity_fields():
    """Confirms the hash is computed from identity fields only, so it's
    reproducible whether the candidate list is pre- or post-adjudication."""
    pre = _raw_candidates()
    post = copy.deepcopy(pre)
    for c in post:
        c["decision"] = "false_positive"
        c["severity"] = "RESOLVED_NOT_A_CORRUPTION"
        c["status_label"] = "VERIFIED"
    assert build_candidate_set_hash(pre) == build_candidate_set_hash(post)


def test_build_candidate_set_hash_is_order_independent():
    candidates = _raw_candidates()
    reversed_candidates = list(reversed(candidates))
    assert build_candidate_set_hash(candidates) == build_candidate_set_hash(reversed_candidates)


def test_build_candidate_set_hash_changes_when_content_changes():
    candidates = _raw_candidates()
    changed = copy.deepcopy(candidates)
    changed[0]["source_value"] = "different"
    assert build_candidate_set_hash(candidates) != build_candidate_set_hash(changed)
