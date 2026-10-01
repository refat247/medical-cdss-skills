"""
Version consistency tests for cdss-unicode-mojibake-guard.
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from guard import __version__

import re

def test_version_consistency():
    skill_path = SCRIPTS_DIR.parent / "SKILL.md"
    changelog_path = SCRIPTS_DIR.parent / "CHANGELOG.md"

    skill_text = skill_path.read_text(encoding="utf-8")
    skill_v = re.search(r"version:\s*([0-9\.]+)", skill_text).group(1)

    changelog_text = changelog_path.read_text(encoding="utf-8")
    changelog_v = re.search(r"##\s*\[([0-9\.]+)\]", changelog_text).group(1)

    assert __version__ == skill_v
    assert __version__ == changelog_v

