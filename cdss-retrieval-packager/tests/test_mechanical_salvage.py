"""Mechanical regression coverage salvaged from PR #1.

Clinical excerpt-compression and cross-book retrieval-routing changes are intentionally
excluded from this file and remain outside the mechanical salvage stream.
"""
import subprocess
import sys
from pathlib import Path

from scripts.packager import CDSSPackager


SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


def test_prune_dry_run_deletes_nothing(tmp_path):
    checkpoint = tmp_path / "Ch1_CHECKPOINT.json"
    archive = tmp_path / "x.zip"
    checkpoint.write_text("{}", encoding="utf-8")
    archive.write_text("z", encoding="utf-8")

    count = CDSSPackager(verbose=False).prune_directory(tmp_path, dry_run=True)

    assert count == 2
    assert checkpoint.exists()
    assert archive.exists()


def test_prune_can_preserve_trust_evidence(tmp_path):
    for name in (
        "Ch1_CHECKPOINT.json",
        "Ch1_ClinicalFidelityGate.json",
        "Ch1_Stage6_Validation.md",
        "junk.zip",
    ):
        (tmp_path / name).write_text("x", encoding="utf-8")

    CDSSPackager(verbose=False).prune_directory(tmp_path, keep_trust_evidence=True)

    assert (tmp_path / "Ch1_CHECKPOINT.json").exists()
    assert (tmp_path / "Ch1_ClinicalFidelityGate.json").exists()
    assert (tmp_path / "Ch1_Stage6_Validation.md").exists()
    assert not (tmp_path / "junk.zip").exists()


def test_patch_paths_reports_residual_hardcoded_paths(tmp_path):
    router = tmp_path / "cdss_qa_router.py"
    router.write_text(
        'BASE = r"D:\\\\somewhere\\\\else"\nINDEX_DIR = r"E:\\\\other"\n',
        encoding="utf-8",
    )

    packager = CDSSPackager(verbose=False)
    packager.patch_paths(tmp_path)

    assert packager.remaining_hardcoded
    assert "cdss_qa_router.py" in packager.remaining_hardcoded[0]


def test_verify_missing_package_directory_exits_nonzero(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "packager.py"), "verify", "-p", str(tmp_path / "missing")],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "package directory not found" in result.stderr.lower()


def test_verify_empty_package_exits_nonzero(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "packager.py"), "verify", "-p", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "no textbook router was verified" in result.stderr.lower()


def test_patch_paths_cli_fails_when_hardcoded_paths_remain(tmp_path):
    (tmp_path / "other.py").write_text('ROOT = r"Q:\\\\still-hardcoded"\n', encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "packager.py"), "patch-paths", "-p", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
