"""Unit tests for Universal Version Bumper & Synchronizer."""
import os
import shutil
import tempfile
import pytest
from scripts.bump_version import (
    parse_semver,
    bump_semver,
    discover_versions,
    bump_all,
    verify_versions,
    discover_skill_suite,
    audit_suite,
)


def test_parse_semver_valid():
    assert parse_semver("1.0.0") == (1, 0, 0, None)
    assert parse_semver("v2.24.0") == (2, 24, 0, None)
    assert parse_semver("0.1.0-alpha.1") == (0, 1, 0, "alpha.1")
    assert parse_semver("3.0.0-rc.2") == (3, 0, 0, "rc.2")


def test_parse_semver_invalid():
    with pytest.raises(ValueError):
        parse_semver("invalid")
    with pytest.raises(ValueError):
        parse_semver("1.2")
    with pytest.raises(ValueError):
        parse_semver("1.2.3.4")


def test_bump_semver():
    assert bump_semver("1.2.3", "major") == "2.0.0"
    assert bump_semver("1.2.3", "minor") == "1.3.0"
    assert bump_semver("1.2.3", "patch") == "1.2.4"
    assert bump_semver("v1.2.3", "patch") == "1.2.4"
    assert bump_semver("1.2.3", "2.0.0-rc.1") == "2.0.0-rc.1"


@pytest.fixture
def mock_project():
    """Creates a temporary project tree containing all supported version declarations."""
    temp_dir = tempfile.mkdtemp(prefix="test_ver_")
    
    # 1. SKILL.md
    skill_md = os.path.join(temp_dir, "SKILL.md")
    with open(skill_md, "w", encoding="utf-8") as f:
        f.write("---\nname: test-skill\nversion: 1.2.0\ndescription: Test description\n---\n\n# Test Skill (v1.2.0)\n")
        
    # 2. pyproject.toml
    pyproj = os.path.join(temp_dir, "pyproject.toml")
    with open(pyproj, "w", encoding="utf-8") as f:
        f.write('[project]\nname = "test-pkg"\nversion = "1.2.0"\n')
        
    # 3. package.json
    pkg_json = os.path.join(temp_dir, "package.json")
    with open(pkg_json, "w", encoding="utf-8") as f:
        f.write('{\n  "name": "test-pkg",\n  "version": "1.2.0"\n}\n')
        
    # 4. __init__.py
    src_dir = os.path.join(temp_dir, "src")
    os.makedirs(src_dir, exist_ok=True)
    init_py = os.path.join(src_dir, "__init__.py")
    with open(init_py, "w", encoding="utf-8") as f:
        f.write('__version__ = "1.2.0"\n')
        
    # 5. README.md
    readme_md = os.path.join(temp_dir, "README.md")
    with open(readme_md, "w", encoding="utf-8") as f:
        f.write('# Test Skill (v1.2.0)\n\nInstalled (v1.2.0)\n')
        
    # 6. CHANGELOG.md
    changelog_md = os.path.join(temp_dir, "CHANGELOG.md")
    with open(changelog_md, "w", encoding="utf-8") as f:
        f.write('# Changelog\n\n## [1.2.0] - 2026-09-01\n\n### Added\n- Initial feature.\n')
        
    # 7. tests/test_version.py
    tests_dir = os.path.join(temp_dir, "tests")
    os.makedirs(tests_dir, exist_ok=True)
    test_ver_py = os.path.join(tests_dir, "test_version.py")
    with open(test_ver_py, "w", encoding="utf-8") as f:
        f.write("def test_version():\n    assert " + "__version__" + " == \"1.2.0\"\n")

    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_version_manager_self_version():
    from scripts import __version__
    assert __version__ == "1.1.1"


def test_discover_and_verify_consistent(mock_project):
    declarations = discover_versions(mock_project)
    assert len(declarations) >= 7
    is_consistent, canonical, mismatches = verify_versions(mock_project)
    assert is_consistent is True
    assert canonical == "1.2.0"
    assert len(mismatches) == 0


def test_verify_detects_drift(mock_project):
    # Introduce drift in pyproject.toml
    pyproj = os.path.join(mock_project, "pyproject.toml")
    with open(pyproj, "w", encoding="utf-8") as f:
        f.write('[project]\nname = "test-pkg"\nversion = "1.3.0"\n')

    is_consistent, canonical, mismatches = verify_versions(mock_project)
    assert is_consistent is False
    assert len(mismatches) > 0


def test_atomic_bump(mock_project):
    # Bump minor: 1.2.0 -> 1.3.0
    success, new_ver = bump_all(
        root_dir=mock_project,
        bump_type="minor",
        message="Support clinical guidelines",
        category="Added",
    )
    assert success is True
    assert new_ver == "1.3.0"

    # Verify all files synchronized
    is_consistent, canonical, mismatches = verify_versions(mock_project)
    assert is_consistent is True
    assert canonical == "1.3.0"
    assert len(mismatches) == 0

    # Verify changelog updated with new section
    changelog_path = os.path.join(mock_project, "CHANGELOG.md")
    with open(changelog_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "## [1.3.0] -" in content
    assert "### Added" in content
    assert "- Support clinical guidelines" in content
    assert "## [1.2.0] -" in content


def test_discover_and_audit_suite(tmp_path):
    # Setup mock workspace with two skills
    skill1_dir = tmp_path / "skill-alpha"
    skill1_dir.mkdir()
    (skill1_dir / "SKILL.md").write_text("---\nname: skill-alpha\nversion: 1.0.0\n---\n", encoding="utf-8")

    skill2_dir = tmp_path / "skill-beta"
    skill2_dir.mkdir()
    (skill2_dir / "SKILL.md").write_text("---\nname: skill-beta\nversion: 2.1.0\n---\n", encoding="utf-8")

    # 1. Test discover_skill_suite
    suite = discover_skill_suite(str(tmp_path))
    names = [s[0] for s in suite]
    assert "skill-alpha" in names
    assert "skill-beta" in names

    # Filter test
    filtered = discover_skill_suite(str(tmp_path), name_filter="alpha")
    assert len(filtered) == 1
    assert filtered[0][0] == "skill-alpha"

    # 2. Test audit_suite consistent
    all_ok, results = audit_suite(str(tmp_path))
    assert all_ok is True
    assert len(results) == 2

    # 3. Test audit_suite with drift
    (skill1_dir / "pyproject.toml").write_text('[project]\nversion = "1.0.1"\n', encoding="utf-8")
    drift_ok, drift_results = audit_suite(str(tmp_path))
    assert drift_ok is False
    alpha_res = [r for r in drift_results if r["name"] == "skill-alpha"][0]
    assert alpha_res["is_consistent"] is False

