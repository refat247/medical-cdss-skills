"""v2.6.8 -- RED/GREEN evidence for the Stage 5.4 output-persistence defect
found by CH11_RELATED_CHUNKS_CONTRACT_AUDIT.md.

Root cause (see the audit, section 2): Chapter 11's checkpoint records
`stage_completions["5.4"] = {"status": "COMPLETED", "linked_chunks": 105}`,
genuinely written by a real Stage 5.4 run on 2026-07-30. A later ad hoc
chunk-file regeneration (documented in BATCH1_CHAPTER_11_COMPLETION_REPORT.md
Category-B finding #6) rebuilt `chunks.md`'s content but did not reproduce
Stage 5.4's `related_chunks` frontmatter additions, and nothing re-validated
the claim afterward -- the checkpoint still says COMPLETED even though the
field it supposedly wrote is now completely absent from both `chunks.md` and
`RAG_Optimised.md`.

Before the enhancement (`_check_stage_5_4_persistence()`,
`verify_trusted_corpus_invariants.py.pre-v2.6.8-20260731T164754Z.bak`), the
invariant checker had ZERO references to `related_chunks` or "5.4" at all
(confirmed by direct grep) -- it could not have caught this defect. This
file's first test (`test_red_pre_enhancement_checker_does_not_catch_ch11_style_loss`)
captures that as genuine, executed RED evidence by importing the pre-v2.6.8
backup module directly and confirming it reports zero violations for the
exact Chapter-11-shaped fixture. Every other test below exercises the new
`_check_stage_5_4_persistence()` function directly (GREEN, post-enhancement).
"""
import importlib.util
import os
import sys
from importlib.machinery import SourceFileLoader
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline import verify_trusted_corpus_invariants as vtci  # noqa: E402
from pipeline import stages as live_stages  # noqa: E402

_REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PRE_V2_6_8_BACKUP = os.path.join(
    _REPO_DIR, "archive", "snapshots", "root", "verify_trusted_corpus_invariants.py.pre-v2.6.8-20260731T164754Z.bak"
)


def _l2_block(chunk_id, disease_focus, related_chunks=None, body="Body text."):
    lines = [
        "---",
        f"chunk_id: {chunk_id}",
        "chunk_level: 2",
        "semantic_type: clinical_feature",
        f"disease_focus: {disease_focus}",
    ]
    if related_chunks is not None:
        lines.append(f"related_chunks: {related_chunks}")
    lines.append("coverage_status: complete")
    lines.append("---")
    return "\n".join(lines) + "\n" + body + "\n"


def _write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _checkpoint(status="COMPLETED", linked_chunks=2):
    return {
        "stage_completions": {
            "5.4": {"status": status, "linked_chunks": linked_chunks} if status else None,
        }
    }


def _setup(tmp_path, chunks_text, rag_text=None, linked_chunks=2, status="COMPLETED",
           write_rag=True, prefix="TestCh11"):
    ch_dir = tmp_path / "11"
    ch_dir.mkdir(parents=True, exist_ok=True)
    _write(ch_dir / f"{prefix}_chunks.md", chunks_text)
    if write_rag:
        _write(ch_dir / f"{prefix}_RAG_Optimised.md",
               rag_text if rag_text is not None else chunks_text)
    checkpoint = None
    if status is not None:
        checkpoint = {"stage_completions": {"5.4": {"status": status, "linked_chunks": linked_chunks}}}
    return str(ch_dir), prefix, checkpoint


# --- Part 2: RED evidence against the exact Chapter-11 real-world shape ----

_CH11_STYLE_CHUNKS_NO_RELATED = (
    _l2_block("L2-001", "paracetamol")
    + _l2_block("L2-002", "paracetamol")
    + _l2_block("L2-003", "salicylates")
)


