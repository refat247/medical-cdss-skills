"""
Stage 4.6 module for davidson-rag-pipeline-cc (v2.1.0).

v2.1.0 makes Sonnet verification MANDATORY, not opt-in, and expands its scope
from "pathophysiology-tagged chunks only" to all chunks. A full manual re-read
of a real chapter (196 L1 + 174 L2 chunks) found a 15-17% misclassification
rate spread across every semantic type -- the old pathophysiology-only scope
structurally could not catch most of it, since clinical_feature (the default
bucket) was the WRONG answer in most cases, not the thing being corrected.
See CHANGELOG [2.1.0] for the full findings.

Two execution paths are supported, auto-selected by whether the `anthropic`
package + API key are available:
  1. API path: calls the Anthropic API directly (stage_4_with_verification).
  2. Manual path: Claude Code sessions commonly run with no anthropic package
     and no API key configured (observed directly in production use of this
     skill). In that case the calling agent IS Sonnet, so verification is done
     by the agent itself reading an exported batch file and returning
     corrections -- see export_for_manual_review() / apply_manual_corrections()
     below, which formalise the exact workflow used to find the v2.1.0 fixes.

Operates on chunks.md/REPAIRED_S2.md as raw text, matching how every other
stage in this skill works (no chunk-object model, no persistent state between
stages).
"""

import os
import re
import json
import logging
from collections import Counter

log = logging.getLogger("stage_4_6")

# Must match the semantic_type taxonomy already used in SKILL.md Stage 4.6 / 4.5b / 5.
SEMANTIC_TYPES = [
    "pathophysiology",
    "drug_info",
    "diagnostic_criteria",
    "clinical_feature",
    "management_step",
    "laboratory_investigation",
    "epidemiology_concept",
]

# TITLE_RULES fire on the chunk's `topic:` frontmatter field and take priority
# over BODY_RULES -- a section header is a much stronger signal than keyword
# hits in the body, and this is where the biggest v2.1.0 findings clustered
# (e.g. "Adverse effects of X" boxes were landing in management_step because
# they sat under a "management" parent section, despite the title itself
# unambiguously saying drug safety content).
TITLE_RULES = [
    ("drug_info",                [r'^Adverse effects of', r'adverse effects of \w+',
                                   r'^Drugs?/toxins$']),
    ("laboratory_investigation", [r'^Investigations?$', r'^Plain X-rays?$',
                                   r'^Ultrasonograph', r'^Computed tomography$',
                                   r'^Magnetic resonance imaging$',
                                   r'^Radionuclide bone scintigraphy$',
                                   r'^Dual X-ray absorptiometry$',
                                   r'^Electromyography$', r'^Tissue biopsy$']),
    ("management_step",          [r'^Management$', r'^Surgery$', r'^Prophylaxis$',
                                   r'^Non-pharmacological (?:therapy|interventions)$',
                                   r'^Pharmacological (?:therapy|treatment|interventions)$']),
]

# BODY_RULES fire on chunk body text, used both as the regex fallback (when no
# TITLE_RULES match) and to build the Sonnet verification prompt's type
# descriptions. Expanded in v2.1.0 with patterns for the two other systematic
# gaps found: pure anatomy/physiology description defaulting to clinical_feature
# instead of pathophysiology, and pure epidemiology-statistic disease-intro
# paragraphs defaulting to clinical_feature instead of epidemiology_concept.
BODY_RULES = [
    # Ordered by signal strength, not alphabetically -- earlier rules win ties.
    # "diagnostic_criteria" is deliberately near the END: 'Box \d+\.' and
    # 'classif' are weak signals that used to steal matches from every other
    # rule (almost any paragraph parenthetically references a box number
    # regardless of its actual topic) -- see CHANGELOG [2.1.0] smoke test,
    # which measured this ordering bug directly before the fix.
    ("drug_info",                [r'\b\d+\s*(?:mg|mcg|g|mL)\b', r'\bdosing\b',
                                   r'\bregimen\b', r'\bpharmacokinetic', r'\bhalf-life\b',
                                   r'\bantibiot', r'\bantiviral', r'\bbioavailability\b',
                                   r'\bside effects?\b', r'\badverse effects?\b']),
    ("laboratory_investigation", [r'\bsensitivity\b', r'\bspecificity\b', r'\blikelihood ratio\b',
                                   r'\bpre-test\b', r'\bpost-test\b']),
    ("pathophysiology",          [r'\bconsists? of\b', r'\bis composed of\b', r'\bcomprises?\b',
                                   r'\bembryonic\b', r'\bossification\b', r'\bcell types?\b',
                                   r'\bmesenchymal\b', r'\bmyocytes?\b', r'\bchondrocytes?\b']),
    ("management_step",          [r'\btreatment\b', r'\bmanage(?:d|ment)?\b', r'\btherapy\b',
                                   r'\bfirst-line\b', r'\bprophylaxis\b', r'\bprescri']),
    ("epidemiology_concept",     [r'\bprevalence\b', r'\bincidence\b', r'\bmortality\b',
                                   r'\brisk factor\b']),
    ("diagnostic_criteria",      [r'\bdiagnostic criteria\b', r'\bclassification criteria\b',
                                   r'\bstaging\b', r'\bdefined as\b']),
    ("clinical_feature",         [r'\bsymptom\b', r'\bsign\b', r'\bpresent']),
]

