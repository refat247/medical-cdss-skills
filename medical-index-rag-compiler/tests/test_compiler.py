"""Unit tests for compiler execution logic."""

import json
import os
import tempfile
import pytest
from scripts.compiler import CompilerConfig, MedicalBookIndexCompiler


def test_compiler_config_default_prefix():
    cfg = CompilerConfig(
        book_title="Davidson's Principles of Medicine",
        edition="25th",
        corpus_root="/dummy",
        index_markdown_path="/dummy/index.md",
        output_dir="/dummy/output"
    )
    assert cfg.asset_prefix == "davidson"
    assert cfg.eval_triplets_count == 768
    assert cfg.skip_eval is False


def test_compiler_phase_1_index_parsing():
    with tempfile.TemporaryDirectory() as temp_dir:
        idx_path = os.path.join(temp_dir, "index.md")
        out_dir = os.path.join(temp_dir, "output")
        corpus_dir = os.path.join(temp_dir, "corpus")
        os.makedirs(corpus_dir, exist_ok=True)

        # Mock index markdown
        index_content = (
            "# Index\n"
            "Accelerated idioventricular rhythm (AIVR)\n"
            "  in acute myocardial infarction, 1842\n"
            "  recurrent, 1845t\n"
            "COAPT (Cardiovascular Outcomes Assessment of MitraClip) trial, 1462\n"
            "Heart failure\n"
            "  acute decompensated\n"
            "  chronic management\n"
            "  hemodynamic classifications\n"
            "  vs. acute pulmonary embolism\n"
        )
        with open(idx_path, "w", encoding="utf-8") as f:
            f.write(index_content)

        # Mock chunk file
        chunk_path = os.path.join(corpus_dir, "SECTION_I_RAG_Optimised.md")
        chunk_content = (
            "# SECTION I\n"
            "---\n"
            "chunk_id: SECTION_I_L2-001\n"
            "topic_primary: Accelerated idioventricular rhythm\n"
            "semantic_type: concept_overview\n"
            "---\n"
            "AIVR is commonly seen after reperfusion in acute myocardial infarction.\n"
        )
        with open(chunk_path, "w", encoding="utf-8") as f:
            f.write(chunk_content)
        # Compiler is fail-closed: only chapters with a trusted Stage 8 checkpoint in the same folder are indexed
        with open(os.path.join(corpus_dir, "SECTION_I_CHECKPOINT.json"), "w", encoding="utf-8") as f:
            json.dump({"stage_completions": {"6": {"status": "COMPLETED"},
                                             "8": {"status": "COMPLETED", "trusted_for_downstream_use": True}}}, f)

        cfg = CompilerConfig(
            book_title="Test Cardiology Book",
            edition="1st",
            corpus_root=corpus_dir,
            index_markdown_path=idx_path,
            output_dir=out_dir,
            asset_prefix="test",
            skip_eval=True
        )
        compiler = MedicalBookIndexCompiler(cfg)
        manifest = compiler.run_all()

        assert manifest["total_index_terms"] >= 2
        assert manifest["total_chunks"] >= 1
        assert os.path.exists(os.path.join(out_dir, "cardiology_synonyms_and_acronyms.json"))
        assert os.path.exists(os.path.join(out_dir, "landmark_clinical_trials_registry.json"))
        assert os.path.exists(os.path.join(out_dir, "test_chunks_master_catalog.json"))
        assert os.path.exists(os.path.join(out_dir, "test_inverted_chunk_index.json"))
        assert os.path.exists(os.path.join(out_dir, "cdss_qa_router.py"))


def test_compiler_skips_blocked_chapters():
    with tempfile.TemporaryDirectory() as temp_dir:
        idx_path = os.path.join(temp_dir, "index.md")
        out_dir = os.path.join(temp_dir, "output")
        corpus_dir = os.path.join(temp_dir, "corpus")
        os.makedirs(corpus_dir, exist_ok=True)

        with open(idx_path, "w", encoding="utf-8") as f:
            f.write("# Index\nAspirin, 100\n")

        # Chapter 1: Valid
        ch1_dir = os.path.join(corpus_dir, "CH01")
        os.makedirs(ch1_dir, exist_ok=True)
        with open(os.path.join(ch1_dir, "CH01_RAG_Optimised.md"), "w", encoding="utf-8") as f:
            f.write("# CH01\n---\nchunk_id: CH01_01\ntopic: Aspirin\n---\nAspirin 75 mg daily.\n")
        with open(os.path.join(ch1_dir, "CH01_CHECKPOINT.json"), "w", encoding="utf-8") as f:
            json.dump({"stage_completions": {"6": {"status": "COMPLETED"},
                                             "8": {"status": "COMPLETED", "trusted_for_downstream_use": True}}}, f)

        # Chapter 2: Blocked by Stage 8
        ch2_dir = os.path.join(corpus_dir, "CH02")
        os.makedirs(ch2_dir, exist_ok=True)
        with open(os.path.join(ch2_dir, "CH02_RAG_Optimised.md"), "w", encoding="utf-8") as f:
            f.write("# CH02\n---\nchunk_id: CH02_01\ntopic: Blocked Topic\n---\nBlocked text.\n")
        ckpt_data = {
            "stage_completions": {
                "6": {"status": "COMPLETED"},
                "8": {"status": "BLOCKED", "error": "gate failed"}
            }
        }
        with open(os.path.join(ch2_dir, "CH02_CHECKPOINT.json"), "w", encoding="utf-8") as f:
            json.dump(ckpt_data, f)

        cfg = CompilerConfig(
            book_title="Test Cardiology Book",
            edition="1st",
            corpus_root=corpus_dir,
            index_markdown_path=idx_path,
            output_dir=out_dir,
            asset_prefix="test",
            skip_eval=True
        )
        compiler = MedicalBookIndexCompiler(cfg)
        manifest = compiler.run_all()

        # CH02 chunks should be excluded, only CH01 indexed
        with open(os.path.join(out_dir, "test_chunks_master_catalog.json"), "r", encoding="utf-8") as f:
            catalog = json.load(f)
        chunk_ids = [c["chunk_id"] for c in catalog]
        assert "CH01_01" in chunk_ids
        assert "CH02_01" not in chunk_ids

