"""Regression coverage for the mechanical compiler subset salvaged from PR #1.

These tests intentionally exclude benchmark redesign, generated-router behavior,
BM25 retuning, and drug-safety-matrix semantics.
"""
import json

from scripts.compiler import CompilerConfig, MedicalBookIndexCompiler


CHUNKS = (
    "---\nchunk_id: C-1\nchunk_level: 2\ntopic_primary: \"Atrial fibrillation\"\nsemantic_type: management_step\n---\n"
    "AF and MI with T2DM; HbA1c 8%. Warfarin is mentioned.\n\n"
    "### Chunk 2 of 3\n"
    "---\nchunk_id: C-2\nchunk_level: 2\ntopic_primary: \"Parkinson's disease\"\nsemantic_type: clinical_feature\n---\n"
    "Tremor and rigidity.\n\n"
    "---\nchunk_id: C-3\nchunk_level: 2\ntopic_primary: \"Heart failure\"\nsemantic_type: concept_overview\n---\n"
    "Congestion and dyspnoea.\n"
)


def build(tmp_path, chunks=CHUNKS, **cfg_kw):
    corpus = tmp_path / "corpus" / "CH01"
    corpus.mkdir(parents=True)
    (corpus / "CH01_RAG_Optimised.md").write_text(chunks, encoding="utf-8")
    (corpus / "CH01_CHECKPOINT.json").write_text(
        json.dumps({"stage_completions": {
            "6": {"status": "COMPLETED"},
            "8": {"status": "COMPLETED", "trusted_for_downstream_use": True},
        }}),
        encoding="utf-8",
    )
    idx = tmp_path / "index.md"
    idx.write_text("# Index\nAtrial fibrillation, 10\nHeart failure, 20\n", encoding="utf-8")
    out = tmp_path / "out"
    cfg = CompilerConfig(
        book_title="Test Book",
        edition="1",
        corpus_root=str(tmp_path / "corpus"),
        index_markdown_path=str(idx),
        output_dir=str(out),
        asset_prefix="t",
        **cfg_kw,
    )
    return MedicalBookIndexCompiler(cfg), out


def test_file_starting_with_chunk_frontmatter_keeps_first_chunk(tmp_path):
    comp, out = build(tmp_path, skip_eval=True)
    comp.run_all()
    cat = json.loads((out / "t_chunks_master_catalog.json").read_text(encoding="utf-8"))
    assert [c["chunk_id"] for c in cat] == ["C-1", "C-2", "C-3"]


def test_inverted_index_keeps_short_acronyms_and_alphanumerics(tmp_path):
    comp, out = build(tmp_path, skip_eval=True)
    comp.run_all()
    inv = json.loads((out / "t_inverted_chunk_index.json").read_text(encoding="utf-8"))
    for token in ("af", "mi", "t2dm", "hba1c"):
        assert token in inv


def test_apostrophe_in_quoted_topic_is_preserved(tmp_path):
    comp, out = build(tmp_path, skip_eval=True)
    comp.run_all()
    cat = json.loads((out / "t_chunks_master_catalog.json").read_text(encoding="utf-8"))
    assert any(c["topic"] == "Parkinson's disease" for c in cat)


def test_trailing_chunk_heading_is_not_previous_chunk_body(tmp_path):
    comp, out = build(tmp_path, skip_eval=True)
    comp.run_all()
    cat = json.loads((out / "t_chunks_master_catalog.json").read_text(encoding="utf-8"))
    assert "### Chunk 2" not in cat[0]["body"]


def test_dry_run_writes_nothing(tmp_path):
    comp, out = build(tmp_path, dry_run=True, skip_eval=True)
    comp.run_all()
    assert not out.exists() or not any(out.iterdir())


def test_duplicate_acronym_preserves_distinct_expansions(tmp_path):
    comp, out = build(tmp_path, skip_eval=True)
    (tmp_path / "index.md").write_text(
        "# Index\nPulmonary embolism (PE), 10\nPre-eclampsia (PE), 20\nPulmonary embolism (PE), 30\n",
        encoding="utf-8",
    )
    comp.run_all()
    syn = json.loads((out / "cardiology_synonyms_and_acronyms.json").read_text(encoding="utf-8"))
    assert syn["PE"]["canonical_terms"] == ["Pulmonary embolism", "Pre-eclampsia"]


def test_page_anchors_do_not_parse_digits_inside_terms(tmp_path):
    comp, out = build(tmp_path, skip_eval=True)
    (tmp_path / "index.md").write_text(
        "# Index\nHbA1c, 12, 14-16, 20t, 21f\nSGLT2 inhibitors, 30\n",
        encoding="utf-8",
    )
    comp.run_all()
    anchors = json.loads((out / "t_typographical_anchors.json").read_text(encoding="utf-8"))
    got = {(a.get("page") or a.get("page_start"), a["anchor_type"]) for a in anchors}
    assert got == {("14", "page_interval"), ("20", "table_anchor"), ("21", "figure_anchor")}


def test_lowercase_initial_mixed_case_term_is_primary_entry(tmp_path):
    comp, out = build(tmp_path, skip_eval=True)
    (tmp_path / "index.md").write_text(
        "# Index\nAtrial fibrillation, 10\nin heart failure, 11\neGFR in, 80\nin CKD, 81\n",
        encoding="utf-8",
    )
    comp.run_all()
    hierarchy = json.loads((out / "index_concept_hierarchy.json").read_text(encoding="utf-8"))
    assert hierarchy["Atrial fibrillation, 10"] == ["in heart failure, 11"]
    assert hierarchy["eGFR in, 80"] == ["in CKD, 81"]


def _extra_chapter(tmp_path, folder, name, chunk_id):
    d = tmp_path / "corpus" / folder
    d.mkdir(parents=True)
    (d / f"{name}_RAG_Optimised.md").write_text(
        f"---\nchunk_id: {chunk_id}\nchunk_level: 2\ntopic_primary: \"Anaemia\"\nsemantic_type: clinical_feature\n---\nPallor.\n",
        encoding="utf-8",
    )
    (d / f"{name}_CHECKPOINT.json").write_text(
        json.dumps({"stage_completions": {
            "6": {"status": "COMPLETED"},
            "8": {"status": "COMPLETED", "trusted_for_downstream_use": True},
        }}),
        encoding="utf-8",
    )


def test_copy_filter_matches_path_tokens_not_substrings(tmp_path):
    comp, out = build(tmp_path, skip_eval=True)
    _extra_chapter(tmp_path, "unbundled_cases", "CH02", "C-keep")
    _extra_chapter(tmp_path, "audit_copy", "CH03", "C-drop")
    comp.run_all()
    cat = json.loads((out / "t_chunks_master_catalog.json").read_text(encoding="utf-8"))
    ids = {c["chunk_id"] for c in cat}
    assert "C-keep" in ids
    assert "C-drop" not in ids
