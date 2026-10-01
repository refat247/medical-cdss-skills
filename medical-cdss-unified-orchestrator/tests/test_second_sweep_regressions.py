"""Regression tests for the unified orchestrator (skill_audits/SECOND_SWEEP.md 3.10, U1-U7)."""
import json
import sys

import pytest

import scripts.unified_orchestrator as uo

ROUTER = ("import sys\nprint('ROUTER-' + sys.argv[0].split('/')[-3] if False else 'ROUTER-OK ' + ' '.join(sys.argv[1:]))\n")
FED = ("import sys, json\n"
       "a = sys.argv\nbook = a[a.index('--book')+1] if '--book' in a else 'all'\n"
       "print(json.dumps({'Davidson_25': [{'chunk_id': 'D-1', 'topic': 't'}]}) if '--json' in a else 'FED-OK book=' + book)\n")


def pkg(tmp_path, monkeypatch, books=("harrison", "hurst", "kumar"), fed=True):
    root = tmp_path / "pkg"
    root.mkdir()
    names = {"harrison": ("02_Harrison_22", "HARRISON_ROUTER_PKG"), "hurst": ("03_Hurst_The_Heart_15", "HURST_ROUTER_PKG"),
             "kumar": ("04_Kumar_and_Clark_11", "KUMAR_ROUTER_PKG")}
    monkeypatch.setattr(uo, "PACKAGE_DIR", root)
    for b, (d, attr) in names.items():
        p = root / d / "Index" / "cdss_qa_router.py"
        if b in books:
            p.parent.mkdir(parents=True)
            p.write_text(f"import sys\nprint('ROUTER-{b.upper()}', *sys.argv[1:])\n")
        monkeypatch.setattr(uo, attr, p)
    for attr in ("HARRISON_ROUTER_SRC", "HURST_ROUTER_SRC"):
        monkeypatch.setattr(uo, attr, root / "none.py")
    f = root / "cdss_federated_search.py"
    if fed:
        f.write_text(FED)
    monkeypatch.setattr(uo, "FEDERATED_SEARCH_SCRIPT", f)
    return root


def run_main(monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", ["uo", *argv])
    with pytest.raises(SystemExit) as e:
        uo.main()
    return e.value.code


def test_partial_results_do_not_exit_zero(tmp_path, monkeypatch, capsys):
    pkg(tmp_path, monkeypatch, books=("harrison",))            # hurst + kumar missing
    assert run_main(monkeypatch, "--diff", "Meningitis") == 3
    assert "PARTIAL" in capsys.readouterr().err


def test_allow_partial_restores_exit_zero(tmp_path, monkeypatch):
    pkg(tmp_path, monkeypatch, books=("harrison",))
    assert run_main(monkeypatch, "--diff", "Meningitis", "--allow-partial") == 0


def test_all_sources_present_exits_zero(tmp_path, monkeypatch):
    pkg(tmp_path, monkeypatch)
    assert run_main(monkeypatch, "--diff", "Meningitis") == 0


def test_book_flag_restricts_diff_to_that_book(tmp_path, monkeypatch, capfd):
    pkg(tmp_path, monkeypatch)
    assert run_main(monkeypatch, "--diff", "Meningitis", "--book", "harrison") == 0
    out = capfd.readouterr().out
    assert "ROUTER-HARRISON" in out and "ROUTER-HURST" not in out and "ROUTER-KUMAR" not in out and "FED-OK" not in out


def test_book_flag_restricts_therapy_and_outline(tmp_path, monkeypatch, capfd):
    pkg(tmp_path, monkeypatch)
    assert run_main(monkeypatch, "--outline", "DKA", "--book", "kumar") == 0
    out = capfd.readouterr().out
    assert "ROUTER-KUMAR" in out and "ROUTER-HARRISON" not in out


@pytest.mark.parametrize("flag", [["--diff", "x"], ["--outline", "x"], ["--vignette", "x"], ["--validate-therapy", "d", "c"]])
def test_json_is_refused_where_it_is_not_supported(tmp_path, monkeypatch, flag):
    pkg(tmp_path, monkeypatch)
    assert run_main(monkeypatch, *flag, "--json") == 2


def test_two_modes_at_once_is_an_error(tmp_path, monkeypatch):
    pkg(tmp_path, monkeypatch)
    assert run_main(monkeypatch, "--query", "a", "--diff", "b") == 2


def test_output_without_context_packet_is_an_error(tmp_path, monkeypatch):
    pkg(tmp_path, monkeypatch)
    assert run_main(monkeypatch, "--query", "a", "--output", str(tmp_path / "o.json")) == 2


def test_context_packet_is_honest_about_what_it_did_not_retrieve(tmp_path, monkeypatch):
    pkg(tmp_path, monkeypatch)
    out = tmp_path / "p.json"
    pkt = uo.run_build_context_packet("DKA", output_path=str(out))
    assert "ESC/AHA" not in json.dumps(pkt["source_hierarchy"])
    assert set(pkt["not_populated"]) >= {"exam_traps", "guideline_recommendations"}


def test_context_packet_with_a_failing_book_is_marked_incomplete(tmp_path, monkeypatch):
    pkg(tmp_path, monkeypatch)
    (tmp_path / "pkg" / "cdss_federated_search.py").write_text(
        "import json\nprint(json.dumps({'Davidson_25': [{'chunk_id': 'D-1'}], 'Harrison_22': [{'error': 'db locked'}]}))\n")
    pkt = uo.run_build_context_packet("DKA")
    assert pkt["complete"] is False and pkt["warnings"]


def test_kumar_has_the_same_unverified_fallback_policy_message(tmp_path, monkeypatch, capsys):
    pkg(tmp_path, monkeypatch, books=("harrison", "hurst"))
    uo.ACTIVE_BOOK = "kumar"
    try:
        assert uo.get_kumar_router() is None
    finally:
        uo.ACTIVE_BOOK = "all"
    assert "kumar" in " ".join(uo.SKIPPED).lower()
