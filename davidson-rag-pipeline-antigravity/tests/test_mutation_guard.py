"""v2.6.3 — Safety Guardrails, requirements 2 & 3: non-mutating-by-default
direct runners (pipeline/stages/mutation_guard.py's CLI-flag authorization contract)
and the production-output protection marker.
"""
import json
import os
from types import SimpleNamespace

import pytest

from pipeline.stages.mutation_guard import (
    build_protection_marker, write_protection_marker, read_protection_marker,
    is_protected, protection_marker_path, PROTECTION_MARKER_FILENAME,
    PROTECTION_MARKER_DISCLAIMER, require_authorization_for_in_place_mutation,
    guarded_write_file, MutationRefused, sha256_of_file, sha256_of_file_or_none,
)


def _args(write=False, in_place=False, backup=False, dry_run=False, output_dir=None):
    return SimpleNamespace(write=write, in_place=in_place, backup=backup,
                            dry_run=dry_run, output_dir=output_dir)


# --------------------------------------------------------------------------
# Protection marker
# --------------------------------------------------------------------------

def test_marker_not_protected_when_no_file(tmp_path):
    assert is_protected(str(tmp_path)) is False
    assert read_protection_marker(str(tmp_path)) is None


def test_build_protection_marker_has_required_fields(tmp_path):
    source = tmp_path / "source.md"
    source.write_text("src\n", encoding="utf-8")
    chunks = tmp_path / "chunks.md"
    chunks.write_text("chunks\n", encoding="utf-8")

    marker = build_protection_marker(
        str(tmp_path), "TestCh", chapter="05", stage6_verdict="PASS",
        pipeline_version="2.6.3", checkpoint_schema_version="2.0",
        source_path=str(source), chunks_path=str(chunks),
        rag_optimised_path=str(tmp_path / "missing_rag.md"),
        clinical_fidelity_gate_path=str(tmp_path / "missing_gate.json"),
    )
    assert marker["chapter"] == "05"
    assert marker["corpus_pipeline_completed"] is True
    assert marker["production_output_protected"] is True
    assert marker["stage_6_verdict"] == "PASS"
    assert marker["pipeline_version"] == "2.6.3"
    assert marker["checkpoint_schema_version"] == "2.0"
    assert marker["source_sha256"] == sha256_of_file(str(source))
    assert marker["chunks_sha256"] == sha256_of_file(str(chunks))
    assert marker["rag_optimised_sha256"] is None  # file doesn't exist -- None, not a crash
    assert marker["clinical_fidelity_gate_sha256"] is None
    assert "protection_timestamp" in marker
    assert marker["disclaimer"] == PROTECTION_MARKER_DISCLAIMER


def test_write_and_read_protection_marker_roundtrip(tmp_path):
    marker = build_protection_marker(
        str(tmp_path), "TestCh", chapter="05", stage6_verdict="PASS",
        pipeline_version="2.6.3", checkpoint_schema_version="2.0",
    )
    path = write_protection_marker(str(tmp_path), "TestCh", marker)
    assert os.path.basename(path) == PROTECTION_MARKER_FILENAME
    reloaded = read_protection_marker(str(tmp_path), "TestCh")
    assert reloaded == marker
    assert is_protected(str(tmp_path), "TestCh") is True


def test_protection_marker_disclaimer_does_not_overclaim():
    disclaimer_lower = PROTECTION_MARKER_DISCLAIMER.lower()
    assert "does not mean" in disclaimer_lower
    assert "clinically safety-validated" in PROTECTION_MARKER_DISCLAIMER
    assert "deployment-ready" in PROTECTION_MARKER_DISCLAIMER


# --------------------------------------------------------------------------
# require_authorization_for_in_place_mutation
# --------------------------------------------------------------------------

def test_refuses_without_write_or_in_place(tmp_path, capsys):
    with pytest.raises(MutationRefused):
        require_authorization_for_in_place_mutation(
            str(tmp_path), "TestCh", _args(), target_description="RAG_Optimised.md",
        )
    out = capsys.readouterr().out
    assert "--write" in out
    assert "--in-place" in out


def test_refuses_with_write_only_missing_in_place(tmp_path, capsys):
    with pytest.raises(MutationRefused):
        require_authorization_for_in_place_mutation(
            str(tmp_path), "TestCh", _args(write=True), target_description="chunks.md",
        )
    out = capsys.readouterr().out
    assert "--in-place" in out
    assert "--write" not in out.split("Refusing")[1].split(".")[0]  # not re-listed as missing


def test_unprotected_chapter_write_and_in_place_is_sufficient(tmp_path):
    result = require_authorization_for_in_place_mutation(
        str(tmp_path), "TestCh", _args(write=True, in_place=True),
        target_description="chunks.md",
    )
    assert result is False  # not protected


def test_protected_chapter_requires_backup_too(tmp_path, capsys):
    marker = build_protection_marker(str(tmp_path), "TestCh", chapter="05",
                                      stage6_verdict="PASS", pipeline_version="2.6.3",
                                      checkpoint_schema_version="2.0")
    write_protection_marker(str(tmp_path), "TestCh", marker)

    with pytest.raises(MutationRefused):
        require_authorization_for_in_place_mutation(
            str(tmp_path), "TestCh", _args(write=True, in_place=True),
            target_description="RAG_Optimised.md",
        )
    out = capsys.readouterr().out
    assert "--backup" in out
    assert "corpus-output-protected" in out


