"""Wrapper CONTRACT tests against a stub router (hermetic: no corpus needed).
They check how the navigator launches the router and reports its result; they say nothing about retrieval quality."""
import json
import os
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from scripts import navigator as navmod  # noqa: E402
from scripts.navigator import HurstNavigator  # noqa: E402


@pytest.fixture
def nav(tmp_path):
    stub = tmp_path / "cdss_qa_router.py"
    stub.write_text(Path(__file__).with_name("stub_router.py").read_text(encoding="utf-8"), encoding="utf-8")
    return HurstNavigator(router_path=str(stub))


def test_wrapper_returns_router_output(nav):
    out = nav.query("Atrial fibrillation")
    assert "Atrial fibrillation" in out
    assert navmod.LAST_RETURNCODE == 0


def test_router_failure_is_reported_not_hidden(nav, monkeypatch):
    monkeypatch.setenv("STUB_EXIT", "3")
    out = nav.query("x")
    assert "[ERROR]" in out and "code 3" in out
    assert "router crashed" in out                      # stderr is shown, not swallowed
    assert navmod.LAST_RETURNCODE == 3


def test_undecodable_bytes_are_visible_not_dropped(nav, monkeypatch):
    monkeypatch.setenv("STUB_BAD_BYTES", "1")
    out = nav.query("x")
    assert "\ufffd" in out                              # errors="replace": corruption stays visible


def test_json_output_is_never_truncated_by_the_word_budget(nav, monkeypatch):
    monkeypatch.setenv("STUB_LONG", "1")
    out = nav.run_router_cli(["--query", "x", "--json"])
    assert json.loads(out)["chunks"][0]["text"].count("word") == 3000


def test_missing_router_is_an_error_with_nonzero_status(tmp_path):
    n = HurstNavigator(router_path=str(tmp_path / "nope.py"))
    assert "[ERROR]" in n.query("x") and navmod.LAST_RETURNCODE == 1
