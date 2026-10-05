"""validate_run_trace: exit codes and empty-trace handling."""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "validate_run_trace.py"


def run(path):
    return subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)


def test_valid_trace_passes(tmp_path):
    f = tmp_path / "t.json"
    f.write_text(
        json.dumps({
            "trace_status": "COMPLETE",
            "trace_note": "ok",
            "funnel": [{"stage": "Available", "status": "VERIFIED", "count": 3, "detail": "d"}],
        }),
        encoding="utf-8",
    )
    assert run(f).returncode == 0


def test_non_utf8_file_is_a_clean_exit_2_not_a_traceback(tmp_path):
    f = tmp_path / "t.json"
    f.write_bytes(b'{"trace_status": "\xff\xfe"}')
    result = run(f)
    assert result.returncode == 2
    assert "Traceback" not in result.stderr


def test_complete_trace_with_an_empty_funnel_is_invalid(tmp_path):
    f = tmp_path / "t.json"
    f.write_text(
        json.dumps({"trace_status": "COMPLETE", "trace_note": "ok", "funnel": []}),
        encoding="utf-8",
    )
    assert run(f).returncode == 2
