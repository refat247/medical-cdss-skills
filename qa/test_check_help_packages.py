"""Regression tests for the repo-wide crash-class QA gate."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_all  # noqa: E402


def test_package_cli_with_relative_import_passes_help(tmp_path, monkeypatch):
    pkg = tmp_path / "skill" / "mypkg"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "util.py").write_text("X = 1\n", encoding="utf-8")
    cli = pkg / "cli.py"
    cli.write_text("import argparse\nfrom .util import X\n\n"
                   "def main():\n    argparse.ArgumentParser().parse_args()\n\n"
                   "if __name__ == '__main__':\n    main()\n", encoding="utf-8")
    monkeypatch.setattr(check_all, "ROOT", tmp_path)
    assert check_all.check_help([cli]) == []


def test_broken_script_is_still_reported(tmp_path, monkeypatch):
    s = tmp_path / "skill" / "bad.py"
    s.parent.mkdir()
    s.write_text("import argparse\nimport definitely_not_installed_xyz\n", encoding="utf-8")
    monkeypatch.setattr(check_all, "ROOT", tmp_path)
    assert len(check_all.check_help([s])) == 1


def test_pyflakes_skips_archived_checkpoint_migration(tmp_path, monkeypatch):
    one_off = tmp_path / "skill" / "scripts" / "maintenance" / "checkpoint_migrate_v1.py"
    one_off.parent.mkdir(parents=True)
    one_off.write_text("print(os.getcwd())\n", encoding="utf-8")
    monkeypatch.setattr(check_all, "ROOT", tmp_path)
    assert check_all.check_pyflakes([one_off]) == []


def test_redefinition_of_unused_is_not_a_crash_class(tmp_path, monkeypatch):
    script = tmp_path / "skill" / "script.py"
    script.parent.mkdir(parents=True)
    script.write_text("import json\njson = 1\n", encoding="utf-8")
    monkeypatch.setattr(check_all, "ROOT", tmp_path)
    assert check_all.check_pyflakes([script]) == []
