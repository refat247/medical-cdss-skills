"""Non-clinical trigger-collision regression tests salvaged from PR #1.

Clinical CDSS routing is intentionally excluded from this low-risk salvage because
changing which clinical engine receives a query can alter clinical behavior.
The public version-manager distribution is also excluded because canonical
version-manager authority is maintained in Private_repo.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def description(skill: str) -> str:
    text = (ROOT / skill / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert match is not None, f"{skill} is missing YAML frontmatter"
    frontmatter = match.group(1)
    assert "description:" in frontmatter, f"{skill} is missing a description"
    return " ".join(frontmatter.split("description:", 1)[1].split())


def test_antigravity_protocol_is_not_a_catch_all():
    d = description("antigravity-protocol")
    assert "ALWAYS" not in d
    assert "any software development task" not in d
    assert "only when efficiency is asked for" in d


def test_master_rag_orchestrator_defers_single_stage_work():
    d = description("medical-rag-orchestrator")
    assert "end-to-end multi-stage build" in d
    assert "medical-index-rag-compiler" in d
    assert "cdss-retrieval-packager" in d


def test_token_audit_and_harness_cleanup_defer_to_each_other():
    token = description("token-audit")
    harness = description("clean-my-ai-harness")
    assert "clean-my-ai-harness" in token
    assert "token-audit" in harness
