"""v2.6.3 — proves run_stage_4_5d.py's CLI entry point (_cli_main) is
non-mutating by default against a protected chapter fixture, and that
--write/--in-place/--backup correctly unlock a real mutation. Covers
requirement 2's mandated proof: "invoking the default CLI against a real
or fixture chapter does not alter any file."
"""
import json
import os
import shutil

import pytest

from scripts.maintenance.run_stage_4_5d import _cli_main
from pipeline.stages.mutation_guard import build_protection_marker, write_protection_marker

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "ch05_regression")
PREFIX = "Davidson_25_Ch05_Nutritional_factors_in_disease"


@pytest.fixture
def protected_chapter_copy(tmp_path):
    """A protected chapter fixture: real (frozen) chunks/REPAIRED_S2 content,
    pre-existing Stage 4.5d outputs (simulating a chapter that already
    passed adjudication), and a CORPUS_OUTPUT_PROTECTED.json marker."""
    out_dir = tmp_path / "ch05_protected"
    out_dir.mkdir()
    shutil.copyfile(os.path.join(FIXTURE_DIR, "repaired_s2_fixture.md"),
                     out_dir / f"{PREFIX}_REPAIRED_S2.md")
    shutil.copyfile(os.path.join(FIXTURE_DIR, "chunks_fixture.md"),
                     out_dir / f"{PREFIX}_chunks.md")

    existing_gate = {"verdict": "PASS", "unresolved_candidates": 0, "unresolved_corruptions": 0,
                      "detectors_run": [], "candidate_count": 0}
    (out_dir / f"{PREFIX}_ClinicalFidelity.md").write_text("EXISTING CONTENT", encoding="utf-8")
    (out_dir / f"{PREFIX}_ClinicalFidelity.json").write_text(json.dumps({"candidates": []}), encoding="utf-8")
    (out_dir / f"{PREFIX}_ClinicalFidelityFailures.json").write_text("[]", encoding="utf-8")
    (out_dir / f"{PREFIX}_ClinicalFidelityGate.json").write_text(json.dumps(existing_gate), encoding="utf-8")

    marker = build_protection_marker(str(out_dir), PREFIX, chapter="05", stage6_verdict="PASS",
                                      pipeline_version="2.6.3", checkpoint_schema_version="2.0")
    write_protection_marker(str(out_dir), PREFIX, marker)
    return str(out_dir)


def _snapshot(out_dir):
    files = {}
    for f in os.listdir(out_dir):
        p = os.path.join(out_dir, f)
        if os.path.isfile(p):
            with open(p, "rb") as fh:
                files[f] = fh.read()
    return files


def test_default_cli_invocation_does_not_alter_any_real_file(protected_chapter_copy):
    before = _snapshot(protected_chapter_copy)
    _cli_main([protected_chapter_copy, PREFIX])  # no flags at all
    after = _snapshot(protected_chapter_copy)
    # every pre-existing real file byte-identical; only a new .dryrun_stage_4_5d/
    # subdirectory may have appeared
    for fname, content in before.items():
        assert after.get(fname) == content, f"{fname} was modified by a default (no-flag) CLI run"


def test_cli_with_write_but_no_in_place_still_refuses_on_protected_existing_outputs(protected_chapter_copy):
    before = _snapshot(protected_chapter_copy)
    _cli_main([protected_chapter_copy, PREFIX, "--write"])  # missing --in-place, --backup
    after = _snapshot(protected_chapter_copy)
    for fname, content in before.items():
        assert after.get(fname) == content, f"{fname} was modified despite missing --in-place/--backup"


def test_cli_dryrun_writes_report_to_subdirectory_not_real_files(protected_chapter_copy):
    _cli_main([protected_chapter_copy, PREFIX])
    report_dir = os.path.join(protected_chapter_copy, ".dryrun_stage_4_5d")
    assert os.path.isdir(report_dir)
    assert os.path.exists(os.path.join(report_dir, f"{PREFIX}_ClinicalFidelityGate.json"))


def test_cli_with_full_authorization_actually_mutates(protected_chapter_copy):
    before_gate = (protected_chapter_copy, f"{PREFIX}_ClinicalFidelityGate.json")
    before_content = open(os.path.join(*before_gate), encoding="utf-8").read()

    _cli_main([protected_chapter_copy, PREFIX, "--write", "--in-place", "--backup"])

    after_content = open(os.path.join(*before_gate), encoding="utf-8").read()
    assert after_content != before_content  # regenerated for real, as authorized

    backups = [f for f in os.listdir(protected_chapter_copy)
               if f.startswith(f"{PREFIX}_ClinicalFidelityGate.json.pre-mutation-")]
    assert backups, "expected a timestamped backup of the pre-mutation Gate.json"


def test_first_time_run_on_unprotected_chapter_needs_only_write(tmp_path):
    out_dir = tmp_path / "ch_new"
    out_dir.mkdir()
    shutil.copyfile(os.path.join(FIXTURE_DIR, "repaired_s2_fixture.md"),
                     out_dir / f"{PREFIX}_REPAIRED_S2.md")
    shutil.copyfile(os.path.join(FIXTURE_DIR, "chunks_fixture.md"),
                     out_dir / f"{PREFIX}_chunks.md")

    _cli_main([str(out_dir), PREFIX, "--write"])
    assert os.path.exists(out_dir / f"{PREFIX}_ClinicalFidelityGate.json")


def test_first_time_run_without_write_produces_no_real_output(tmp_path):
    out_dir = tmp_path / "ch_new2"
    out_dir.mkdir()
    shutil.copyfile(os.path.join(FIXTURE_DIR, "repaired_s2_fixture.md"),
                     out_dir / f"{PREFIX}_REPAIRED_S2.md")
    shutil.copyfile(os.path.join(FIXTURE_DIR, "chunks_fixture.md"),
                     out_dir / f"{PREFIX}_chunks.md")

    _cli_main([str(out_dir), PREFIX])  # no --write
    assert not os.path.exists(out_dir / f"{PREFIX}_ClinicalFidelityGate.json")
    assert os.path.exists(out_dir / ".dryrun_stage_4_5d" / f"{PREFIX}_ClinicalFidelityGate.json")
