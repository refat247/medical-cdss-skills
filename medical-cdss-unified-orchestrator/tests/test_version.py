"""Version consistency tests for medical-cdss-unified-orchestrator (v1.2.0)."""

import os
import re
from scripts import __version__


def test_version_matches_init():
    assert re.match(r"^\d+\.\d+\.\d+$", __version__)



def test_version_matches_skill_md():
    skill_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "SKILL.md")
    assert os.path.exists(skill_path)
    with open(skill_path, encoding="utf-8") as f:
        content = f.read()
    fm_match = re.search(r"^version:\s*([0-9\.]+)", content, re.MULTILINE)
    assert fm_match is not None
    assert fm_match.group(1) == __version__

    title_match = re.search(r"# Unified Medical CDSS Orchestrator \(v([0-9\.]+)\)", content)
    assert title_match is not None
    assert title_match.group(1) == __version__


def test_version_matches_readme_md():
    readme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "README.md")
    assert os.path.exists(readme_path)
    with open(readme_path, encoding="utf-8") as f:
        content = f.read()
    title_match = re.search(r"# Unified Medical CDSS Orchestrator \(v([0-9\.]+)\)", content)
    assert title_match is not None
    assert title_match.group(1) == __version__


def test_version_matches_changelog_md():
    changelog_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "CHANGELOG.md")
    assert os.path.exists(changelog_path)
    with open(changelog_path, encoding="utf-8") as f:
        content = f.read()
    header_match = re.search(r"## \[([0-9\.]+)\]", content)
    assert header_match is not None
    assert header_match.group(1) == __version__