def test_red_pre_enhancement_checker_does_not_catch_ch11_style_loss(tmp_path):
    """Genuine RED evidence: the pre-v2.6.8 invariant checker (zero
    `related_chunks`/"5.4" references, confirmed by grep in the audit) does
    NOT flag a chapter whose checkpoint claims Stage 5.4 COMPLETED with
    linked_chunks=3 while chunks.md/RAG_Optimised.md have zero
    related_chunks fields anywhere -- the exact real Chapter 11 defect
    shape. Imports the actual pre-v2.6.8 backup module (not a rewritten
    stand-in) to prove this."""
    if not os.path.exists(_PRE_V2_6_8_BACKUP):
        pytest.skip("pre-v2.6.8 backup snapshot not present in standalone repository")
    loader = SourceFileLoader("vtci_pre_v2_6_8", _PRE_V2_6_8_BACKUP)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    old_vtci = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("stages", live_stages)
    sys.modules.setdefault("stages.trust_ledger", live_stages.trust_ledger)
    sys.modules.setdefault("stages.mutation_guard", live_stages.mutation_guard)
    sys.modules.setdefault("stages.stage_6_validation", live_stages.stage_6_validation)
    loader.exec_module(old_vtci)

    output_dir, prefix, checkpoint = _setup(
        tmp_path, _CH11_STYLE_CHUNKS_NO_RELATED, linked_chunks=3, status="COMPLETED"
    )
    # Minimal extra files the pre-existing checks in check_chapter() need are
    # deliberately omitted here since we call the private stage-agnostic
    # helper surface directly where possible; the pre-v2.6.8 module simply
    # has no function at all that reads related_chunks -- confirmed by the
    # grep in CH11_RELATED_CHUNKS_CONTRACT_AUDIT.md section 1. As a stronger,
    # more direct proof: the module has no such attribute whatsoever.
    assert not hasattr(old_vtci, "_check_stage_5_4_persistence")


# --- Part 7: GREEN evidence for the new _check_stage_5_4_persistence() ----

def test_clean_complete_stage_5_4_with_relationships_no_violation(tmp_path):
    chunks = (
        _l2_block("L2-001", "paracetamol", related_chunks="[L2-002]")
        + _l2_block("L2-002", "paracetamol", related_chunks="[L2-001]")
        + _l2_block("L2-003", "salicylates", related_chunks="[]")
    )
    output_dir, prefix, checkpoint = _setup(tmp_path, chunks, linked_chunks=3)
    violations = vtci._check_stage_5_4_persistence(output_dir, "11", prefix, checkpoint)
    assert violations == []


def test_all_empty_valid_relationships_no_violation(tmp_path):
    chunks = (
        _l2_block("L2-001", "paracetamol", related_chunks="[]")
        + _l2_block("L2-002", "salicylates", related_chunks="[]")
    )
    output_dir, prefix, checkpoint = _setup(tmp_path, chunks, linked_chunks=2)
    violations = vtci._check_stage_5_4_persistence(output_dir, "11", prefix, checkpoint)
    assert violations == []


def test_total_output_absence_with_checkpoint_complete_is_violation(tmp_path):
    """The Chapter-11 scenario itself: 0/N chunks have related_chunks at
    all, but the checkpoint claims Stage 5.4 COMPLETED."""
    output_dir, prefix, checkpoint = _setup(
        tmp_path, _CH11_STYLE_CHUNKS_NO_RELATED, linked_chunks=3
    )
    violations = vtci._check_stage_5_4_persistence(output_dir, "11", prefix, checkpoint)
    assert any(vtci._STAGE_5_4_LABEL in v for v in violations)
    assert any("total output loss" in v for v in violations)


def test_partial_field_loss_is_violation(tmp_path):
    chunks = (
        _l2_block("L2-001", "paracetamol", related_chunks="[L2-002]")
        + _l2_block("L2-002", "paracetamol")  # missing entirely
    )
    output_dir, prefix, checkpoint = _setup(tmp_path, chunks, linked_chunks=2)
    violations = vtci._check_stage_5_4_persistence(output_dir, "11", prefix, checkpoint)
    assert any("partial field loss" in v for v in violations)


def test_chunks_rag_mismatch_is_violation(tmp_path):
    chunks = _l2_block("L2-001", "paracetamol", related_chunks="[L2-002]") + \
        _l2_block("L2-002", "paracetamol", related_chunks="[L2-001]")
    rag = _l2_block("L2-001", "paracetamol", related_chunks="[]") + \
        _l2_block("L2-002", "paracetamol", related_chunks="[L2-001]")
    output_dir, prefix, checkpoint = _setup(tmp_path, chunks, rag_text=rag, linked_chunks=2)
    violations = vtci._check_stage_5_4_persistence(output_dir, "11", prefix, checkpoint)
    assert any("differs between chunks.md and RAG_Optimised.md" in v for v in violations)


