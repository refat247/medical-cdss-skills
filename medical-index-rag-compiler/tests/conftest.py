"""Shared test helper: a stand-in for the RAG pipeline's classify_trust().

Unit tests build tiny fake chapters that do not carry the full evidence set (Stage 4.5d gate, 4.6/4.7
reviews, Stage 8 precision files) the real classifier requires, so by default tests use this stand-in:
a chapter is trusted iff its checkpoint has Stage 6 COMPLETED and Stage 8 trusted_for_downstream_use True.
tests/test_claude_audit_fixes.py::test_real_classifier_rejects_flag_only exercises the real classifier.
"""
import glob
import json
import os

import pytest


def fake_classifier(out_dir, chapter_name):
    cks = glob.glob(os.path.join(out_dir, "*_CHECKPOINT.json"))
    if not cks:
        return None
    try:
        st = json.load(open(cks[0], encoding="utf-8")).get("stage_completions", {})
    except ValueError:
        return {"trusted_for_downstream_use": False, "classification": "UNREADABLE"}
    s8 = st.get("8", {}) or {}
    ok = (st.get("6", {}) or {}).get("status") == "COMPLETED" and s8.get("trusted_for_downstream_use") is True
    return {"trusted_for_downstream_use": ok, "classification": "OK" if ok else "NOT_TRUSTED"}


@pytest.fixture(autouse=True)
def _stand_in_classifier(request, monkeypatch):
    if "real_classifier" in request.keywords:
        return
    import scripts.compiler as comp
    monkeypatch.setattr(comp, "TRUST_CLASSIFIER", fake_classifier)
