"""Unit tests for Unified Medical CDSS Orchestrator logic and bug fixes."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import scripts.unified_orchestrator as uo


def test_build_context_packet_dict_results(tmp_path):
    """Verify run_build_context_packet parses dict of books correctly without AttributeError."""
    simulated_dict = {
        "Davidson_25": [
            {"chunk_id": "ch16_01", "heading": "Infective Endocarditis", "text": "Davidson text"}
        ],
        "Harrison_22": [
            {"chunk_id": "ch260_01", "heading": "Infective Endocarditis", "text": "Harrison text"}
        ],
        "Hurst_15": [
            {"chunk_id": "ch45_01", "heading": "Endocarditis", "text": "Hurst text"}
        ]
    }
    
    out_file = tmp_path / "test_packet.json"
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = json.dumps(simulated_dict)

    with patch("pathlib.Path.exists", return_value=True), \
         patch("subprocess.run", return_value=mock_proc):
        packet = uo.run_build_context_packet("Infective Endocarditis", output_path=str(out_file))

    assert len(packet["core_spine_chunks"]) == 1
    assert packet["core_spine_chunks"][0]["chunk_id"] == "ch16_01"
    assert len(packet["beyond_davidson_chunks"]) == 2
    assert out_file.exists()
    
    saved_data = json.loads(out_file.read_text(encoding="utf-8"))
    assert saved_data["topic"] == "Infective Endocarditis"
    assert len(saved_data["core_spine_chunks"]) == 1


def test_run_federated_query_passes_compress_and_preserves_json():
    """Verify run_federated_query passes --compress and avoids token budgeting on JSON output."""
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = json.dumps({"test": "data" * 2000})
    mock_proc.stderr = ""

    with patch("pathlib.Path.exists", return_value=True), \
         patch("subprocess.run", return_value=mock_proc) as mock_sub, \
         patch("builtins.print") as mock_print:
        uo.run_federated_query("Endocarditis", as_json=True, compress=True)


    # Verify cmd arguments
    call_args = mock_sub.call_args[0][0]
    assert "--compress" in call_args
    assert "--json" in call_args

    # Verify printed stdout was not truncated with budget notice
    printed_str = mock_print.call_args[0][0]
    assert "[TRUNCATED:" not in printed_str
    assert json.loads(printed_str)["test"] is not None


def test_run_federated_query_propagates_exit_code():
    """Verify run_federated_query returns non-zero returncode from subprocess."""
    mock_proc = MagicMock()
    mock_proc.returncode = 2
    mock_proc.stdout = ""
    mock_proc.stderr = "Error in search"

    with patch("pathlib.Path.exists", return_value=True), \
         patch("subprocess.run", return_value=mock_proc):
        code = uo.run_federated_query("QueryWithFailure")
        assert code == 2


def test_run_case_vignette_includes_davidson(capsys):
    """Verify run_case_vignette includes Davidson evaluation."""
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = "Retrieved chunks"
    mock_proc.stderr = ""

    with patch("pathlib.Path.exists", return_value=True), \
         patch("scripts.unified_orchestrator.get_harrison_router", return_value=None), \
         patch("scripts.unified_orchestrator.get_hurst_router", return_value=None), \
         patch("scripts.unified_orchestrator.get_kumar_router", return_value=None), \
         patch("subprocess.run", return_value=mock_proc):
        code = uo.run_case_vignette("65yo male with chest pain")
        assert code == 0

    captured = capsys.readouterr()
    assert "[DAVIDSON 25TH ED - CORE MEDICINE EVALUATION]" in captured.out

