"""
Version consistency tests for cdss-retrieval-packager.
"""

from pathlib import Path
import re

SKILL_DIR = Path(__file__).resolve().parent.parent

import sys
SCRIPTS_DIR = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
import packager

def test_version_consistency():
    skill_md = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    m = re.search(r"version:\s*([0-9\.]+)", skill_md)
    assert m is not None, "Version not found in SKILL.md"
    skill_v = m.group(1)

    changelog = (SKILL_DIR / "CHANGELOG.md").read_text(encoding="utf-8")
    m2 = re.search(r"##\s*\[([0-9\.]+)\]", changelog)
    assert m2 is not None
    assert skill_v == m2.group(1)
    assert skill_v == packager.__version__