# Backward-compat alias -- older callers/tests may still import RULES.
RULES = BODY_RULES

# Strong-signal epidemiology detector: fires when a chunk is DOMINATED by
# statistics with no clinical-presentation language, distinguishing pure
# epidemiology intros (Ch25: "Septic arthritis... incidence is 2-10 per
# 100 000... mortality of about 10%...") from hybrid disease-overview chunks
# that blend demographics with actual presentation description (which should
# stay clinical_feature -- e.g. "Presentation is with fever, myalgia...").
_EPI_STAT_RE = re.compile(
    r'\b\d+(?:\.\d+)?\s*(?:%|per\s*(?:1000|10\s*000|100\s*000|million))\b|\bprevalence\b|\bincidence\b',
    re.I,
)
_CLINICAL_CUE_RE = re.compile(
    r'\bpresent(?:s|ation|ing)?\b|\bsymptoms?\b|\bsigns?\b|\bexamination\b|\bpain\b|\btender',
    re.I,
)


def _is_pure_epidemiology(body):
    stat_hits = len(_EPI_STAT_RE.findall(body))
    return stat_hits >= 2 and not _CLINICAL_CUE_RE.search(body)


# Non-clinical back-matter that should never receive a clinical semantic_type.
# Found chunked and force-tagged in Ch25 at both L1 and L2 (Journal articles /
# Websites / Patient organisations, and the wrapping "Further information"
# section) -- none of the 7 taxonomy types fit reference/bibliography content.
# Stage 4B's subagent prompt (SKILL.md) now excludes these from chunk
# emission entirely; this list is kept here as a defensive filter so the
# verifier skips them cleanly if the subagent didn't obey the instruction.
BACKMATTER_TOPIC_RE = re.compile(
    r'^(?:Further information|Journal articles|Websites|Patient organisations)$', re.I
)

# Two chunk-file formats exist in the wild:
#   legacy: "### Chunk L2-001\n---\nchunk_id: ...\n---\nBODY"
#   actual: "---\nchunk_id: L2-001\n...\n---\nBODY"  (no "### Chunk" header line —
#           this is what davidson-rag-pipeline-cc's Stage 4 subagent actually
#           produces via verbatim line-slicing; see CHANGELOG [2.0.1]).
CHUNK_SPLIT_RE_LEGACY = re.compile(r'(?=^### Chunk )', re.MULTILINE)
CHUNK_SPLIT_RE_BARE   = re.compile(r'(?=^---\s*\nchunk_id:)', re.MULTILINE)

# Matches either format's frontmatter/body boundary in one shot, so callers
# never need to hand-count "\n---\n" occurrences (which silently breaks on
# the bare format — it only has ONE such delimiter per chunk, not two).
_CHUNK_BODY_RE = re.compile(r'^(?:### Chunk[^\n]*\n)?---\n.*?\n---\n?(.*)$', re.DOTALL)


