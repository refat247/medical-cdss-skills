"""D-26: partial drug match must not return another drug's guardrail (skill_audits/SECOND_SWEEP.md 3.11)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from navigator import KumarNavigator  # noqa: E402


def _nav(tmp_path, keys):
    (tmp_path / "router.py").write_text("", encoding="utf-8")
    matrix = {k: {"general_indication": f"ind-{k}", "safety_precautions": f"safe-{k}"} for k in keys}
    (tmp_path / "kumar_clark_drug_disease_safety_matrix.json").write_text(
        json.dumps({"matrix": matrix}), encoding="utf-8")
    return KumarNavigator(str(tmp_path / "router.py"))


def test_substring_of_another_drug_is_not_a_match(tmp_path):
    out = _nav(tmp_path, ["acetazolamide", "sacubitril/valsartan"]).validate_therapy("ace")
    assert "not explicitly indexed" in out and "ind-acetazolamide" not in out


def test_whole_word_partial_match_is_labelled(tmp_path):
    out = _nav(tmp_path, ["sacubitril/valsartan", "warfarin"]).validate_therapy("Sacubitril")
    assert "SACUBITRIL/VALSARTAN" in out and "partial match" in out and "safe-warfarin" not in out


def test_ambiguous_partial_match_lists_candidates_without_a_guardrail(tmp_path):
    out = _nav(tmp_path, ["insulin glargine", "insulin lispro"]).validate_therapy("insulin")
    assert "several indexed entries" in out and "insulin glargine" in out and "safe-" not in out
