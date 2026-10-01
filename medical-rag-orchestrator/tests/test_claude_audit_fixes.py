"""Regression tests for Claude audit findings: trust gating, portable paths."""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "orchestrator.py"
spec = importlib.util.spec_from_file_location("orchestrator_under_test", SCRIPT)
orch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(orch)


def _fake_classifier(out_dir, chapter_name):
    """Stand-in for the pipeline's classify_trust(): trusted iff Stage 8 checkpoint flag is True."""
    import glob as _g
    cks = _g.glob(os.path.join(out_dir, "*_CHECKPOINT.json"))
    if not cks:
        return None
    try:
        st = json.load(open(cks[0], encoding="utf-8")).get("stage_completions", {})
    except ValueError:
        return {"trusted_for_downstream_use": False, "classification": "FAKE_UNREADABLE"}
    s8 = st.get("8", {}) or {}
    ok = st.get("6", {}).get("status") == "COMPLETED" and s8.get("trusted_for_downstream_use") is True
    return {"trusted_for_downstream_use": ok, "classification": "FAKE_OK" if ok else f"FAKE_{s8.get('status', 'NONE')}"}

orch.TRUST_CLASSIFIER = _fake_classifier


def chapter(tmp, name, stages=None, protected=False, raw=None):
    out = tmp / name / "rag_pipeline_output"
    out.mkdir(parents=True)
    (out / f"{name}_RAG_Optimised.md").write_text("x", encoding="utf-8")
    if protected:
        (out / "CORPUS_OUTPUT_PROTECTED.json").write_text("{}", encoding="utf-8")
    if raw is not None:
        (out / f"{name}_CHECKPOINT.json").write_text(raw, encoding="utf-8")
    elif stages is not None:
        (out / f"{name}_CHECKPOINT.json").write_text(json.dumps({"stage_completions": stages}), encoding="utf-8")
    return tmp / name


def ready(d):
    return orch.evaluate_chapter_trust([d])["ready"]


def test_trust_rules(tmp_path):
    C = {"status": "COMPLETED"}
    assert not ready(chapter(tmp_path, "protected", protected=True))  # marker is informational only
    assert ready(chapter(tmp_path, "trusted", {"6": C, "8": dict(C, trusted_for_downstream_use=True)}))
    assert not ready(chapter(tmp_path, "s8_untrusted", {"6": C, "8": dict(C, trusted_for_downstream_use=False)}))
    assert not ready(chapter(tmp_path, "s8_no_flag", {"6": C, "8": C}))
    assert not ready(chapter(tmp_path, "s6_only", {"6": C}))
    assert not ready(chapter(tmp_path, "s6_blocked", {"6": {"status": "BLOCKED"}}))
    assert not ready(chapter(tmp_path, "no_ckpt"))
    assert not ready(chapter(tmp_path, "bad_json", raw="{bad"))


def test_skills_root_is_not_hardcoded():
    assert orch.SKILLS_ROOT == Path(__file__).resolve().parents[2] or "CDSS_SKILLS_ROOT" in os.environ
    assert (orch.SKILLS_ROOT / "cdss-unicode-mojibake-guard" / "scripts" / "guard.py").exists()


def test_rag_skip_reruns_untrusted_chapter(tmp_path, capsys, monkeypatch):
    C = {"status": "COMPLETED"}
    ch = chapter(tmp_path, "Ch01", {"6": C, "8": dict(C, trusted_for_downstream_use=False)})
    src = ch / "Ch01.pdf.markdown_inlined.md"
    src.write_text("# x", encoding="utf-8")
    calls = []
    monkeypatch.setattr(orch, "run_subcommand", lambda cmd, **kw: calls.append(cmd) or 0)
    orch.cmd_rag(str(src), skip_completed=True)
    assert calls, "untrusted chapter must be re-run, not skipped"


def test_status_cli_runs(tmp_path):
    chapter(tmp_path, "Ch01", {"6": {"status": "COMPLETED"}})
    r = subprocess.run([sys.executable, str(SCRIPT), "status", "--book-dir", str(tmp_path)], capture_output=True, text=True)
    assert r.returncode == 0 and "RAG UNTRUSTED" in r.stdout  # real classifier: no gates -> not trusted


def test_canonical_output_dir_wins_over_side_copies(tmp_path):
    C = {"status": "COMPLETED"}
    ch = tmp_path / "Davidson_25_05_Nutrition.pdf"
    canon = ch / "rag_pipeline_output"
    cand = ch / "rag_pipeline_output_v22"
    for d, trusted in ((canon, True), (cand, False)):
        d.mkdir(parents=True)
        (d / "Ch05_RAG_Optimised.md").write_text("x", encoding="utf-8")
        (d / "Ch05_CHECKPOINT.json").write_text(json.dumps({"stage_completions": {
            "6": C, "8": dict(C, trusted_for_downstream_use=trusted)}}), encoding="utf-8")
    # make the side copy newer: must still not override the canonical folder
    os.utime(cand / "Ch05_CHECKPOINT.json", (9e9, 9e9))
    v = orch.evaluate_chapter_trust([ch])
    assert v["ready"] and v["output_dir"].endswith("rag_pipeline_output")


def test_real_pipeline_classifier_is_used(tmp_path):
    """With the real classify_trust(), a Stage 8 flag or a protection marker alone is never enough."""
    real = orch._load_trust_classifier()
    assert real is not None, "pipeline trust classifier must be importable from the skills folder"
    C = {"status": "COMPLETED"}
    d = chapter(tmp_path, "flag_only", {"6": C, "8": dict(C, trusted_for_downstream_use=True)}, protected=True)
    rec = real(str(d / "rag_pipeline_output"), "flag_only")
    assert rec and rec["trusted_for_downstream_use"] is False
