"""Regression tests for Version Manager v1.2.0."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from scripts.bump_version import (
    apply_version_bump,
    audit_suite,
    bump_all,
    bump_semver,
    check_consistency,
    discover_skill_suite,
    discover_versions,
    normalize_semver,
    parse_semver,
    verify_versions,
)


def test_parse_semver_valid_and_build_metadata():
    assert parse_semver("1.0.0") == (1, 0, 0, None)
    assert parse_semver("v2.24.0") == (2, 24, 0, None)
    assert parse_semver("0.1.0-alpha.1") == (0, 1, 0, "alpha.1")
    assert parse_semver("3.0.0-rc.2+build.7") == (3, 0, 0, "rc.2+build.7")
    assert normalize_semver("v1.2.3+abc.7") == "1.2.3+abc.7"


def test_parse_semver_invalid():
    for value in ["invalid", "1.2", "1.2.3.4", "01.2.3"]:
        with pytest.raises(ValueError):
            normalize_semver(value)


def test_bump_semver():
    assert bump_semver("1.2.3", "major") == "2.0.0"
    assert bump_semver("1.2.3-rc.1", "minor") == "1.3.0"
    assert bump_semver("1.2.3+build.9", "patch") == "1.2.4"
    assert bump_semver("1.2.3", "2.0.0-rc.1+build.3") == "2.0.0-rc.1+build.3"


@pytest.fixture
def mock_project():
    root = Path(tempfile.mkdtemp(prefix="test_ver_"))
    (root / "SKILL.md").write_text(
        "---\nname: test-skill\nversion: 1.2.0\ndescription: Test\n---\n\n# Test Skill (v1.2.0)\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        "# Test Skill (v1.2.0)\n\n**Version:** 1.2.0\n\nInstalled (v1.2.0)\n",
        encoding="utf-8",
    )
    (root / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [1.2.0] - 2026-09-01\n\n### Added\n- Initial.\n",
        encoding="utf-8",
    )
    (root / "agents").mkdir()
    (root / "agents" / "openai.yaml").write_text("name: test-skill\nversion: 1.2.0\n", encoding="utf-8")
    (root / "pyproject.toml").write_text('[project]\nname="x"\nversion = "1.2.0"\n', encoding="utf-8")
    (root / "package.json").write_text('{"name":"x","version":"1.2.0"}\n', encoding="utf-8")
    (root / "src").mkdir()
    (root / "src" / "__init__.py").write_text('__version__ = "1.2.0"\n', encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_version.py").write_text(
        'def test_version():\n    assert __version__ == "1.2.0"\n', encoding="utf-8"
    )
    yield str(root)
    shutil.rmtree(root, ignore_errors=True)


def test_discover_and_verify_consistent(mock_project):
    decls = discover_versions(mock_project)
    kinds = {d.file_type for d in decls}
    assert "SKILL_FRONTMATTER" in kinds
    assert "OPENAI_YAML" in kinds
    assert "README_VERSION" in kinds
    assert "CHANGELOG_LATEST" in kinds
    assert len(decls) >= 10
    ok, canonical, mismatches = verify_versions(mock_project)
    assert ok is True
    assert canonical == "1.2.0"
    assert mismatches == []


def test_verify_zero_declarations_fails(tmp_path):
    (tmp_path / "README.md").write_text("No current version here.\n", encoding="utf-8")
    consistent, current, groups = check_consistency(str(tmp_path))
    assert consistent is False
    assert current is None
    assert groups == {}
    verified, canonical, mismatches = verify_versions(str(tmp_path))
    assert verified is False
    assert canonical is None
    assert mismatches == []


def test_detects_openai_yaml_drift(mock_project):
    path = Path(mock_project) / "agents" / "openai.yaml"
    path.write_text("name: test-skill\nversion: 1.1.9\n", encoding="utf-8")
    ok, canonical, mismatches = verify_versions(mock_project)
    assert ok is False
    assert any(d.file_type == "OPENAI_YAML" for d in mismatches)


def test_nested_metadata_version_research_curator_pattern(tmp_path):
    (tmp_path / "SKILL.md").write_text(
        '---\nname: research-method-curator\ndescription: Test\nmetadata:\n  version: "1.1.2"\n  status: "stable"\n---\n',
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# Research Method Curator\n\nVersion: **1.1.2**\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\n## 1.1.2 — 2026-09-23\n", encoding="utf-8")
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "openai.yaml").write_text("name: research-method-curator\nversion: 1.1.2\n", encoding="utf-8")
    decls = discover_versions(str(tmp_path))
    assert any(d.file_type == "SKILL_METADATA_VERSION" and d.current_version == "1.1.2" for d in decls)
    ok, canonical, _ = verify_versions(str(tmp_path))
    assert ok is True
    assert canonical == "1.1.2"


def test_bump_nested_metadata_and_openai_yaml(tmp_path):
    (tmp_path / "SKILL.md").write_text(
        '---\nname: x\ndescription: Test\nmetadata:\n  version: "1.1.2"\n---\n', encoding="utf-8"
    )
    (tmp_path / "README.md").write_text("Version: **1.1.2**\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\n## [1.1.2] - 2026-09-23\n", encoding="utf-8")
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "openai.yaml").write_text("name: x\nversion: 1.1.2\n", encoding="utf-8")
    success, target = bump_all(str(tmp_path), "patch", message="Repair metadata", category="Fixed")
    assert success is True
    assert target == "1.1.3"
    assert 'version: "1.1.3"' in (tmp_path / "SKILL.md").read_text(encoding="utf-8")
    assert "version: 1.1.3" in (tmp_path / "agents" / "openai.yaml").read_text(encoding="utf-8")
    assert "Version: **1.1.3**" in (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "## [1.1.3]" in (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")


def test_full_semver_update(mock_project):
    changed = apply_version_bump(mock_project, "2.0.0-rc.1+build.7", "### Added\n- RC")
    assert changed
    ok, canonical, _ = verify_versions(mock_project)
    assert ok is True
    assert canonical == "2.0.0-rc.1+build.7"


def test_dry_run_does_not_write(mock_project):
    before = (Path(mock_project) / "SKILL.md").read_text(encoding="utf-8")
    success, target = bump_all(mock_project, "minor", message="New feature", category="Added", dry_run=True)
    after = (Path(mock_project) / "SKILL.md").read_text(encoding="utf-8")
    assert success is True
    assert target == "1.3.0"
    assert after == before


def test_changelog_historical_versions_are_not_treated_as_drift(tmp_path):
    (tmp_path / "SKILL.md").write_text("---\nname: x\nversion: 2.0.0\ndescription: x\n---\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [2.0.0] - 2026-09-23\n\n## [1.9.0] - 2026-09-01\n", encoding="utf-8"
    )
    ok, canonical, _ = verify_versions(str(tmp_path))
    assert ok is True
    assert canonical == "2.0.0"


def test_suite_marks_zero_declaration_skill_failed(tmp_path):
    a = tmp_path / "skill-a"
    a.mkdir()
    (a / "SKILL.md").write_text("# malformed/no frontmatter version\n", encoding="utf-8")
    b = tmp_path / "skill-b"
    b.mkdir()
    (b / "SKILL.md").write_text("---\nname: skill-b\nversion: 1.0.0\ndescription: x\n---\n", encoding="utf-8")
    ok, results = audit_suite(str(tmp_path))
    assert ok is False
    ar = next(r for r in results if r["name"] == "skill-a")
    assert ar["declarations"] == 0
    assert ar["is_consistent"] is False


def test_discover_skill_suite(tmp_path):
    for name, version in [("skill-alpha", "1.0.0"), ("skill-beta", "2.1.0")]:
        d = tmp_path / name
        d.mkdir()
        (d / "SKILL.md").write_text(f"---\nname: {name}\nversion: {version}\ndescription: x\n---\n", encoding="utf-8")
    suite = discover_skill_suite(str(tmp_path))
    assert {n for n, _ in suite} == {"skill-alpha", "skill-beta"}
    filtered = discover_skill_suite(str(tmp_path), name_filter="alpha")
    assert [n for n, _ in filtered] == ["skill-alpha"]


def test_cli_verify_zero_declarations_exits_nonzero(tmp_path):
    script = Path(__file__).parents[1] / "scripts" / "bump_version.py"
    proc = subprocess.run([sys.executable, str(script), str(tmp_path), "--verify"], capture_output=True, text=True)
    assert proc.returncode == 1
    assert "No version declarations" in proc.stderr


def test_relative_bump_refuses_drift(tmp_path):
    (tmp_path / "SKILL.md").write_text("---\nname: x\nversion: 1.2.0\ndescription: x\n---\n", encoding="utf-8")
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "openai.yaml").write_text("name: x\nversion: 1.3.0\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="baseline ambiguous"):
        bump_all(str(tmp_path), "patch")
    success, target = bump_all(str(tmp_path), "1.3.1", message="Reconcile drift")
    assert success is True
    assert target == "1.3.1"



# --- v1.2.1 lineage-reconciliation regressions ---
def test_skill_version_constant_is_discovered_and_updated(tmp_path):
    (tmp_path / "SKILL.md").write_text(
        "---\nname: x\nversion: 1.2.0\ndescription: x\n---\n", encoding="utf-8"
    )
    (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [1.2.0] - 2026-09-23\n", encoding="utf-8"
    )
    (tmp_path / "scripts").mkdir()
    const = tmp_path / "scripts" / "auditor.py"
    const.write_text('SKILL_VERSION = "1.1.9"\n', encoding="utf-8")
    consistent, _, groups = check_consistency(str(tmp_path))
    assert consistent is False
    assert {"1.1.9", "1.2.0"} <= set(groups)
    apply_version_bump(str(tmp_path), "1.2.1", "### Fixed\n- Sync constant")
    assert 'SKILL_VERSION = "1.2.1"' in const.read_text(encoding="utf-8")
    ok, canonical, _ = verify_versions(str(tmp_path))
    assert ok is True and canonical == "1.2.1"


def test_crlf_style_is_preserved_during_bump(tmp_path):
    skill = tmp_path / "SKILL.md"
    changelog = tmp_path / "CHANGELOG.md"
    skill.write_bytes(b"---\r\nname: x\r\nversion: 1.2.0\r\ndescription: x\r\n---\r\n")
    changelog.write_bytes(b"# Changelog\r\n\r\n## [1.2.0] - 2026-09-23\r\n")
    apply_version_bump(str(tmp_path), "1.2.1", "### Fixed\n- Preserve newlines")
    for path in (skill, changelog):
        data = path.read_bytes()
        assert b"\r\n" in data
        assert b"\n" not in data.replace(b"\r\n", b"")


def test_cli_suite_rejects_mutation_flags(tmp_path):
    skill = tmp_path / "skill-a"
    skill.mkdir()
    (skill / "SKILL.md").write_text(
        "---\nname: skill-a\nversion: 1.0.0\ndescription: x\n---\n", encoding="utf-8"
    )
    script = Path(__file__).parents[1] / "scripts" / "bump_version.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--suite", str(tmp_path), "--bump", "patch"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert "--suite is audit-only" in proc.stderr
