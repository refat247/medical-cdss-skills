"""Regression tests for Claude audit findings: exit codes and fail-closed context packets."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import unified_orchestrator as uo  # noqa: E402


def stub(tmp_path, payload, code=0):
    s = tmp_path / "cdss_federated_search.py"
    s.write_text(f"import sys\nprint({json.dumps(json.dumps(payload))})\nsys.exit({code})\n", encoding="utf-8")
    return s


def test_no_sources_is_failure():
    assert uo._finish([], "test") == 1
    assert uo._finish([0, 0], "test") == 0


def test_packet_fails_when_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(uo, "FEDERATED_SEARCH_SCRIPT", stub(tmp_path, {"Davidson_25": [], "Harrison_22": []}))
    out = tmp_path / "p.json"
    assert uo.run_build_context_packet("AF", str(out)) is None
    assert not out.exists()


def test_packet_fails_when_search_errors(tmp_path, monkeypatch):
    monkeypatch.setattr(uo, "FEDERATED_SEARCH_SCRIPT", stub(tmp_path, {}, code=2))
    assert uo.run_build_context_packet("AF") is None


def test_packet_excludes_error_entries(tmp_path, monkeypatch):
    payload = {"Davidson_25": [{"chunk_id": "L2-001", "excerpt": "x"}], "Harrison_22": [{"error": "db locked"}]}
    monkeypatch.setattr(uo, "FEDERATED_SEARCH_SCRIPT", stub(tmp_path, payload))
    pkt = uo.run_build_context_packet("AF")
    assert [c["chunk_id"] for c in pkt["core_spine_chunks"]] == ["L2-001"]
    assert pkt["beyond_davidson_chunks"] == []
    assert pkt["warnings"]


def test_no_hardcoded_user_paths():
    src = (Path(__file__).resolve().parent.parent / "scripts" / "unified_orchestrator.py").read_text(encoding="utf-8")
    assert r"C:\Users" not in src