def test_protected_chapter_with_all_three_flags_is_authorized(tmp_path):
    marker = build_protection_marker(str(tmp_path), "TestCh", chapter="05",
                                      stage6_verdict="PASS", pipeline_version="2.6.3",
                                      checkpoint_schema_version="2.0")
    write_protection_marker(str(tmp_path), "TestCh", marker)
    result = require_authorization_for_in_place_mutation(
        str(tmp_path), "TestCh", _args(write=True, in_place=True, backup=True),
        target_description="RAG_Optimised.md",
    )
    assert result is True  # protected, and authorized


# --------------------------------------------------------------------------
# guarded_write_file
# --------------------------------------------------------------------------

def test_default_invocation_never_touches_real_path(tmp_path):
    target = tmp_path / "output.md"
    result = guarded_write_file(str(target), "new content", args=_args(), is_new_file=True)
    assert result["written"] is False
    assert not target.exists()
    assert os.path.exists(str(target) + ".DRYRUN.report")


def test_new_file_written_with_write_flag_only(tmp_path):
    target = tmp_path / "output.md"
    result = guarded_write_file(str(target), "new content", args=_args(write=True), is_new_file=True)
    assert result["written"] is True
    assert target.read_text(encoding="utf-8") == "new content"


def test_existing_file_mutation_refused_without_in_place(tmp_path):
    target = tmp_path / "chunks.md"
    target.write_text("original", encoding="utf-8")
    with pytest.raises(MutationRefused):
        guarded_write_file(str(target), "changed", args=_args(write=True), is_new_file=False,
                            out_dir=str(tmp_path), prefix="TestCh", target_description="chunks.md")
    assert target.read_text(encoding="utf-8") == "original"  # untouched


def test_existing_file_mutation_succeeds_with_write_and_in_place(tmp_path):
    target = tmp_path / "chunks.md"
    target.write_text("original", encoding="utf-8")
    result = guarded_write_file(str(target), "changed", args=_args(write=True, in_place=True),
                                 is_new_file=False, out_dir=str(tmp_path), prefix="TestCh",
                                 target_description="chunks.md")
    assert result["written"] is True
    assert target.read_text(encoding="utf-8") == "changed"


def test_protected_chapter_existing_file_mutation_takes_backup(tmp_path):
    marker = build_protection_marker(str(tmp_path), "TestCh", chapter="05",
                                      stage6_verdict="PASS", pipeline_version="2.6.3",
                                      checkpoint_schema_version="2.0")
    write_protection_marker(str(tmp_path), "TestCh", marker)

    target = tmp_path / "RAG_Optimised.md"
    target.write_text("original certified content", encoding="utf-8")

    result = guarded_write_file(
        str(target), "corrected content", args=_args(write=True, in_place=True, backup=True),
        is_new_file=False, out_dir=str(tmp_path), prefix="TestCh",
        target_description="RAG_Optimised.md",
    )
    assert result["written"] is True
    assert result["backup_path"] is not None
    assert os.path.exists(result["backup_path"])
    with open(result["backup_path"], encoding="utf-8") as f:
        assert f.read() == "original certified content"
    assert target.read_text(encoding="utf-8") == "corrected content"


def test_protected_chapter_existing_file_mutation_refused_without_backup(tmp_path):
    marker = build_protection_marker(str(tmp_path), "TestCh", chapter="05",
                                      stage6_verdict="PASS", pipeline_version="2.6.3",
                                      checkpoint_schema_version="2.0")
    write_protection_marker(str(tmp_path), "TestCh", marker)

    target = tmp_path / "RAG_Optimised.md"
    target.write_text("original certified content", encoding="utf-8")

    with pytest.raises(MutationRefused):
        guarded_write_file(
            str(target), "corrected content", args=_args(write=True, in_place=True),
            is_new_file=False, out_dir=str(tmp_path), prefix="TestCh",
            target_description="RAG_Optimised.md",
        )
    assert target.read_text(encoding="utf-8") == "original certified content"


def test_rollback_on_empty_content_validation_failure(tmp_path):
    target = tmp_path / "chunks.md"
    target.write_text("original content that must survive", encoding="utf-8")

    with pytest.raises(ValueError):
        guarded_write_file(str(target), "   ", args=_args(write=True, in_place=True, backup=True),
                            is_new_file=False, out_dir=str(tmp_path), prefix="TestCh",
                            target_description="chunks.md")

    assert target.read_text(encoding="utf-8") == "original content that must survive"
    assert not os.path.exists(str(target) + ".tmp")


def test_rollback_on_malformed_json_validation_failure(tmp_path):
    target = tmp_path / "Gate.json"
    target.write_text(json.dumps({"verdict": "PASS"}), encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        guarded_write_file(str(target), "{not valid json,,,", args=_args(write=True, in_place=True, backup=True),
                            is_new_file=False, out_dir=str(tmp_path), prefix="TestCh",
                            target_description="Gate.json")

    reloaded = json.loads(target.read_text(encoding="utf-8"))
    assert reloaded == {"verdict": "PASS"}  # original, valid content survived
    assert not os.path.exists(str(target) + ".tmp")


def test_sha256_of_file_or_none_missing_file(tmp_path):
    assert sha256_of_file_or_none(str(tmp_path / "nope.md")) is None


def test_sha256_of_file_or_none_existing_file(tmp_path):
    p = tmp_path / "f.md"
    p.write_text("x", encoding="utf-8")
    assert sha256_of_file_or_none(str(p)) == sha256_of_file(str(p))