def stage_4_with_verification(chunks_data, repaired_s2_text, levels=(2,),
                               min_budget_to_run=4000, max_output_tokens=12000):
    """
    v2.1.0 default entry point. Stage 4a (regex baseline, now applied to ALL
    chunks in `levels`, not just pathophysiology-tagged ones) + Stage 4b
    (Sonnet verification, now MANDATORY rather than an opt-in flag).

    levels: which chunk_level(s) to verify. Defaults to (2,) since
    RAG_Optimised.md only ever emits L2 chunks (Stage 5) -- L1 corrections
    don't reach the final retrieval file, so verifying L1 too roughly doubles
    cost for output that's intermediate/advisory only. Pass (1, 2) for a full
    audit like the one that found the v2.1.0 patterns in the first place.

    Returns (new_chunks_text, metadata). Tries the Anthropic API first; if the
    `anthropic` package or a working API key isn't available (common in
    Claude Code sessions with no API credentials configured -- this is the
    normal case, not an error path), falls back to the regex baseline alone
    and flags `needs_manual_verification: True` in the metadata so the
    calling agent knows to run the manual protocol (see
    export_for_manual_review() / apply_manual_corrections() below) instead of
    silently shipping regex-only output as if it were verified.

    The regex baseline here only auto-applies TITLE_RULES (measured to cause
    zero regressions -- see _regex_remap_all docstring); it does NOT apply
    BODY_RULES broadly, since that was measured to introduce MORE new errors
    than it fixed. metadata['review_priority'] lists chunks worth checking
    first when the manual protocol runs, but is advisory only -- the manual
    reviewer must still judge each chunk from its own content, not trust the
    candidate type at face value.
    """
    chunks_text, changed, review_priority = _regex_remap_all(chunks_data, levels=levels)

    if min_budget_to_run < 4000:
        metadata = _build_metadata(
            chunks_text, sonnet_used=False, sonnet_failed_fallback=False,
            sonnet_failure_reason="min_budget_to_run below floor", corrected=changed,
            unparsed_ids=[], tokens_used=0,
        )
        metadata["needs_manual_verification"] = True
        metadata["review_priority"] = review_priority
        return chunks_text, metadata

    try:
        new_text, metadata = _stage_4_6_sonnet_verification_all(
            chunks_text, repaired_s2_text, levels, max_output_tokens
        )
        metadata["review_priority"] = []
        return new_text, metadata
    except Exception as e:
        log.warning(f"Sonnet API verification unavailable ({e}); "
                    f"regex baseline applied. Run the manual verification protocol "
                    f"(export_for_manual_review / apply_manual_corrections) before "
                    f"treating this chapter's semantic_type tags as final.")
        metadata = _build_metadata(
            chunks_text, sonnet_used=False, sonnet_failed_fallback=True,
            sonnet_failure_reason=str(e), corrected=changed,
            unparsed_ids=[], tokens_used=0,
        )
        metadata["needs_manual_verification"] = True
        metadata["review_priority"] = review_priority
        return chunks_text, metadata


def stage_4_6_semantic_remap(
    chunks_data,
    repaired_s2_text,
    verify_with_sonnet=True,
    min_budget_to_run=4000,
    max_output_tokens=8000,
    fallback_on_sonnet_fail=True,
):
    """
    Deprecated as of v2.1.0 -- kept for backward compatibility with existing
    callers. `verify_with_sonnet` now defaults to True (verification is
    mandatory in the new design; see stage_4_with_verification, which is the
    preferred entry point going forward). This wrapper still only scopes to
    pathophysiology-tagged L2 chunks, matching its original v2.0.0 contract --
    switch callers to stage_4_with_verification() to get the full-scope,
    all-types verification that v2.1.0 actually recommends.
    """
    if verify_with_sonnet and min_budget_to_run >= 4000:
        try:
            return _stage_4_6_sonnet_verification(
                chunks_data, repaired_s2_text, max_output_tokens
            )
        except Exception as e:
            if fallback_on_sonnet_fail:
                log.warning(f"Sonnet verification failed: {e}, falling back to regex")
                new_text, changed = _regex_remap(chunks_data)
                metadata = _build_metadata(
                    new_text, sonnet_used=False, sonnet_failed_fallback=True,
                    sonnet_failure_reason=str(e), corrected=changed,
                    unparsed_ids=[], tokens_used=0,
                )
                return new_text, metadata
            else:
                raise
    else:
        new_text, changed = _regex_remap(chunks_data)
        metadata = _build_metadata(
            new_text, sonnet_used=False, sonnet_failed_fallback=False,
            sonnet_failure_reason=None, corrected=changed,
            unparsed_ids=[], tokens_used=0,
        )
        return new_text, metadata


def _split_chunks(text):
    """
    Auto-detects which chunk-file format `text` uses and splits accordingly.
    Tries the legacy "### Chunk " header format first; if that finds nothing
    (as it always will against davidson-rag-pipeline-cc's actual chunks.md —
    see CHANGELOG [2.0.1]), falls back to the bare "---\\nchunk_id:" format.
    """
    parts = CHUNK_SPLIT_RE_LEGACY.split(text)
    c_parts = [p for p in parts if p.startswith('### Chunk')]
    if c_parts:
        preamble = parts[0] if not parts[0].startswith('### Chunk') else ''
        return preamble, c_parts

    parts = CHUNK_SPLIT_RE_BARE.split(text)
    c_parts = [p for p in parts if p.startswith('---')]
    preamble = parts[0] if not parts[0].startswith('---') else ''
    return preamble, c_parts


