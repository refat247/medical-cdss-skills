"""
Version consistency tests for cdss-bridge-note-publisher.
"""

from pathlib import Path
import re
import sys

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
from __init__ import __version__

SKILL_DIR = Path(__file__).resolve().parent.parent

def test_version_consistency():
    # Test __init__.py version is valid semver
    assert re.match(r"^\d+\.\d+\.\d+$", __version__)


    # Test SKILL.md frontmatter
    skill_md = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    m = re.search(r"version:\s*([0-9\.]+)", skill_md)
    assert m is not None
    assert m.group(1) == __version__

    # Test pyproject.toml
    pyproj = (SKILL_DIR / "pyproject.toml").read_text(encoding="utf-8")
    m2 = re.search(r'version\s*=\s*"([0-9\.]+)"', pyproj)
    assert m2 is not None
    assert m2.group(1) == __version__

    # Test CHANGELOG.md
    changelog = (SKILL_DIR / "CHANGELOG.md").read_text(encoding="utf-8")
    m3 = re.search(r"## \[([0-9\.]+)\]", changelog)
    assert m3 is not None
    assert m3.group(1) == __version__


def test_candidate_resolution_fail_closed(tmp_path):
    from synthesize_bridge_note import run_pipeline
    out = tmp_path / "notes"
    out.mkdir()
    (out / "Note_16.1_Murmurs.md").write_text("# Murmurs", encoding="utf-8")
    (out / "Note_16.2_Syncope.md").write_text("# Syncope", encoding="utf-8")

    # If asking for note_id='16.9' and topic='Asthma', neither matches, so it must return False (fail closed)
    res = run_pipeline(topic="Asthma", output_dir=out, package_dir=tmp_path, note_id="16.9")
    assert res is False

def test_note_id_boundary_no_prefix_match(tmp_path):
    from synthesize_bridge_note import run_pipeline
    out = tmp_path / "notes"
    out.mkdir()
    # Candidate is 16.12, but we will search for 16.1
    (out / "Note_16.12_Cardiac.md").write_text("# Cardiac", encoding="utf-8")

    # note_id='16.1' must NOT match '16.12'
    res = run_pipeline(topic="UnmatchedTopic", output_dir=out, package_dir=tmp_path, note_id="16.1")
    assert res is False

def test_topic_partial_collision_fail_closed(tmp_path):
    from synthesize_bridge_note import run_pipeline
    out = tmp_path / "notes"
    out.mkdir()
    (out / "Note_Cardiac_Auscultation.md").write_text("# Auscultation", encoding="utf-8")

    # Searching for 'Cardiac Arrhythmias' must NOT match 'Cardiac Auscultation'
    res = run_pipeline(topic="Cardiac Arrhythmias", output_dir=out, package_dir=tmp_path)
    assert res is False

def test_single_candidate_unmatched_fail_closed(tmp_path):
    from synthesize_bridge_note import run_pipeline
    out = tmp_path / "notes"
    out.mkdir()
    (out / "Note_04_Pneumonia.md").write_text("# Pneumonia", encoding="utf-8")

    # Single unrelated candidate must fail closed rather than silently publishing wrong topic
    res = run_pipeline(topic="Cardiac Arrhythmias", output_dir=out, package_dir=tmp_path)
    assert res is False

