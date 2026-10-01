"""Stage 6 (hard-fail validation gate) logic, extracted from SKILL.md's
inline block. Checks 6.1/6.2/6.4 are unchanged from the original; 6.4b is
new (Stage 4.5d wiring, correction C).

Correction C: Stage 6 must not rely only on
{PREFIX}_ClinicalFidelityFailures.json, because an unresolved-but-not-yet-
adjudicated candidate is not yet classified as a confirmed failure and
absence of a "failure" doesn't mean the chapter is clean — it might just
mean nobody has looked yet. Check 6.4b instead reads
{PREFIX}_ClinicalFidelityGate.json and requires verdict == PASS,
unresolved_candidates == 0, unresolved_corruptions == 0, every required
detector present in detectors_run, and detectors_not_tested empty.
"""
import re

from pipeline.stages.stage_4_5d_clinical_fidelity import REQUIRED_DETECTORS


_CHUNK_START_RE = re.compile(r'(?m)^---\nchunk_id:')

# v2.6.7 fix (REPOSITORY_PRODUCTION_READINESS_AUDIT.md Blocker 2): the
# original single regex
#   r'(---\nchunk_id:.*?\n---\n.*?)(?=\n---\nchunk_id:|\Z)'
# required the literal 5-byte sequence '\n---\n' (WITH a trailing newline)
# to close a chunk's own frontmatter. When RAG_Optimised.md has no trailing
# newline at end-of-file AND the last chunk is empty-body (frontmatter-only,
# e.g. a Tier-3 coverage_gap stub whose closing '---' is the file's final 3
# bytes), that exact sequence never occurs -- the block is silently dropped,
# not merged into a neighbor, not double-counted, just invisible to the
# parser. Confirmed live against Chapter 11 (105 vs real 106) and Chapter 15
# (86 vs real 87).
#
# Fix: split on chunk_id block *boundaries* first (frontmatter-agnostic --
# every chunk unconditionally starts with a line-anchored '^---\nchunk_id:'),
# then validate each individual chunk's own frontmatter closes, accepting
# EITHER '\n---\n' (mid-file, more content follows) OR '\n---' at the exact
# end of that chunk's slice (end-of-file, no trailing newline -- the
# empty-body-last-chunk case). This never depends on whether the file as a
# whole ends with a newline, and never merges two real chunks: boundaries are
# derived once, up front, from the unambiguous chunk_id line, not from the
# closing '---' (which is exactly what made the old regex newline-sensitive).
_FRONTMATTER_CLOSE_RE = re.compile(r'\A---\nchunk_id:.*?\n---(?:\n|\Z)', re.DOTALL)


def _split_blocks(rag_text):
    """Splits rag_text into one raw slice per chunk (frontmatter + body),
    robust to a missing trailing newline at end-of-file. Returns
    (blocks, malformed) where `blocks` is the list of well-formed chunk
    slices (in file order) and `malformed` is a list of human-readable
    error strings for any chunk whose frontmatter never closes (missing its
    own closing '---' line) -- these are never silently dropped or merged
    into a neighboring block; they are surfaced as an explicit, testable
    failure mode instead (see check_6_1_6_2's docstring)."""
    starts = [m.start() for m in _CHUNK_START_RE.finditer(rag_text)]
    blocks = []
    malformed = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(rag_text)
        raw = rag_text[start:end]
        if _FRONTMATTER_CLOSE_RE.match(raw) is None:
            cid_m = re.search(r'chunk_id:\s*(.+)', raw)
            cid = cid_m.group(1).strip() if cid_m else '?'
            malformed.append(f"{cid}: malformed chunk -- frontmatter never closes "
                              f"(no closing '---' line found before the next chunk "
                              f"or end of file)")
            continue
        blocks.append(raw)
    return blocks, malformed


def check_6_1_6_2(rag_text):
    """disease_focus / coverage_status presence+validity, and partial/gap
    chunks must carry a non-empty gap_note. Block-splitting hardened in
    v2.6.7 (see _split_blocks docstring) to fix a real blind spot on a
    file's final chunk when it is empty-body and the file has no trailing
    newline; the per-chunk 6.1/6.2 field checks below are otherwise
    unchanged from the original inline block. `chunks_checked` (the second
    return value) counts only well-formed blocks -- a chunk whose
    frontmatter never closes contributes its own explicit failure message
    (via `malformed`) but is not counted as a validly-inspected block,
    since check_6_1_6_2 was never actually able to inspect its 6.1/6.2
    fields."""
    blocks, malformed = _split_blocks(rag_text)
    failures = list(malformed)
    for b in blocks:
        cid = re.search(r'chunk_id:\s*(.+)', b)
        cid = cid.group(1).strip() if cid else '?'

        dfm = re.search(r'disease_focus:\s*(.*)', b)
        if not dfm or not dfm.group(1).strip():
            failures.append(f"{cid}: missing disease_focus")

        csm = re.search(r'coverage_status:\s*(.+)', b)
        status = csm.group(1).strip() if csm else None
        if status not in ('complete', 'partial', 'gap'):
            failures.append(f"{cid}: missing/invalid coverage_status ({status!r})")

        if status in ('partial', 'gap'):
            gnm = re.search(r'gap_note:\s*"(.*)"', b)
            if not gnm or not gnm.group(1).strip():
                failures.append(f"{cid}: coverage_status={status} but gap_note is empty")

    return failures, len(blocks)