def _get_body(part):
    """Frontmatter-stripped body text for a chunk part, format-agnostic."""
    m = _CHUNK_BODY_RE.match(part)
    return m.group(1) if m else part


def _get_topic(part):
    m = re.search(r'^topic:\s*"?(.+?)"?\s*$', part, re.MULTILINE)
    return m.group(1) if m else ''


def _get_chunk_level(part):
    m = re.search(r'^chunk_level:\s*(\d+)', part, re.MULTILINE)
    return int(m.group(1)) if m else None


def _get_semantic_type(part):
    m = re.search(r'^semantic_type:\s*(\S+)', part, re.MULTILINE)
    return m.group(1) if m else None


def _is_backmatter(part):
    return bool(BACKMATTER_TOPIC_RE.match(_get_topic(part).strip()))


CHUNK_LEVEL_2_RE = re.compile(r'^chunk_level:\s*2\b', re.MULTILINE)


def _is_pathophysiology_l2(part):
    # Matches "chunk_level: 2" or "chunk_level: 2 (micro)" — actual chunker
    # output uses the bare integer, the original base-skill guard required
    # the "(micro)" suffix literally and never matched real chunks.md files.
    return bool(CHUNK_LEVEL_2_RE.search(part)) and 'semantic_type: pathophysiology' in part


def _classify_by_rules(topic, body):
    """
    Used by the manual-review protocol and the legacy pathophysiology-only
    path as a full-strength classifier (title first, then epidemiology
    detector, then body keywords). NOT used by _regex_remap_all for
    auto-relabeling — see that function's docstring for why: a direct
    measurement against 58 known-correct corrections in a real chapter found
    BODY_RULES (even scoped to chunks currently tagged clinical_feature)
    introduced 76 NEW wrong labels on chunks that were already correct, and
    even the narrower epidemiology-only detector introduced 4. Body-text
    regex is not reliable enough to auto-apply; only a human/Sonnet judgment
    call safely resolves it, which is exactly why verification is mandatory
    rather than "run better regex." See CHANGELOG [2.1.0].
    """
    for new_type, pats in TITLE_RULES:
        if any(re.search(p, topic, re.I) for p in pats):
            return new_type
    if _is_pure_epidemiology(body):
        return "epidemiology_concept"
    for new_type, pats in BODY_RULES:
        if any(re.search(p, body, re.I) for p in pats):
            return new_type
    return None


def _flag_review_priority(topic, body, current_type):
    """
    Advisory only — never auto-applied. Returns a candidate semantic_type if
    BODY_RULES/the epidemiology detector disagree with the chunk's current
    tag, purely to help a verifier (Sonnet API prompt or manual reviewer)
    triage which chunks most likely need a closer look first. Measured
    directly to introduce false positives if treated as ground truth (see
    _classify_by_rules docstring) — treat this as "worth a second look," not
    "known wrong."
    """
    if _is_pure_epidemiology(body) and current_type != "epidemiology_concept":
        return "epidemiology_concept"
    for new_type, pats in BODY_RULES:
        if new_type != current_type and any(re.search(p, body, re.I) for p in pats):
            return new_type
    return None


def _regex_remap_all(chunks_data, levels=(2,)):
    """
    v2.1.0 Stage 4a: applies ONLY `TITLE_RULES` for auto-relabeling — measured
    directly against a real chapter's 58 known corrections to produce ZERO
    regressions on the 312 already-correct chunks (title/topic matches like
    "Adverse effects of X" or an exact "Investigations" header are strong,
    unambiguous signals). `BODY_RULES` and the epidemiology detector are
    advisory-only (see _flag_review_priority) — they are surfaced in the
    returned metadata's `review_priority` list to help prioritize what the
    mandatory verification step should look at closely, but never silently
    change a tag, because body-text regex measurably introduces new wrong
    labels when auto-applied (see _classify_by_rules docstring and
    CHANGELOG [2.1.0]).

    Back-matter chunks (bibliography/websites/patient orgs) are skipped
    entirely; no type in the taxonomy fits them and forcing one just
    relabels the same problem under a different name.
    """
    preamble, c_parts = _split_chunks(chunks_data)
    changed, review_priority, out_parts = 0, [], [preamble]
    for part in c_parts:
        level = _get_chunk_level(part)
        if level not in levels or _is_backmatter(part):
            out_parts.append(part)
            continue
        current = _get_semantic_type(part)
        topic = _get_topic(part)
        body = _get_body(part)

        title_type = next(
            (nt for nt, pats in TITLE_RULES if any(re.search(p, topic, re.I) for p in pats)),
            None,
        )
        if title_type and title_type != current:
            out_parts.append(part.replace(f'semantic_type: {current}',
                                           f'semantic_type: {title_type}', 1))
            changed += 1
            continue

        out_parts.append(part)
        candidate = _flag_review_priority(topic, body, current)
        if candidate:
            cid_m = re.search(r'chunk_id:\s*(\S+)', part)
            review_priority.append({
                "chunk_id": cid_m.group(1) if cid_m else '?',
                "current_type": current,
                "candidate_type": candidate,
            })
    return ''.join(out_parts), changed, review_priority


