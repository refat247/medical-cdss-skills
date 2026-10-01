"""Zero-drift version consistency tests for clinical-preceptor-cdss-orchestrator."""
import os
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent

def test_version_declarations_match():
    # 1. Check scripts/__init__.py
    from scripts import __version__
    assert __version__ == "1.2.0"

    # 2. Check orchestrator.py
    from scripts.orchestrator import VERSION
    assert VERSION == "1.2.0"

    # 3. Check generate_extended_modalities.py
    from scripts.generate_extended_modalities import VERSION as EXT_VERSION
    assert EXT_VERSION == "1.2.0"

    # 4. Check SKILL.md frontmatter
    skill_md = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    m_fm = re.search(r"^version:\s*([0-9\.]+)", skill_md, re.MULTILINE)
    assert m_fm is not None
    skill_v = m_fm.group(1)
    assert skill_v == "1.2.0"

    # 5. Check CHANGELOG.md latest release
    changelog_md = (SKILL_DIR / "CHANGELOG.md").read_text(encoding="utf-8")
    m_cl = re.search(r"^##\s*\[([0-9\.]+)\]", changelog_md, re.MULTILINE)
    assert m_cl is not None
    changelog_v = m_cl.group(1)
    assert changelog_v == "1.2.0"
