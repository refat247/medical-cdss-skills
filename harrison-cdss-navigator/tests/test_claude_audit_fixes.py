"""Regression test: navigator exits non-zero when its router is missing (was exit 0)."""
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "navigator.py"


def test_missing_router_exits_nonzero(tmp_path):
    env = dict(os.environ, CDSS_PACKAGE_DIR=str(tmp_path / "no_package"))
    r = subprocess.run([sys.executable, str(SCRIPT), "--diff", "X"], capture_output=True, text=True, env=env)
    if "UNPACKAGED build router" in r.stderr:  # a build-folder router exists on this machine
        return
    assert r.returncode == 1
    assert "Router not found" in r.stderr
