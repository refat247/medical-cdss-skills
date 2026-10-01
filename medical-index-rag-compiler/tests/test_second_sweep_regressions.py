"""Regression tests for the second audit sweep (skill_audits/SECOND_SWEEP.md 2.7-2.9, I1-I3)."""
import json
import os
import subprocess
import sys

import pytest

from scripts.compiler import CompilerConfig, MedicalBookIndexCompiler

CHUNKS = (
    "---\nchunk_id: C-1\nchunk_level: 2\ntopic_primary: \"Atrial fibrillation\"\nsemantic_type: management_step\n---\n"
    "AF and MI with T2DM; HbA1c 8%. Warfarin or apixaban is used for stroke prevention.\n\n"
    "---\nchunk_id: C-2\nchunk_level: 2\ntopic_primary: \"Parkinson's disease\"\nsemantic_type: clinical_feature\n---\n"
    "Tremor and rigidity. Levodopa is first line.\n\n"
    "---\nchunk_id: C-3\nchunk_level: 2\ntopic_primary: \"Heart failure\"\nsemantic_type: drug_info\n---\n"
    "Sacubitril/valsartan reduces mortality; furosemide relieves congestion.\n"
)


def build(tmp_path, chunks=CHUNKS, **cfg_kw):
    corpus = tmp_path / "corpus" / "CH01"
    corpus.mkdir(parents=True)
    (corpus / "CH01_RAG_Optimised.md").write_text(chunks, encoding="utf-8")   # NOTE: starts directly with '---'
    (corpus / "CH01_CHECKPOINT.json").write_text(json.dumps({"stage_completions": {
        "6": {"status": "COMPLETED"}, "8": {"status": "COMPLETED", "trusted_for_downstream_use": True}}}), encoding="utf-8")
    idx = tmp_path / "index.md"
    idx.write_text("# Index\nAtrial fibrillation, 10\nHeart failure, 20\n", encoding="utf-8")
    out = tmp_path / "out"
    cfg = CompilerConfig(book_title="Test Book", edition="1", corpus_root=str(tmp_path / "corpus"),
                         index_markdown_path=str(idx), output_dir=str(out), asset_prefix="t", **cfg_kw)
    return MedicalBookIndexCompiler(cfg), out


def test_first_chunk_of_a_file_starting_with_frontmatter_is_catalogued(tmp_path):
    comp, out = build(tmp_path, skip_eval=True)
    comp.run_all()
    cat = json.loads((out / "t_chunks_master_catalog.json").read_text(encoding="utf-8"))
    assert [c["chunk_id"] for c in cat] == ["C-1", "C-2", "C-3"]


def test_inverted_index_keeps_acronyms_and_alphanumerics(tmp_path):
    comp, out = build(tmp_path, skip_eval=True)
    comp.run_all()
    inv = json.loads((out / "t_inverted_chunk_index.json").read_text(encoding="utf-8"))
    for tok in ("af", "mi", "t2dm", "hba1c"):
        assert tok in inv, tok


def test_apostrophe_topic_is_not_truncated(tmp_path):
    comp, out = build(tmp_path, skip_eval=True)
    comp.run_all()
    cat = json.loads((out / "t_chunks_master_catalog.json").read_text(encoding="utf-8"))
    assert any(c["topic"] == "Parkinson's disease" for c in cat)


def test_dry_run_writes_nothing(tmp_path):
    comp, out = build(tmp_path, dry_run=True)
    comp.run_all()
    assert not out.exists() or not any(out.iterdir())


def test_scorecard_is_computed_not_hard_coded(tmp_path):
    comp, out = build(tmp_path)
    man = comp.run_all()
    card = (out / "BENCHMARK_SCORECARD.md").read_text(encoding="utf-8")
    assert "78.4%" not in card and "6.54 ms" not in card and "95.8%" not in card
    assert "SELF-TOPIC" in card.upper()
    raw = json.loads((out / "t_benchmark_raw_results.json").read_text(encoding="utf-8"))
    assert raw["queries"] and "latency_ns" in raw["queries"][0]
    assert man["benchmark_verdict"] in ("PASS", "FAIL")


def test_safety_matrix_is_derived_from_chunks_not_boilerplate(tmp_path):
    comp, out = build(tmp_path, skip_eval=True)
    comp.run_all()
    m = json.loads((out / "t_drug_disease_safety_matrix.json").read_text(encoding="utf-8"))["matrix"]
    assert "Cardiovascular pharmacotherapy" not in json.dumps(m)
    assert m["warfarin"]["matches_count"] == 1 and m["warfarin"]["chunk_ids"] == ["C-1"]
    assert m["metformin"]["matches_count"] == 0


def test_generated_router_really_retrieves_and_refuses_what_it_cannot_do(tmp_path):
    comp, out = build(tmp_path, skip_eval=True)
    comp.run_all()
    router = out / "cdss_qa_router.py"
    r = subprocess.run([sys.executable, str(router), "--query", "levodopa tremor", "--json"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    hits = json.loads(r.stdout)["results"]
    assert hits and hits[0]["chunk_id"] == "C-2"
    r2 = subprocess.run([sys.executable, str(router), "--validate-therapy", "warfarin"], capture_output=True, text=True)
    assert r2.returncode != 0 and "not implemented" in (r2.stdout + r2.stderr).lower()


def test_router_template_exposes_packager_class_interface():
    from scripts.compiler import ROUTER_TEMPLATE
    ns = {"__name__": "gen_router", "__file__": __file__}
    exec(compile(ROUTER_TEMPLATE.replace("__TITLE__", "T"), "router", "exec"), ns)
    assert hasattr(ns["CDSSRouter"], "retrieve_chunks")
    assert ns["HarrisonCDSSRouter"] is ns["CDSSRouter"]


def test_trailing_chunk_divider_heading_is_not_in_body():
    import re
    body = "text of chunk\n\n### Chunk 2 of 5\n"
    out = re.sub(r"(?:\r?\n)+#{1,6}[ \t]+Chunk\b[^\n]*\s*$", "", body.strip())
    assert out == "text of chunk"
