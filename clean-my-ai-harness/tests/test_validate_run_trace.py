"""validate_run_trace: exit codes and empty-trace handling (second-sweep D-31)."""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "validate_run_trace.py"


def run(path):
    return subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)


def test_valid_trace_passes(tmp_path):
    f = tmp_path / "t.json"
    f.write_text(json.dumps({"trace_status": "COMPLETE", "trace_note": "ok",
                             "funnel": [{"stage": "Available", "status": "VERIFIED", "count": 3, "detail": "d"}]}))
    assert run(f).returncode == 0


def test_non_utf8_file_is_a_clean_exit_2_not_a_traceback(tmp_path):
    f = tmp_path / "t.json"
    f.write_bytes(b'{"trace_status": "\xff\xfe"}')
    r = run(f)
    assert r.returncode == 2 and "Traceback" not in r.stderr


def test_complete_trace_with_an_empty_funnel_is_invalid(tmp_path):
    f = tmp_path / "t.json"
    f.write_text(json.dumps({"trace_status": "COMPLETE", "trace_note": "ok", "funnel": []}))
    assert run(f).returncode == 2
