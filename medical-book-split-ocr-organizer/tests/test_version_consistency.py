from pathlib import Path
import re


def test_version_consistency():
    root = Path(__file__).resolve().parent.parent
    # Read SKILL.md
    skill_text = (root / "SKILL.md").read_text(encoding="utf-8")
    skill_v = re.search(r"^version:\s*([0-9\.]+)", skill_text, re.M).group(1)

    # Read __init__.py
    init_text = (root / "__init__.py").read_text(encoding="utf-8")
    init_v = re.search(r'^__version__\s*=\s*["\']([0-9\.]+)["\']', init_text, re.M).group(1)

    # Read CHANGELOG.md
    changelog_text = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    changelog_v = re.search(r"^##\s*\[([0-9\.]+)\]", changelog_text, re.M).group(1)

    assert skill_v == "1.3.0"
    assert init_v == "1.2.0"
    assert changelog_v == "1.3.0"