def test_stale_linked_chunks_is_violation(tmp_path):
    chunks = _l2_block("L2-001", "paracetamol", related_chunks="[]") + \
        _l2_block("L2-002", "salicylates", related_chunks="[]")
    output_dir, prefix, checkpoint = _setup(tmp_path, chunks, linked_chunks=99)
    violations = vtci._check_stage_5_4_persistence(output_dir, "11", prefix, checkpoint)
    assert any("linked_chunks" in v and "does not equal" in v for v in violations)


def test_invalid_target_id_is_violation(tmp_path):
    chunks = _l2_block("L2-001", "paracetamol", related_chunks="[L2-999]")
    output_dir, prefix, checkpoint = _setup(tmp_path, chunks, linked_chunks=1)
    violations = vtci._check_stage_5_4_persistence(output_dir, "11", prefix, checkpoint)
    assert any("non-existent chunk" in v for v in violations)


def test_self_reference_is_violation(tmp_path):
    chunks = _l2_block("L2-001", "paracetamol", related_chunks="[L2-001]")
    output_dir, prefix, checkpoint = _setup(tmp_path, chunks, linked_chunks=1)
    violations = vtci._check_stage_5_4_persistence(output_dir, "11", prefix, checkpoint)
    assert any("self-reference" in v for v in violations)


def test_cross_disease_reference_is_violation(tmp_path):
    chunks = _l2_block("L2-001", "paracetamol", related_chunks="[L2-002]") + \
        _l2_block("L2-002", "salicylates", related_chunks="[L2-001]")
    output_dir, prefix, checkpoint = _setup(tmp_path, chunks, linked_chunks=2)
    violations = vtci._check_stage_5_4_persistence(output_dir, "11", prefix, checkpoint)
    assert any("cross-disease_focus" in v for v in violations)


def test_asymmetric_relationship_is_violation(tmp_path):
    chunks = _l2_block("L2-001", "paracetamol", related_chunks="[L2-002]") + \
        _l2_block("L2-002", "paracetamol", related_chunks="[]")
    output_dir, prefix, checkpoint = _setup(tmp_path, chunks, linked_chunks=2)
    violations = vtci._check_stage_5_4_persistence(output_dir, "11", prefix, checkpoint)
    assert any("asymmetric" in v for v in violations)


def test_malformed_list_syntax_is_violation(tmp_path):
    chunks = _l2_block("L2-001", "paracetamol", related_chunks="L2-002, L2-003")  # no brackets
    output_dir, prefix, checkpoint = _setup(tmp_path, chunks, linked_chunks=1)
    violations = vtci._check_stage_5_4_persistence(output_dir, "11", prefix, checkpoint)
    assert any("malformed" in v for v in violations)


def test_duplicate_related_chunks_lines_is_violation(tmp_path):
    block = _l2_block("L2-001", "paracetamol", related_chunks="[]")
    # inject a second related_chunks line manually
    block = block.replace(
        "related_chunks: []\n", "related_chunks: []\nrelated_chunks: [L2-999]\n"
    )
    output_dir, prefix, checkpoint = _setup(tmp_path, block, linked_chunks=1)
    violations = vtci._check_stage_5_4_persistence(output_dir, "11", prefix, checkpoint)
    assert any("duplicate related_chunks lines" in v for v in violations)


def test_missing_rag_optimised_entirely_is_violation(tmp_path):
    chunks = _l2_block("L2-001", "paracetamol", related_chunks="[]")
    output_dir, prefix, checkpoint = _setup(tmp_path, chunks, linked_chunks=1, write_rag=False)
    violations = vtci._check_stage_5_4_persistence(output_dir, "11", prefix, checkpoint)
    assert any("RAG_Optimised.md is missing entirely" in v for v in violations)


def test_stage_5_4_absent_is_not_a_violation_of_this_check(tmp_path):
    output_dir, prefix, _ = _setup(tmp_path, _CH11_STYLE_CHUNKS_NO_RELATED, status=None)
    checkpoint = {"stage_completions": {}}  # no "5.4" key at all
    violations = vtci._check_stage_5_4_persistence(output_dir, "11", prefix, checkpoint)
    assert violations == []


def test_stage_5_4_not_completed_is_not_a_violation_of_this_check(tmp_path):
    output_dir, prefix, _ = _setup(tmp_path, _CH11_STYLE_CHUNKS_NO_RELATED, status=None)
    checkpoint = {"stage_completions": {"5.4": {"status": "IN_PROGRESS"}}}
    violations = vtci._check_stage_5_4_persistence(output_dir, "11", prefix, checkpoint)
    assert violations == []
