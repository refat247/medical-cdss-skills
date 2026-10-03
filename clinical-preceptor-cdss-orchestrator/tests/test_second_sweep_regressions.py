"""Regression tests for the preceptor orchestrator (skill_audits/SECOND_SWEEP.md 3.4, 3.5, D-04, D-05, D-19, D-20)."""
import csv
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import orchestrator as orch  # noqa: E402


def ws(tmp_path):
    w = tmp_path / "ws"
    (w / "00_CONTROL").mkdir(parents=True)
    return w


def never_events(w, n=4):
    d = w / "08_EXPORTS" / "PHARMACOVIGILANCE"; d.mkdir(parents=True)
    with (d / "never_events_toxic_drug_matrix.csv").open("w", encoding="utf-8", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=["id", "prescribed_agent", "forbidden_clinical_context", "lethal_adverse_consequence", "underlying_pathophysiology", "safe_clinical_alternative", "record_id"])
        wr.writeheader()
        for i in range(n):
            wr.writerow({"id": f"NE-{i}", "prescribed_agent": f"Drug{i}", "forbidden_clinical_context": "ctx", "lethal_adverse_consequence": "harm", "underlying_pathophysiology": "p", "safe_clinical_alternative": "s", "record_id": "R"})


def test_never_events_without_a_filter_shows_every_row(tmp_path, capsys):
    w = ws(tmp_path); never_events(w, 4)
    orch.run_never_events(w, "all")                      # argparse const="all"
    out = capsys.readouterr().out
    assert "(4 alerts)" in out and all(f"NE-{i}" in out for i in range(4))


def test_never_events_real_filter_still_filters(tmp_path, capsys):
    w = ws(tmp_path); never_events(w, 4)
    orch.run_never_events(w, "drug2")
    assert "(1 alerts)" in capsys.readouterr().out


def test_sbar_all_prints_every_card_and_no_match_is_reported(tmp_path, capsys):
    w = ws(tmp_path)
    d = w / "08_EXPORTS" / "SBAR_HANDOVERS"; d.mkdir(parents=True)
    cards = [{"record_id": f"R{i}", "condition": f"Cond{i}", "situation": "s", "background": "b", "assessment": "a", "recommendation": "r"} for i in range(3)]
    (d / "ward_sbar_handover_cards.jsonl").write_text("\n".join(json.dumps(c) for c in cards), encoding="utf-8")
    orch.run_sbar(w, "all")
    out = capsys.readouterr().out
    assert all(f"Cond{i}" in out for i in range(3))
    orch.run_sbar(w, "nothing-like-this")
    assert "NO MATCH" in capsys.readouterr().out.upper()


def test_pipeline_missing_stage_scripts_are_reported_not_silently_completed(tmp_path, capsys):
    w = ws(tmp_path)
    rc = orch.run_pipeline_stage(w, "claims")            # tools/expand_clinical_claims.py does not exist
    out = capsys.readouterr().out
    assert rc != 0 and "SKIPPED" in out and "completed successfully" not in out


def test_pipeline_failing_stage_script_fails_the_run(tmp_path, capsys):
    w = ws(tmp_path); (w / "tools").mkdir()
    (w / "tools" / "expand_clinical_claims.py").write_text("import sys\nsys.exit(4)\n")
    assert orch.run_pipeline_stage(w, "claims") != 0
    assert "completed successfully" not in capsys.readouterr().out


def test_pipeline_stage_script_is_not_run_with_the_orchestrators_argv(tmp_path):
    w = ws(tmp_path); (w / "tools").mkdir()
    (w / "tools" / "expand_clinical_claims.py").write_text("import argparse\nargparse.ArgumentParser().parse_args()\n")  # rejects stray args
    assert orch.run_pipeline_stage(w, "claims") == 0


def test_runtime_forwards_workspace_and_propagates_exit_code(tmp_path, monkeypatch):
    w = ws(tmp_path)
    marker = tmp_path / "seen.txt"
    stub = tmp_path / "nav.py"
    stub.write_text(f"import os, sys\nopen(r'{marker}', 'w').write(os.environ.get('CDSS_HABIJABI_ROOT', '') + '|' + ' '.join(sys.argv[1:]))\nsys.exit(5)\n")
    monkeypatch.setenv("CDSS_KAWSAR_NAVIGATOR", str(stub))
    monkeypatch.setattr(sys, "argv", ["orch", "--workspace", str(w), "--prescribing-safety", "x"])
    with pytest.raises(SystemExit) as e:
        orch.main()
    assert e.value.code == 5
    seen = marker.read_text()
    assert seen.startswith(str(w) + "|") and "--prescribing-safety x" in seen


def test_default_workspace_on_posix_is_not_a_literal_drive_name(monkeypatch):
    monkeypatch.delenv("CDSS_WORKSPACE", raising=False); monkeypatch.delenv("CDSS_HABIJABI_ROOT", raising=False)
    p = orch.resolve_workspace(None)
    assert "\\" not in str(p) or os.name == "nt"


def test_init_workspace_records_clinician_and_series(tmp_path):
    w = tmp_path / "newws"
    orch.init_workspace(w, "Dr X", "Series Y")
    meta = json.loads((w / "00_CONTROL" / "workspace.json").read_text(encoding="utf-8"))
    assert meta["clinician_name"] == "Dr X" and meta["series_name"] == "Series Y"


# ---------------- generator: tiering, counts, links ----------------
import importlib.util


def _gen():
    spec = importlib.util.spec_from_file_location("gen_ext", str(Path(__file__).resolve().parent.parent / "scripts" / "generate_extended_modalities.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def _recs():
    return [{"record_id": "R1", "title": "Graves disease", "domain": "Endocrinology", "primary_condition": "Graves disease"},
            {"record_id": "R2", "title": "Hypertensive crisis", "domain": "Cardiology", "primary_condition": "Hypertensive emergency"},
            {"record_id": "R3", "title": "Dengue fever", "domain": "Infectious", "primary_condition": "Dengue"}]


def test_curriculum_tiering_uses_whole_words_and_real_counts(tmp_path, capsys):
    g = _gen(); g.configure_workspace(tmp_path)
    g.build_modality_2_curriculum(_recs(), {})
    out = capsys.readouterr().out
    assert "Classified 3 cases" in out                      # was always "137"
    rows = {r["record_id"]: r for r in csv.DictReader((tmp_path / "03_NORMALIZED_CORPUS" / "TABLES" / "residency_curriculum_tiers.csv").open(encoding="utf-8"))}
    assert rows["R1"]["curriculum_tier"] != "Tier 3"        # 'gra' is not a substring of 'Graves'
    assert rows["R2"]["curriculum_tier"] != "Tier 1"        # 'iv' is not a substring of 'Hypertensive'
    assert rows["R3"]["curriculum_tier"] == "Tier 1"


def test_generated_links_point_at_the_workspace_not_a_literal_drive(tmp_path):
    g = _gen(); g.configure_workspace(tmp_path)
    g.build_modality_2_curriculum(_recs(), {})
    md = next((tmp_path / "08_EXPORTS" / "CURRICULUM").glob("*.md"))
    assert "file:///D:/HABIJABI_FULL" not in md.read_text(encoding="utf-8")