def _regex_remap(chunks_data):
    """Legacy v2.0.0 behaviour: only remaps pathophysiology-tagged L2 chunks.
    Kept for stage_4_6_semantic_remap() backward compatibility."""
    preamble, c_parts = _split_chunks(chunks_data)
    changed, out_parts = 0, [preamble]
    for part in c_parts:
        if not _is_pathophysiology_l2(part):
            out_parts.append(part); continue
        body = _get_body(part)
        new_type = next(
            (nt for nt, pats in BODY_RULES if any(re.search(p, body, re.I) for p in pats)), None
        )
        out_parts.append(part.replace('semantic_type: pathophysiology',
                                       f'semantic_type: {new_type}') if new_type else part)
        if new_type: changed += 1
    return ''.join(out_parts), changed


def _get_source_lines(part):
    """v2.6.5 (CATEGORY D emergency fix): delegates to the canonical
    stages.source_lines_parser module. The previous inline regex here
    matched only a single hyphenated range and returned None (falling
    back to the chunk's own body in _get_context_window, losing all real
    source context) for anything else — a single-line value, a
    comma-separated combination, or extra whitespace around the dash all
    silently degraded to the no-context fallback. Returns the overall
    (min_start, max_end) envelope across every parsed segment; see
    V2_6_5_EMERGENCY_INTEGRITY_FIX_REPORT.md. Do not reintroduce inline
    range-parsing regex here (see
    tests/test_no_duplicate_source_lines_parser.py)."""
    from pipeline.stages.source_lines_parser import parse_source_lines_from_block
    segments = parse_source_lines_from_block(part).segments
    if not segments:
        return None
    return (min(s[0] for s in segments), max(s[1] for s in segments))


def _get_context_window(repaired_s2_text, part, window_lines=15):
    """
    Source text surrounding the chunk's origin, from source_lines frontmatter
    (Stage 4 already writes this — no source_offset tracking needed).
    Falls back to the chunk's own body if source_lines is missing/malformed.
    """
    span = _get_source_lines(part)
    if span is None:
        return part
    start_line, end_line = span
    lines = repaired_s2_text.splitlines()
    lo = max(0, start_line - 1 - window_lines)
    hi = min(len(lines), end_line + window_lines)
    return '\n'.join(lines[lo:hi])


_TYPE_DESCRIPTIONS = """- pathophysiology: how something works or develops at cellular/tissue level (includes
  functional anatomy/physiology description -- structural composition, embryology, cell types)
- drug_info: drug effects, side effects, interactions, dosing, adverse-effects boxes
- diagnostic_criteria: formal diagnostic criteria or classification/staging rules
- clinical_feature: symptoms, signs, presentations, differential-diagnosis lists
- management_step: treatment, management, intervention, procedures, lifestyle advice
- laboratory_investigation: lab tests, imaging modalities, investigation panels/procedures
- epidemiology_concept: incidence, prevalence, mortality, risk-factor statistics (only when
  the chunk is DOMINATED by statistics, not when it blends demographics with an actual
  clinical presentation description -- the latter stays clinical_feature)"""


