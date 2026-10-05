"""Non-clinical orchestration robustness salvaged from PR #1."""
import json

import scripts.orchestrator as orch


def test_cmd_guard_audit_does_not_pass_enforce_ismp(monkeypatch):
    seen = {}

    def fake_run(cmd, **kwargs):
        seen["cmd"] = cmd
        return 0

    monkeypatch.setattr(orch, "run_subcommand", fake_run)
    assert orch.cmd_guard("X", fix=False, enforce_ismp=True) == 0
    assert "audit" in seen["cmd"]
    assert "--enforce-ismp" not in seen["cmd"]


def test_status_on_missing_directory_returns_false(tmp_path):
    assert orch.audit_book_status(tmp_path / "nope") is False


def test_publish_manifest_with_no_topics_is_an_error(tmp_path):
    manifest = tmp_path / "m.json"
    manifest.write_text(json.dumps({"chapter": "1", "title": "t", "topics": []}), encoding="utf-8")
    assert orch.cmd_publish_manifest(str(manifest), str(tmp_path)) == 1


def test_publish_manifest_with_string_topics_is_an_error_not_a_traceback(tmp_path):
    manifest = tmp_path / "m.json"
    manifest.write_text(json.dumps({"chapter": "1", "title": "t", "topics": ["a", "b"]}), encoding="utf-8")
    assert orch.cmd_publish_manifest(str(manifest), str(tmp_path)) == 1
