"""Version consistency tests for medical-rag-orchestrator."""
from pathlib import Path
import re

SKILL_DIR = Path(__file__).resolve().parent.parent

def test_version_consistency():
    skill_md = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    m = re.search(r"version:\s*([0-9\.]+)", skill_md)
    assert m is not None
    skill_v = m.group(1)

    changelog = (SKILL_DIR / "CHANGELOG.md").read_text(encoding="utf-8")
    m2 = re.search(r"## \[([0-9\.]+)\]", changelog)
    assert m2 is not None
    changelog_v = m2.group(1)

    import sys
    sys.path.insert(0, str(SKILL_DIR / "scripts"))
    import orchestrator

    assert skill_v == changelog_v
    assert skill_v == orchestrator.__version__