def _build_verification_prompt(chunks_for_review):
    return f"""You are reviewing semantic type assignments for medical text chunks
from a Davidson's Principles and Practice of Medicine chapter, some or all of
which may be mistagged by a regex-only first pass.

For each chunk, determine what it is primarily about, independent of any
neighboring chunk or parent section context -- classify strictly on the
chunk's own content:
{_TYPE_DESCRIPTIONS}

Use local_source_context only to disambiguate the chunk's OWN meaning (e.g. a
chunk mentioning a drug name is not automatically drug_info if it's really
explaining a mechanism, and should stay pathophysiology if that's genuinely
the primary subject). Do not let the context's topic bleed into the chunk's
classification if the chunk itself is about something else -- this is the
single most common regex failure mode (sibling type-bleed): a chunk sitting
near an "Investigations" chunk is not automatically laboratory_investigation
if its own content is a disease description.

Chunks to verify:
{chunks_for_review}

Output a JSON array, one object per chunk, in this exact form:
[
  {{"chunk_id": "L2-001", "semantic_type": "drug_info", "confidence": 0.95, "reason": "..."}},
  ...
]

Output ONLY the JSON array, no other text."""


def _parse_sonnet_verification(response_text, expected_ids):
    corrections = {}
    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", response_text, re.DOTALL)
        try:
            parsed = json.loads(match.group(0)) if match else []
        except json.JSONDecodeError:
            parsed = []

    if isinstance(parsed, dict):
        # dict-shaped replies: {"corrections": [...]} / {"results": [...]} / a single {"chunk_id":..} item
        lists = [v for v in parsed.values() if isinstance(v, list)]
        parsed = lists[0] if lists else ([parsed] if "chunk_id" in parsed else [])
    if not isinstance(parsed, list):
        parsed = []

    seen_ids = set()
    for item in parsed:
        if not isinstance(item, dict):
            continue
        cid = item.get("chunk_id")
        stype = item.get("semantic_type")
        if cid and stype in SEMANTIC_TYPES:
            corrections[cid] = stype
            seen_ids.add(cid)

    unparsed_ids = [cid for cid in expected_ids if cid not in seen_ids]
    return corrections, unparsed_ids


VERIFIER_MODEL = os.environ.get("CDSS_VERIFIER_MODEL", "claude-sonnet-5")   # override if this id is not available to your key
VERIFIER_BATCH_SIZE = 25


def _run_verifier_batches(client, reviews, ids, max_output_tokens, batch_size=None):
    """One request per `batch_size` chunks (a whole chapter in one request overruns output limits). A reply
    cut off by max_tokens is not trusted: that batch's ids are returned as unparsed so existing tags are kept.
    Returns (corrections, unparsed_ids, tokens_used, truncated_batches)."""
    batch_size = batch_size or VERIFIER_BATCH_SIZE
    corrections, unparsed, tokens, truncated = {}, [], 0, 0
    for i in range(0, len(reviews), batch_size):
        b_reviews, b_ids = reviews[i:i + batch_size], ids[i:i + batch_size]
        response = client.messages.create(
            model=VERIFIER_MODEL,
            max_tokens=max_output_tokens,
            messages=[{"role": "user", "content": _build_verification_prompt("\n".join(b_reviews))}],
        )
        tokens += response.usage.input_tokens + response.usage.output_tokens
        if getattr(response, "stop_reason", None) == "max_tokens":
            truncated += 1
            unparsed.extend(b_ids)
            continue
        text = response.content[0].text if response.content else "[]"
        c, u = _parse_sonnet_verification(text, b_ids)
        corrections.update(c)
        unparsed.extend(u)
    return corrections, unparsed, tokens, truncated


