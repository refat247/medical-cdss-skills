"""Trigger-collision regression (skill_audits/SECOND_SWEEP.md 3.17): overlapping skills must name each other."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def description(skill):
    fm = re.match(r"---\n(.*?)\n---\n", (ROOT / skill / "SKILL.md").read_text(encoding="utf-8"), re.S).group(1)
    return " ".join(fm.split("description:", 1)[1].split())


def test_antigravity_protocol_is_not_a_catch_all():
    d = description("antigravity-protocol")
    assert "ALWAYS" not in d and "any software development task" not in d


def test_overlapping_skills_defer_to_each_other():
    pairs = {
        "kawsar-habijabi-cdss-navigator": ["medical-cdss-unified-orchestrator", "clinical-preceptor-cdss-orchestrator"],
        "clinical-preceptor-cdss-orchestrator": ["kawsar-habijabi-cdss-navigator"],
        "medical-cdss-unified-orchestrator": ["kumar-cdss-navigator"],
        "medical-rag-orchestrator": ["medical-index-rag-compiler", "cdss-retrieval-packager"],
        "token-audit": ["clean-my-ai-harness"],
        "clean-my-ai-harness": ["token-audit"],
        "version-manager": ["medical-rag-orchestrator"],
    }
    for skill, others in pairs.items():
        d = description(skill)
        for o in others:
            assert o in d, f"{skill} description must point at {o}"