def check_6_4(coverage_gaps_text_or_none):
    """Stage 4.5c must have run clean. Absence of the file is ALSO a
    failure, not a pass-by-default (unchanged rule)."""
    if coverage_gaps_text_or_none is None:
        return ["Stage 4.5c did not run — L1L2_CoverageGaps.md is missing"]
    if 'BLOCKING FAIL' in coverage_gaps_text_or_none:
        n_gaps = coverage_gaps_text_or_none.count('\n|') - 1
        return [f"Stage 4.5c reported {max(n_gaps, 1)} unresolved L1/L2 coverage gap(s) "
                f"— see L1L2_CoverageGaps.md"]
    return []


def check_6_4b(clinical_fidelity_gate_or_none):
    """New: Stage 4.5d must have run clean, per correction C. Reads the gate
    JSON's own verdict/counts rather than re-deriving them, so Stage 6 and
    Stage 4.5d can never silently disagree about what "clean" means."""
    if clinical_fidelity_gate_or_none is None:
        return ["Stage 4.5d did not run — ClinicalFidelityGate.json is missing"]

    gate = clinical_fidelity_gate_or_none
    failures = []
    if gate.get("verdict") != "PASS":
        failures.append(f"Stage 4.5d verdict is {gate.get('verdict')!r}, not PASS")
    if gate.get("unresolved_candidates", -1) != 0:
        failures.append(f"Stage 4.5d has {gate.get('unresolved_candidates')} unresolved "
                         f"(un-adjudicated) candidate(s)")
    if gate.get("unresolved_corruptions", -1) != 0:
        failures.append(f"Stage 4.5d has {gate.get('unresolved_corruptions')} unresolved "
                         f"confirmed corruption(s)")
    not_tested = gate.get("detectors_not_tested", REQUIRED_DETECTORS)
    if not_tested:
        failures.append(f"Stage 4.5d required detector(s) not tested: {not_tested}")
    return failures


def check_6_5_cdss_features(rag_text):
    """Check 6.5: CDSS Multi-Modal Figure & Algorithm Invariants.
    - If is_clinical_algorithm: true, algorithm_type must be present and valid.
    - If contains_figures: true, figure_assets or figure_captions must be non-empty.
    """
    blocks, malformed = _split_blocks(rag_text)
    failures = []
    valid_algo_types = {"decision_tree", "scoring_system", "stepwise_escalation"}
    for b in blocks:
        cid = re.search(r'chunk_id:\s*(.+)', b)
        cid = cid.group(1).strip() if cid else '?'

        algo_m = re.search(r'is_clinical_algorithm:\s*(.+)', b)
        if algo_m and algo_m.group(1).strip().lower() == "true":
            atype_m = re.search(r'algorithm_type:\s*(.+)', b)
            atype = atype_m.group(1).strip().lower() if atype_m else None
            if atype not in valid_algo_types:
                failures.append(f"{cid}: is_clinical_algorithm=true but algorithm_type ({atype!r}) is invalid")

        fig_m = re.search(r'contains_figures:\s*(.+)', b)
        if fig_m and fig_m.group(1).strip().lower() == "true":
            has_assets = bool(re.search(r'figure_assets:\s*\[.+\]', b))
            has_captions = bool(re.search(r'figure_captions:\s*\[.+\]', b))
            if not has_assets and not has_captions:
                failures.append(f"{cid}: contains_figures=true but no figure_assets or figure_captions list found")

    return failures


def check_6_6_provenance_and_breadcrumbs(rag_text):
    """Check 6.6: Provenance & Taxonomy Invariants (v2.16.0).
    Validates page_numbers and breadcrumb format when present.
    """
    blocks, malformed = _split_blocks(rag_text)
    failures = []
    for b in blocks:
        cid = re.search(r'chunk_id:\s*(.+)', b)
        cid = cid.group(1).strip() if cid else '?'

        pg_m = re.search(r'page_numbers:\s*(\[.*?\])', b)
        if pg_m:
            raw_pg = pg_m.group(1).strip()
            if raw_pg == "[]":
                failures.append(f"{cid}: page_numbers list is empty")
    return failures


def run_stage_6(rag_text, coverage_gaps_text_or_none, clinical_fidelity_gate_or_none):
    """Returns {failures, chunks_checked, verdict}. verdict is "PASS" only
    when every check below is clean — same aggregation pattern as the
    original inline block, extended with 6.4b, 6.5, and 6.6."""
    f1, n = check_6_1_6_2(rag_text)
    f2 = check_6_4(coverage_gaps_text_or_none)
    f3 = check_6_4b(clinical_fidelity_gate_or_none)
    f4 = check_6_5_cdss_features(rag_text)
    f5 = check_6_6_provenance_and_breadcrumbs(rag_text)
    failures = f1 + f2 + f3 + f4 + f5
    return {
        "failures": failures,
        "chunks_checked": n,
        "verdict": "PASS" if not failures else "HARD-FAIL",
    }


def decide_checkpoint_action(result):
    """CP-02: only PASS reaches mark_stage_complete; HARD-FAIL blocks (this
    was already correct in the original inline block for Stage 6 — kept as
    the reference pattern the other stages' fixes copy)."""
    metadata = {"chunks_checked": result["chunks_checked"], "hard_fails": len(result["failures"]),
                "verdict": result["verdict"]}
    if result["verdict"] == "PASS":
        return "complete", metadata
    metadata["failures"] = result["failures"]
    return "blocked", metadata