def _stage_4_6_sonnet_verification_all(chunks_data, repaired_s2_text, levels, max_output_tokens):
    """
    v2.1.0: reviews ALL chunks in `levels` (not just pathophysiology-tagged
    ones). Raises on API failure — caller (stage_4_with_verification) handles
    fallback to the regex baseline + manual-verification flag.
    """
    from anthropic import Anthropic

    preamble, c_parts = _split_chunks(chunks_data)
    targets = [p for p in c_parts
               if _get_chunk_level(p) in levels and not _is_backmatter(p)]

    if not targets:
        return chunks_data, _build_metadata(
            chunks_data, sonnet_used=True, sonnet_failed_fallback=False,
            sonnet_failure_reason=None, corrected=0, unparsed_ids=[], tokens_used=0,
        )

    reviews, ids = [], []
    for part in targets:
        cid_m = re.search(r'chunk_id:\s*(\S+)', part)
        cid = cid_m.group(1) if cid_m else '?'
        ids.append(cid)
        current_type = _get_semantic_type(part) or 'unknown'
        body = _get_body(part).strip()
        context = _get_context_window(repaired_s2_text, part)
        reviews.append(
            f"chunk_id: {cid}\ncurrent_semantic_type: {current_type}\n"
            f"content: {body}\nlocal_source_context: {context}\n---"
        )

    client = Anthropic()
    corrections, unparsed_ids, tokens_used, truncated = _run_verifier_batches(client, reviews, ids, max_output_tokens)

    changed = 0
    out_parts = [preamble]
    for part in c_parts:
        if _get_chunk_level(part) not in levels or _is_backmatter(part):
            out_parts.append(part); continue
        cid_m = re.search(r'chunk_id:\s*(\S+)', part)
        cid = cid_m.group(1) if cid_m else '?'
        current_type = _get_semantic_type(part)
        new_type = corrections.get(cid)
        if new_type and new_type != current_type:
            out_parts.append(part.replace(f'semantic_type: {current_type}',
                                           f'semantic_type: {new_type}', 1))
            changed += 1
        else:
            out_parts.append(part)

    if unparsed_ids:
        log.warning(f"{len(unparsed_ids)} chunks unparsed, kept existing tags: {unparsed_ids}")

    new_text = ''.join(out_parts)
    metadata = _build_metadata(
        new_text, sonnet_used=True, sonnet_failed_fallback=False,
        sonnet_failure_reason=None, corrected=changed, unparsed_ids=unparsed_ids,
        tokens_used=tokens_used, chunks_reviewed=len(targets),
    )
    metadata["needs_manual_verification"] = truncated > 0    # a truncated reply is never silently accepted
    if truncated:
        metadata["truncated_batches"] = truncated
    return new_text, metadata


def _stage_4_6_sonnet_verification(chunks_data, repaired_s2_text, max_output_tokens):
    """Legacy v2.0.0 scope (pathophysiology-tagged L2 only). Kept for
    stage_4_6_semantic_remap() backward compatibility -- prefer
    stage_4_with_verification() / _stage_4_6_sonnet_verification_all()."""
    from anthropic import Anthropic

    preamble, c_parts = _split_chunks(chunks_data)
    targets = [p for p in c_parts if _is_pathophysiology_l2(p)]

    if not targets:
        return chunks_data, _build_metadata(
            chunks_data, sonnet_used=True, sonnet_failed_fallback=False,
            sonnet_failure_reason=None, corrected=0, unparsed_ids=[], tokens_used=0,
        )

    reviews = []
    ids = []
    for part in targets:
        cid_m = re.search(r'chunk_id:\s*(\S+)', part)
        cid = cid_m.group(1) if cid_m else '?'
        ids.append(cid)
        body = _get_body(part).strip()
        context = _get_context_window(repaired_s2_text, part)
        reviews.append(
            f"chunk_id: {cid}\ncurrent_semantic_type: pathophysiology\n"
            f"content: {body}\nlocal_source_context: {context}\n---"
        )

    client = Anthropic()
    corrections, unparsed_ids, tokens_used, _truncated = _run_verifier_batches(client, reviews, ids, max_output_tokens)

    changed = 0
    out_parts = [preamble]
    for part in c_parts:
        if not _is_pathophysiology_l2(part):
            out_parts.append(part); continue
        cid_m = re.search(r'chunk_id:\s*(\S+)', part)
        cid = cid_m.group(1) if cid_m else '?'
        new_type = corrections.get(cid)
        if new_type and new_type != "pathophysiology":
            out_parts.append(part.replace('semantic_type: pathophysiology',
                                           f'semantic_type: {new_type}'))
            changed += 1
        else:
            out_parts.append(part)

    if unparsed_ids:
        log.warning(f"{len(unparsed_ids)} chunks unparsed, kept pathophysiology: {unparsed_ids}")

    new_text = ''.join(out_parts)
    metadata = _build_metadata(
        new_text, sonnet_used=True, sonnet_failed_fallback=False,
        sonnet_failure_reason=None, corrected=changed, unparsed_ids=unparsed_ids,
        tokens_used=tokens_used, chunks_reviewed=len(targets),
    )
    return new_text, metadata


