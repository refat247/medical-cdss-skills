"""Version consistency test for davidson-ocr-preready."""
import os
import re
import pytest
from preready import __version__


def test_version_consistency():
    pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    skill_path = os.path.join(pkg_dir, "SKILL.md")
    readme_path = os.path.join(pkg_dir, "README.md")
    changelog_path = os.path.join(pkg_dir, "CHANGELOG.md")

    # SKILL.md
    with open(skill_path, "r", encoding="utf-8") as f:
        skill_text = f.read()
    skill_v = re.search(r"version:\s*([0-9\.]+)", skill_text).group(1)

    # CHANGELOG.md
    with open(changelog_path, "r", encoding="utf-8") as f:
        changelog_text = f.read()
    changelog_v = re.search(r"##\s*\[([0-9\.]+)\]", changelog_text).group(1)

    assert __version__ == skill_v
    assert __version__ == changelog_v

