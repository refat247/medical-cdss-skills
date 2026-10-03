"""SECOND_SWEEP 1.30: Stage 3 must not block a short document for losing one tiny stray line."""
from pipeline.stages.stage_3_reaudit import compute_reaudit

BODY = ["Clinical sentence number %d about management of the condition in detail." % i for i in range(4)]


def test_losing_a_tiny_line_in_a_short_doc_still_passes():
    orig = "# Title\n\n" + "\n".join(BODY) + "\n\nOK.\n"
    rep = "# Title\n\n" + "\n".join(BODY) + "\n"
    assert compute_reaudit(orig, rep)["verdict"] == "PASSED"


def test_losing_real_content_in_a_short_doc_is_still_blocked():
    orig = "# Title\n\n" + "\n".join(BODY) + "\n"
    rep = "# Title\n\n" + "\n".join(BODY[:2]) + "\n"
    r = compute_reaudit(orig, rep)
    assert r["verdict"] != "PASSED" and r["preservation_percent"] < 95


def test_identical_text_is_100_percent():
    t = "# Title\n\n" + "\n".join(BODY) + "\n"
    assert compute_reaudit(t, t)["preservation_percent"] == 100.0
