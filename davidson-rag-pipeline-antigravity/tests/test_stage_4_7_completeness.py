"""SECOND_SWEEP 1.27 / B13: Stage 4.7 completeness scoring."""
from pipeline.stages.stage_4_7_serialize import evaluate_clinical_completeness


def _chunk(cid, disease, stype, topic, body):
    return (f"---\nchunk_id: {cid}\nchunk_level: 2\ndisease_focus: {disease}\nsemantic_type: {stype}\n"
            f"topic: {topic}\nreviewer_note: treatment and investigation pending\n---\n\n{body}\n\n")


def test_keywords_match_whole_words_only():
    from pipeline.stages.stage_4_7_serialize import _has_keyword
    assert not _has_keyword("it was because of rain", "cause")
    assert not _has_keyword("a significant design", "sign")
    assert _has_keyword("common causes include", "cause")
    assert _has_keyword("on examination", "examination")


def test_frontmatter_text_is_not_scored_as_clinical_content():
    # topic/semantic_type say nothing clinical; only the body does. Frontmatter keys such as 'source_lines'
    # must not be what drives categories.
    text = "".join(_chunk(f"L2-0{i}", "Asthma", "overview_note", "General", "Plain narrative text here.")
                    for i in range(3))
    res = evaluate_clinical_completeness(text)
    assert res["category_coverage"]["Asthma"] == []        # nothing clinical anywhere
    assert "Asthma" in res["scattered"] or "Asthma" in res["suspected_gap"]


def test_because_in_body_does_not_fake_pathophysiology():
    text = "".join(_chunk(f"L2-0{i}", "Gout", "overview_note", "General", "This is discussed because it matters.")
                    for i in range(3))
    assert "pathophysiology" not in evaluate_clinical_completeness(text)["category_coverage"]["Gout"]


def test_small_clusters_are_reported_as_low_evidence_not_silently_complete():
    text = _chunk("L2-01", "Rare syndrome", "clinical_feature", "Presentation", "Symptoms of the syndrome.")
    res = evaluate_clinical_completeness(text)
    assert "Rare syndrome" in res["complete_diseases"]        # verdict unchanged ...
    assert res["low_evidence"] == {"Rare syndrome": 1}        # ... but now visible
