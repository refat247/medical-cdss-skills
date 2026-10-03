"""F10 / SECOND_SWEEP 1.20: a chapter edited after finalize must stop being trusted."""
import hashlib
import json

from pipeline.stages import trust_ledger
from pipeline.stages.mutation_guard import PROTECTION_MARKER_FILENAME


def _h(b):
    return hashlib.sha256(b).hexdigest()


def _chapter(tmp_path):
    (tmp_path / "CH_RAG_Optimised.md").write_bytes(b"rag")
    (tmp_path / "CH_chunks.md").write_bytes(b"chunks")
    marker = {"rag_optimised_sha256": _h(b"rag"), "chunks_sha256": _h(b"chunks"),
              "clinical_fidelity_gate_sha256": None}
    (tmp_path / PROTECTION_MARKER_FILENAME).write_text(json.dumps(marker), encoding="utf-8")
    return marker


def test_unchanged_files_have_no_mismatch(tmp_path):
    marker = _chapter(tmp_path)
    assert trust_ledger.marker_hash_mismatches(str(tmp_path), "CH", marker) == []


def test_edited_chunks_file_is_reported(tmp_path):
    marker = _chapter(tmp_path)
    (tmp_path / "CH_chunks.md").write_bytes(b"chunks edited")
    assert trust_ledger.marker_hash_mismatches(str(tmp_path), "CH", marker) == ["CH_chunks.md"]


def test_deleted_protected_file_is_reported(tmp_path):
    marker = _chapter(tmp_path)
    (tmp_path / "CH_RAG_Optimised.md").unlink()
    assert trust_ledger.marker_hash_mismatches(str(tmp_path), "CH", marker) == ["CH_RAG_Optimised.md"]


def test_trusted_record_is_downgraded_when_a_protected_file_changed(tmp_path, monkeypatch):
    _chapter(tmp_path)
    monkeypatch.setattr(trust_ledger, "_derive_prefix", lambda d: "CH")
    monkeypatch.setattr(trust_ledger.corpus_trust, "load_checkpoint_for_classification", lambda d, p: (None, ""))
    monkeypatch.setattr(trust_ledger.corpus_trust, "classify_trust", lambda *a, **k: {
        "classification": "CORPUS_TESTING_READY", "trusted_for_downstream_use": True, "reasons": [],
        "required_action": "", "protection_marker_present": True, "semantic_metadata_review_complete": True,
        "completeness_review_complete": True, "retrieval_ready": True})
    assert trust_ledger.build_chapter_trust_record(str(tmp_path), "CH")["trusted_for_downstream_use"] is True
    (tmp_path / "CH_chunks.md").write_bytes(b"tampered")
    rec = trust_ledger.build_chapter_trust_record(str(tmp_path), "CH")
    assert rec["trusted_for_downstream_use"] is False and rec["classification"] == "CORPUS_REVIEW_PENDING"
    assert any("CH_chunks.md" in r for r in rec["reasons"])
