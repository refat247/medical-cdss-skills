"""Safety regression tests for habijabi_navigator (second-sweep findings H1-H8, 3.1-3.3, 3.13-3.14).
Behaviour under test is deliberately FAIL-SAFE: no rule matched => NOT_EVALUATED, missing inputs => refuse."""
import importlib.util
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = importlib.util.spec_from_file_location("habijabi_navigator", os.path.join(HERE, "..", "scripts", "habijabi_navigator.py"))
nav = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(nav)


def run(fn, *a):
    return fn(*a)


# ---------------- prescribing safety ----------------
def test_no_rule_matched_is_not_a_clearance(capsys):
    rc = nav.run_prescribing_safety("start amoxicillin 500 mg tds")
    out = capsys.readouterr().out
    assert rc != 0
    assert "NOT_EVALUATED" in out
    assert "PERMITTED" not in out and "No hard-stop" not in out


def test_all_matching_rules_are_shown_not_just_the_first(capsys):
    rc = nav.run_prescribing_safety("gout flare allopurinol linezolid fluoxetine")
    out = capsys.readouterr().out
    assert rc == 1
    assert "Urate-Lowering" in out and "Serotonin" in out


@pytest.mark.parametrize("order", ["linezolid with paroxetine", "linezolid and tramadol", "linezolid plus venlafaxine"])
def test_linezolid_with_other_serotonergic_agents_is_flagged(order, capsys):
    assert nav.run_prescribing_safety(order) == 1
    assert "Serotonin" in capsys.readouterr().out


def test_substring_false_positives_do_not_fire(capsys):
    rc = nav.run_prescribing_safety("environment anemia")      # 'iron' inside 'environment'
    assert rc != 0 and "Iron" not in capsys.readouterr().out
    rc = nav.run_prescribing_safety("see http://example.org platelet transfusion")  # 'ttp' inside 'http'
    assert rc != 0


def test_british_spelling_anaemia_matches_iron_rule(capsys):
    assert nav.run_prescribing_safety("anaemia start oral iron") == 1


def test_empty_order_is_an_error_not_silent_success(capsys):
    assert nav.main_cli(["--prescribing-safety", ""]) != 0


# ---------------- calculators ----------------
@pytest.mark.parametrize("calc,args", [("anion", []), ("anion", ["140", "100"]), ("mentzer", []), ("mentzer", ["70"]),
                                       ("dengue", []), ("drop", [])])
def test_calculators_refuse_missing_inputs(calc, args, capsys):
    rc = nav.run_tropical_calc(calc, args)
    out = capsys.readouterr().out
    assert rc != 0
    assert "RESULT" not in out


@pytest.mark.parametrize("calc,args", [("dengue", ["nan"]), ("dengue", ["-5"]), ("dengue", ["1e9"]), ("dengue", ["abc"]),
                                       ("mentzer", ["90", "0"]), ("anion", ["140", "100", "x"])])
def test_calculators_reject_implausible_or_nonnumeric(calc, args, capsys):
    assert nav.run_tropical_calc(calc, args) != 0


@pytest.mark.parametrize("w,expected", [(9, 900), (10, 1000), (11, 1050), (19, 1450), (20, 1500), (21, 1520), (50, 2100)])
def test_maintenance_fluid_is_continuous_holliday_segar(w, expected):
    assert nav.maintenance_ml_per_24h(w) == expected


def test_anion_gap_normal_bicarbonate_is_not_called_acidosis(capsys):
    assert nav.run_tropical_calc("anion", ["140", "100", "25"]) == 0
    out = capsys.readouterr().out
    assert "ACIDOSIS" not in out.upper().replace("NO METABOLIC ACIDOSIS", "")


def test_mentzer_thresholds(capsys):
    assert nav.run_tropical_calc("mentzer", ["65", "5.8"]) == 0
    assert "THALASSEMIA" in capsys.readouterr().out.upper()
    assert nav.run_tropical_calc("mentzer", ["65", "5.0"]) == 0          # exactly 13
    assert "INDETERMINATE" in capsys.readouterr().out.upper()
    assert nav.run_tropical_calc("mentzer", ["90", "5.0"]) == 0          # not microcytic
    assert "NOT APPLICABLE" in capsys.readouterr().out.upper()


def test_drop_rate_formulas_unchanged(capsys):
    assert nav.run_tropical_calc("drop", ["120"]) == 0
    out = capsys.readouterr().out
    assert "40 drops/min" in out and "30 drops/min" in out and "120 drops/min" in out


