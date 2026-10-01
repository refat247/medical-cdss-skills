"""Regression test: the compiler indexes only trusted chapters unless --allow-unverified."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.compiler import CompilerConfig, MedicalBookIndexCompiler  # noqa: E402

C = {"status": "COMPLETED"}
CASES = {
    "trusted": {"6": C, "8": dict(C, trusted_for_downstream_use=True)},
    "marker_only": "MARKER",
    "untrusted": {"6": C, "8": dict(C, trusted_for_downstream_use=False)},
    "stopped_after_5": {"5": C},
    "blocked": {"6": {"status": "BLOCKED"}},
    "no_checkpoint": None,
    "bad_json": "RAW",
}


def build(tmp_path):
    for name, stages in CASES.items():
        out = tmp_path / "corpus" / name / "rag_pipeline_output"
        out.mkdir(parents=True)
        (out / f"{name}_RAG_Optimised.md").write_text(
            f"# header\n\n---\nchunk_id: {name}_L2_001\ntopic: T\n---\nbody text for {name}\n", encoding="utf-8")
        if stages == "MARKER":
            (out / "CORPUS_OUTPUT_PROTECTED.json").write_text("{}", encoding="utf-8")
        elif stages == "RAW":
            (out / f"{name}_CHECKPOINT.json").write_text("{bad", encoding="utf-8")
        elif stages is not None:
            (out / f"{name}_CHECKPOINT.json").write_text(json.dumps({"stage_completions": stages}), encoding="utf-8")
    (tmp_path / "idx.md").write_text("# Index\n", encoding="utf-8")


def catalog(tmp_path, allow):
    cfg = CompilerConfig(book_title="T", edition="1", corpus_root=str(tmp_path / "corpus"),
                         index_markdown_path=str(tmp_path / "idx.md"), output_dir=str(tmp_path / "out"),
                         skip_eval=True, allow_unverified=allow)
    comp = MedicalBookIndexCompiler(cfg)
    comp.phase_2_catalog_chunks_and_inverted_index()
    return {c["chunk_id"] for c in comp.chunks_catalog}


def test_only_trusted_chapters_indexed(tmp_path):
    build(tmp_path)
    assert catalog(tmp_path, allow=False) == {"trusted_L2_001"}


def test_allow_unverified_includes_all(tmp_path):
    build(tmp_path)
    assert len(catalog(tmp_path, allow=True)) == len(CASES)


def test_duplicate_copies_indexed_once(tmp_path):
    ok = {"stage_completions": {"6": C, "8": dict(C, trusted_for_downstream_use=True)}}
    for sub in ("Ch01.pdf/rag_pipeline_output", "Ch01.pdf/extracted_v23/rag_pipeline_output"):
        out = tmp_path / "corpus" / sub
        out.mkdir(parents=True)
        (out / "Ch01_RAG_Optimised.md").write_text("# h\n\n---\nchunk_id: Ch01_L2_001\ntopic: T\n---\nbody\n", encoding="utf-8")
        (out / "Ch01_CHECKPOINT.json").write_text(json.dumps(ok), encoding="utf-8")
    (tmp_path / "idx.md").write_text("# Index\n", encoding="utf-8")
    cfg = CompilerConfig(book_title="T", edition="1", corpus_root=str(tmp_path / "corpus"),
                         index_markdown_path=str(tmp_path / "idx.md"), output_dir=str(tmp_path / "out"), skip_eval=True)
    comp = MedicalBookIndexCompiler(cfg)
    comp.phase_2_catalog_chunks_and_inverted_index()
    assert [c["chunk_id"] for c in comp.chunks_catalog] == ["Ch01_L2_001"]


import pytest  # noqa: E402


@pytest.mark.real_classifier
def test_real_classifier_rejects_flag_only(tmp_path, monkeypatch):
    import scripts.compiler as comp
    monkeypatch.setattr(comp, "TRUST_CLASSIFIER", None)
    real = comp.get_trust_classifier()
    assert real is not None
    out = tmp_path / "Ch01.pdf" / "rag_pipeline_output"
    out.mkdir(parents=True)
    (out / "Ch01_RAG_Optimised.md").write_text("x", encoding="utf-8")
    (out / "Ch01_CHECKPOINT.json").write_text(json.dumps({"stage_completions": {
        "6": C, "8": dict(C, trusted_for_downstream_use=True)}}), encoding="utf-8")
    (out / "CORPUS_OUTPUT_PROTECTED.json").write_text("{}", encoding="utf-8")
    assert real(str(out), "Ch01.pdf")["trusted_for_downstream_use"] is False
