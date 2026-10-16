import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_defense.py"
LEDGER = ROOT / "fixtures" / "angina_trimetazidine_ledger.json"
sys.path.insert(0, str(ROOT / "scripts"))
from render_defense import load, render  # noqa: E402


def test_four_shapes_differ():
    data = load(LEDGER)
    texts = {n: render(data, n) for n in (1, 2, 3, 4)}
    assert len(set(texts.values())) == 4
    assert "Ward limit:" in texts[1] or data["ward_limit"] in texts[1]
    for text in texts.values():
        assert data["ward_limit"] in text


def test_version_markers():
    data = load(LEDGER)
    v1, v2, v3, v4 = (render(data, n) for n in (1, 2, 3, 4))
    assert "## Books" in v1 and "## Guidelines" in v1 and "## Do not say" in v1
    assert "DO NOT SAY." not in v2
    assert "If asked:" in v3 and "What you may say:" in v3
    assert "DO NOT SAY." in v4 and "SUPPORTED." in v4 and "CONFLICT." in v4
    assert "Harrison L2-634" in v4
    assert "+33%" in v4


def test_cli_switch(tmp_path):
    outs = []
    for n in (1, 2, 3, 4):
        dest = tmp_path / f"v{n}.md"
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), str(LEDGER), "--output-version", str(n), "--out", str(dest)],
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, proc.stderr
        outs.append(dest.read_text(encoding="utf-8"))
    assert len(set(outs)) == 4


def test_package_version_agreement():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    yaml = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert 'version: "1.0.0"' in skill
    assert "**Version:** 1.0.0" in readme
    assert 'version: "1.0.0"' in yaml
    assert "## [1.0.0] - 2026-10-14" in changelog
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert ledger["groups"]