def export_for_manual_review(chunks_data, levels=(2,), batch_size=25, body_chars=450,
                              review_priority=None):
    """
    Manual verification protocol, step 1. Use when the `anthropic` package or
    API key isn't available (the common case in Claude Code sessions) --
    stage_4_with_verification() already detects this and falls back to regex
    + `needs_manual_verification: True`, but doesn't perform the manual pass
    itself since it can't be an active agent. The CALLING Claude Code agent
    (which is Sonnet) performs the review directly instead of an API call.

    `review_priority` (optional): pass the list from
    stage_4_with_verification()'s returned metadata to flag candidate chunks
    inline in the export -- purely a triage hint (checked first, not trusted
    blindly; see _flag_review_priority's docstring for why it can be wrong).

    Returns a list of batch strings (one per `batch_size` chunks), each
    formatted the same way the manual review that found the v2.1.0 findings
    was actually conducted: chunk_id, current type, topic, truncated body.
    Write each batch to its own file, Read it back, and judge each chunk's
    semantic_type independently of its neighbors (see the prompt text in
    _build_verification_prompt for the exact reasoning standard to apply).
    """
    priority_map = {p["chunk_id"]: p["candidate_type"] for p in (review_priority or [])}

    preamble, c_parts = _split_chunks(chunks_data)
    targets = [p for p in c_parts
               if _get_chunk_level(p) in levels and not _is_backmatter(p)]

    lines = []
    for part in targets:
        cid_m = re.search(r'chunk_id:\s*(\S+)', part)
        cid = cid_m.group(1) if cid_m else '?'
        current_type = _get_semantic_type(part) or 'unknown'
        topic = _get_topic(part)
        body = _get_body(part).strip()[:body_chars].replace('\n', ' ')
        flag = f" [CHECK: regex suggests {priority_map[cid]}]" if cid in priority_map else ""
        lines.append(f"[{cid}] type={current_type} | topic={topic}{flag}\nBODY: {body}\n")

    batches = []
    for i in range(0, len(lines), batch_size):
        batches.append('\n'.join(lines[i:i + batch_size]))
    return batches


def apply_manual_corrections(chunks_data, corrections):
    """
    Manual verification protocol, step 2. `corrections` is a dict of
    {chunk_id: new_semantic_type} produced by the calling agent's own review
    of the export_for_manual_review() batches. Applies them the same way the
    API path does -- exact-match the current `semantic_type: X` line for that
    chunk and replace it, so a stale/wrong chunk_id in `corrections` fails
    loudly (returned in the metadata's `unparsed_ids`) rather than silently
    no-op'ing.
    """
    preamble, c_parts = _split_chunks(chunks_data)
    changed, unparsed, out_parts = 0, [], [preamble]
    seen_ids = set()
    for part in c_parts:
        cid_m = re.search(r'chunk_id:\s*(\S+)', part)
        cid = cid_m.group(1) if cid_m else None
        seen_ids.add(cid)
        if cid not in corrections:
            out_parts.append(part)
            continue
        current_type = _get_semantic_type(part)
        new_type = corrections[cid]
        if new_type not in SEMANTIC_TYPES:
            unparsed.append(cid)          # typo / unknown type: not a valid review
            out_parts.append(part)
            continue
        if new_type == current_type:      # explicit confirmation of the existing type is a valid review
            out_parts.append(part)
            continue
        expected_line = f'semantic_type: {current_type}'
        if expected_line not in part:
            unparsed.append(cid)
            out_parts.append(part)
            continue
        out_parts.append(part.replace(expected_line, f'semantic_type: {new_type}', 1))
        changed += 1

    unparsed.extend(sorted(set(corrections) - seen_ids))   # stale / unknown chunk ids fail loudly
    new_text = ''.join(out_parts)
    metadata = _build_metadata(
        new_text, sonnet_used=True, sonnet_failed_fallback=False,
        sonnet_failure_reason=None, corrected=changed, unparsed_ids=unparsed,
        tokens_used=0, chunks_reviewed=len(corrections),
    )
    metadata["verification_method"] = "manual"
    return new_text, metadata


def _build_metadata(final_text, sonnet_used, sonnet_failed_fallback, sonnet_failure_reason,
                     corrected, unparsed_ids, tokens_used, chunks_reviewed=None):
    types = re.findall(r'^semantic_type:\s*(.+)', final_text, re.M)
    dist = Counter(types)
    total = sum(dist.values())
    unparsed_ratio = len(unparsed_ids) / chunks_reviewed if chunks_reviewed else 0
    status = "partial_success" if unparsed_ratio > 0.10 else "success"
    return {
        "sonnet_verification_used": sonnet_used,
        "sonnet_failed_fallback": sonnet_failed_fallback,
        "sonnet_failure_reason": sonnet_failure_reason,
        "chunks_reviewed": chunks_reviewed if chunks_reviewed is not None else 0,
        "chunks_corrected": corrected,
        "chunks_unparsed": len(unparsed_ids),
        "unparsed_chunk_ids": unparsed_ids,
        "sonnet_tokens_used": tokens_used,
        "status": status,
        "semantic_type_distribution": dict(dist),
        "total_chunks": total,
    }