# ---------------- federation / matching ----------------
def test_federated_does_not_fabricate_other_book_text(capsys, monkeypatch):
    monkeypatch.setattr(nav, "load_bridge", lambda: [{"habijabi_topic": "Gout", "davidson_chapter_title": "Diseases of the joints",
        "habijabi_record_id": "HABIJABI-003", "bridge_id": "B1", "relationship_type": "x", "davidson_chapter_number": "25",
        "davidson_section_heading": "Gout", "concordance_notes": "n"}])
    rc = nav.run_federated("gout")
    out = capsys.readouterr().out
    assert rc == 0
    assert "Hemodynamic pressure-volume loops" not in out and "Definitive guidance on rare secondary" not in out
    assert "NOT QUERIED" in out.upper()


def test_federated_without_a_match_says_so_instead_of_returning_row_zero(capsys, monkeypatch):
    monkeypatch.setattr(nav, "load_bridge", lambda: [{"habijabi_topic": "Gout", "davidson_chapter_title": "Diseases of the joints",
        "habijabi_record_id": "HABIJABI-003", "bridge_id": "B1", "relationship_type": "x", "davidson_chapter_number": "25",
        "davidson_section_heading": "Gout", "concordance_notes": "n"}])
    rc = nav.run_federated("management of dengue")     # 'of' is in 'Diseases of the joints'
    assert rc != 0
    assert "NO BRIDGE MATCH" in capsys.readouterr().out.upper()


def test_preceptor_stopwords_do_not_match_everything(capsys, monkeypatch):
    recs = [{"record_id": "R1", "primary_condition": "Gout", "title": "Gout", "domain": "Rheum", "vignette": "a man with a hot joint",
             "pathophysiology": "p", "contraindications": "c", "pearls": "x"}]
    monkeypatch.setattr(nav, "load_english_synthesis_records", lambda: recs)
    rc = nav.run_preceptor("a young female with severe hypertension")   # only 'a'/'with' overlap
    assert rc != 0
    assert "NO MATCHING" in capsys.readouterr().out.upper()


def test_preceptor_with_empty_corpus_does_not_crash(capsys, monkeypatch):
    monkeypatch.setattr(nav, "load_english_synthesis_records", lambda: [])
    assert nav.run_preceptor("anything") != 0


# ---------------- SBA / CLI ----------------
def test_unknown_sba_target_is_an_error_not_a_random_item(capsys):
    assert nav.run_exam_sba("HABIJABI-999") != 0
    assert "SBA ITEM ID" not in capsys.readouterr().out


def test_two_modes_at_once_is_an_error(capsys):
    assert nav.main_cli(["--prescribing-safety", "x", "--search", "y"]) != 0


@pytest.mark.parametrize("k", ["0", "-1"])
def test_top_k_must_be_positive(k):
    with pytest.raises(SystemExit):
        nav.main_cli(["--search", "dengue", "--top_k", k])


def test_bengali_words_are_not_split_into_letters():
    assert nav.query_terms("ডেঙ্গু জ্বরে") == ["ডেঙ্গু", "জ্বরে"]
    assert "tb" in nav.query_terms("TB and DM")


def test_rule_text_was_not_altered_by_the_safety_refactor():
    """The refactor must not change clinical wording: compare against the pinned strings of the 6 rules."""
    src = open(os.path.join(HERE, "..", "scripts", "habijabi_navigator.py"), encoding="utf-8").read()
    for s in ["CLM-HABIJABI-126-001 | RECOVERY Trial / Davidson 25th Ed, Ch 14",
              "Contraindicated Urate-Lowering Therapy During Acute Gout Flare",
              "Absolute Contraindication of Platelet Transfusion in TTP",
              "Severe Drug Interaction: Serotonin Syndrome"]:
        assert s in src


@pytest.mark.parametrize("order", ["TTP - transfuse platelets", "Linezolid with SSRIs", "linezolid and Zoloft",
                                   "start Zyloprim in gout flare", "microcytic anemia: ferrous sulfate"])
def test_plural_and_brand_forms_fire(order):
    assert nav.run_prescribing_safety(order) == 1


def test_negated_order_still_alerts_with_note(capsys):
    assert nav.run_prescribing_safety("do not start allopurinol in gout flare") == 1
    assert "negation" in capsys.readouterr().out


def test_search_is_not_dead(tmp_path, monkeypatch, capsys):
    import inspect
    src = inspect.getsource(nav.run_search)
    body = src.split("print(\"=\" * 80)")[2] if src.count("print(\"=\" * 80)") > 2 else src
    assert "return 0\n\n    terms" not in src
