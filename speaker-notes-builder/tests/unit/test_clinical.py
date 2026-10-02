import json
from speaker_notes_builder.clinical import lint_scripts


def test_blocks_unqualified_local_approval(tmp_path):
    data = {"slides": [{
        "slide": 1,
        "included": True,
        "title": "Approval",
        "main_script": "This drug is approved in Bangladesh for obesity.",
        "compressed_script": "Approved in Bangladesh.",
        "optional_expansion": "",
        "delivery_intent": "",
        "estimated_seconds": 10,
        "claim_status": "UNVERIFIED"
    }]}
    (tmp_path / "scripts.json").write_text(json.dumps(data), encoding="utf-8")
    report = lint_scripts(tmp_path)
    assert report["status"] == "FAIL"
    assert report["blockers"]


def test_allows_qualified_jurisdiction_wording(tmp_path):
    data = {"slides": [{
        "slide": 1,
        "included": True,
        "title": "Approval",
        "main_script": "According to the product-label evidence used here, Bangladesh/DGDA status must be checked separately before calling this locally approved.",
        "compressed_script": "Verify the current local label before making an approval claim.",
        "optional_expansion": "",
        "delivery_intent": "",
        "estimated_seconds": 10,
        "claim_status": "JURISDICTION_SENSITIVE"
    }]}
    (tmp_path / "scripts.json").write_text(json.dumps(data), encoding="utf-8")
    report = lint_scripts(tmp_path)
    assert report["status"] in {"PASS", "PASS_WITH_WARNINGS"}


def test_clinical_profile_requires_claim_ledger_for_high_risk_script(tmp_path):
    manifest = {"profile": "clinical_cme", "slides": [{"slide": 1, "include": True}]}
    (tmp_path / "deck_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    data = {"slides": [{
        "slide": 1,
        "included": True,
        "title": "Dose",
        "main_script": "Start at 2.5 mg once weekly.",
        "compressed_script": "Start at 2.5 mg.",
        "optional_expansion": "",
        "delivery_intent": "",
        "estimated_seconds": 10,
        "claim_status": "SUPPORTED"
    }]}
    (tmp_path / "scripts.json").write_text(json.dumps(data), encoding="utf-8")
    report = lint_scripts(tmp_path)
    assert report["status"] == "FAIL"
    assert any("claim_ledger" in x for x in report["blockers"])
