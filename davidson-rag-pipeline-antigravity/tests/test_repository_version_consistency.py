"""v2.6.2 — prevents the exact three-way version mismatch the v2.6.2
stabilization audit found (SKILL.md said 2.6.1, checkpoint_utils.py said
2.6.0, README.md said 2.6.0). Defines EXACT declaration locations for each
of the four sources of truth and fails clearly, naming which file(s)
disagree, rather than loosely parsing arbitrary prose.
"""
import os
import re

import pytest

from pipeline.checkpoint_utils import PIPELINE_VERSION

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(filename):
    with open(os.path.join(REPO_DIR, filename), encoding="utf-8") as f:
        return f.read()


def _skill_md_version():
    text = _read("SKILL.md")
    m = re.search(r'^version:\s*(\S+)', text, re.MULTILINE)
    assert m, "SKILL.md: no 'version:' line found in frontmatter"
    return m.group(1)


def _readme_version():
    text = _read("README.md")
    m = re.search(r'Installed \(v([\d.]+)\)', text)
    assert m, "README.md: no 'Installed (vX.Y.Z)' declaration found in Status section"
    return m.group(1)


def _changelog_latest_version():
    text = _read("CHANGELOG.md")
    m = re.search(r'^## \[([\d.]+)\]', text, re.MULTILINE)
    assert m, "CHANGELOG.md: no '## [X.Y.Z]' release heading found"
    return m.group(1)


def test_skill_md_version_matches_pipeline_version():
    assert _skill_md_version() == PIPELINE_VERSION, (
        f"SKILL.md frontmatter version ({_skill_md_version()}) != "
        f"checkpoint_utils.PIPELINE_VERSION ({PIPELINE_VERSION})"
    )


def test_readme_version_matches_pipeline_version():
    assert _readme_version() == PIPELINE_VERSION, (
        f"README.md 'Installed (vX)' ({_readme_version()}) != "
        f"checkpoint_utils.PIPELINE_VERSION ({PIPELINE_VERSION})"
    )


def test_changelog_latest_heading_matches_pipeline_version():
    assert _changelog_latest_version() == PIPELINE_VERSION, (
        f"CHANGELOG.md's latest '## [X.Y.Z]' heading ({_changelog_latest_version()}) != "
        f"checkpoint_utils.PIPELINE_VERSION ({PIPELINE_VERSION})"
    )


def test_all_four_version_declarations_are_mutually_consistent():
    """Single, unambiguous failure message naming exactly which of the
    four sources disagree, per the task's requirement to fail clearly
    rather than parse prose loosely."""
    declared = {
        "SKILL.md frontmatter": _skill_md_version(),
        "checkpoint_utils.PIPELINE_VERSION": PIPELINE_VERSION,
        "README.md 'Installed (vX)'": _readme_version(),
        "CHANGELOG.md latest heading": _changelog_latest_version(),
    }
    unique_values = set(declared.values())
    assert len(unique_values) == 1, (
        f"Version declarations disagree: {declared}"
    )


def test_pipeline_version_format():
    """Verifies PIPELINE_VERSION is a valid Semantic Version."""
    assert re.match(r"^\d+\.\d+\.\d+$", PIPELINE_VERSION) is not None


