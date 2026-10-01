"""source_lines precision checker/corrector — Stage 4B metadata quality.

Built in response to the Chapter 05 Stage 4.5d adjudication finding: 4 of 5
chunks with clinical-fidelity candidates turned out to have nothing wrong
with their actual body content — their `source_lines` frontmatter was
imprecise (either excluding real content that belongs to the chunk, or
including neighboring content that doesn't). Stage 4.5d's own detectors
trust `source_lines` as ground truth (correction E); if that ground truth
is wrong, every downstream check built on it inherits the error. This
module checks `source_lines` directly against where the chunk's own body
content actually lives in `REPAIRED_S2.md`, independent of Stage 4.5d.

Two failure patterns found on Chapter 05, both handled here:
  - UNDER_INCLUSIVE: real chunk content matches source text OUTSIDE the
    declared source_lines range (L2-097 — a table's numbers weren't in the
    declared "1045-1058" span at all, because the table starts at 1059).
  - OVER_INCLUSIVE: the declared range spans source lines that don't
    correspond to ANY of the chunk's own content, usually because an
    unrelated interleaved block (a box, a figure caption, a running header)
    sits inside the declared range (L2-118 — declared span swept in an
    entire unrelated scurvy box that's separately chunked elsewhere).

This is a MEASUREMENT tool, not a silent auto-fix: `check_chunk_precision()`
only ever proposes a `suggested_segments` value from where the content was
actually found — nothing calls `apply_corrections()` automatically. Same
posture as Stage 4.5d's human-adjudication requirement, scaled down to a
metadata-precision check rather than a clinical-content one (lower stakes,
but still not something to silently rewrite without review).
"""
import re

MATCH_RATE_FLOOR = 0.5
GAP_TOLERANCE = 2  # lines allowed between two matched anchors to still cluster as one segment


def _normalize(s):
    """Tolerant-match normalization: markdown emphasis markers and unicode
    punctuation variants that differ between REPAIRED_S2.md and chunks.md
    without being a real content difference (see Stage 4.5's Rule B — the
    same curly-quote/dash tolerance already established there)."""
    s = re.sub(r'\*+|_+|`+', '', s)
    s = s.replace(''', "'").replace(''', "'")
    s = s.replace('"', '"').replace('"', '"')
    s = s.replace('–', '-').replace('—', '-')
    return s.strip()


def _get_body(chunk_block):
    m = re.search(r'^(?:### Chunk[^\n]*\n)?---\n.*?\n---\n?(.*)$', chunk_block, re.DOTALL)
    return m.group(1).strip() if m else chunk_block


def _get_declared_segments(chunk_block):
    """v2.6.5 (CATEGORY D emergency fix): delegates to the canonical
    stages.source_lines_parser module instead of a local regex. The
    previous inline regex here silently dropped comma-separated
    single-line segments (e.g. "1049-1053,1095" -> only (1049,1053)) and
    returned [] entirely for a pure single-line value like "281" — see
    V2_6_5_EMERGENCY_INTEGRITY_FIX_REPORT.md. Do not reintroduce inline
    range-parsing regex here (see
    tests/test_no_duplicate_source_lines_parser.py)."""
    from pipeline.stages.source_lines_parser import parse_source_lines_from_block
    return parse_source_lines_from_block(chunk_block).segments


def _anchor_units(body, min_len=8):
    """Extracts matchable text units from a chunk body: prose split into
    sentence-length pieces (same technique as Stage 4.5c's clean_sentences),
    PLUS table rows kept as their own anchor (Stage 4.5c explicitly skips
    table rows — correct for its purpose, wrong for this one, since the
    L2-097 failure pattern is precisely a table whose rows are the content
    that needs locating).

    min_len=8, much lower than Stage 4.5c's 20: this checker needs to
    locate WHERE content is, not just confirm its presence, so it can't
    afford to drop short-but-real lines the way a presence-only check can.
    Found on Chapter 05: physical-exam/symptom boxes are dense with short
    list items ("Finger clubbing", "Koilonychia") that a 20-25 char floor
    silently excludes entirely — a chunk built almost entirely from such
    lines could contribute zero anchors, making a genuinely PRECISE chunk
    look OVER_INCLUSIVE purely from under-sampling, not a real metadata
    problem. Safe to lower here specifically because `_find_anchor_line`'s
    hint-line-based nearest-match disambiguation (see its docstring)
    already handles a short/repeated string matching multiple places —
    the risk a longer floor exists to avoid is handled there instead."""
    units = []
    for l in body.splitlines():
        l = l.strip()
        if not l or re.match(r'^#{1,6}\s', l):
            continue
        if l.startswith('|'):
            if re.match(r'^\|?\s*-+\s*\|', l):  # table separator row, no content
                continue
            cell_text = l.strip('|').strip()
            if len(cell_text) >= min_len:
                units.append(cell_text[:100])
            continue
        l = re.sub(r'^[-*]\s+', '', l)  # bullet marker doesn't help matching
        parts = [p.strip() for p in re.split(r'(?<=[.!?])\s+', l) if len(p.strip()) >= min_len]
        units.extend(parts if parts else ([l] if len(l) >= min_len else []))
    return units


def _find_anchor_line(anchor, normalized_source_lines, sample_chars=70, hint_line=None):
    """Returns the 1-indexed line number the anchor was found at, or None.

    Repeated boilerplate (running headers, MCQ stems, recurring bullet
    text) can appear at multiple lines in REPAIRED_S2.md — found on
    Chapter 05: "NUTRITIONAL FACTORS IN DISEASE" (a page-footer residue)
    appears 12 times. An earlier version of this function returned the
    FIRST occurrence anywhere in the document regardless of which chunk was
    being checked, which meant a chunk whose body legitimately ends with
    that boilerplate matched line 9 (the document's first occurrence) no
    matter where the chunk's real content actually was — producing a
    spurious lone "outside declared range" hit for dozens of otherwise
    correctly-mapped chunks. Fixed to return the occurrence CLOSEST to
    `hint_line` (the chunk's declared range) when the anchor matches
    multiple places, rather than always the first.
    """
    key = _normalize(anchor)[:sample_chars]
    if len(key) < 8:
        return None

    if hint_line is not None:
        # Fast local search around hint_line first (covers 99%+ of cases and avoids full-file scans on large corpora)
        hint_int = int(hint_line)
        w_start = max(0, hint_int - 250 - 1)
        w_end = min(len(normalized_source_lines), hint_int + 250)
        local_matches = [w_start + idx + 1 for idx, sl in enumerate(normalized_source_lines[w_start:w_end]) if key in sl]
        if local_matches:
            if len(local_matches) == 1:
                return local_matches[0]
            return min(local_matches, key=lambda ln: abs(ln - hint_line))

    # Full document search when not found locally or when hint_line is None
    matches = [i + 1 for i, sl in enumerate(normalized_source_lines) if key in sl]
    if not matches:
        return None
    if len(matches) == 1 or hint_line is None:
        return matches[0]
    return min(matches, key=lambda ln: abs(ln - hint_line))


def locate_body_in_source(body, repaired_s2_text, hint_line=None):
    """Returns (matched_lines, total_units, unmatched_count). `hint_line`
    should be the declared range's midpoint when available (see
    check_chunk_precision) — used only to disambiguate an anchor that
    matches multiple places in the source, never to constrain which lines
    can match at all."""
    source_lines_list = repaired_s2_text.splitlines()
    normalized_source = [_normalize(l) for l in source_lines_list]
    units = _anchor_units(body)
    matched_lines, unmatched = [], 0
    for u in units:
        found = _find_anchor_line(u, normalized_source, hint_line=hint_line)
        if found:
            matched_lines.append(found)
        else:
            unmatched += 1
    return matched_lines, len(units), unmatched


def _cluster_lines(sorted_unique_lines, gap_tolerance=GAP_TOLERANCE):
    if not sorted_unique_lines:
        return []
    clusters = []
    start = prev = sorted_unique_lines[0]
    for n in sorted_unique_lines[1:]:
        if n - prev <= gap_tolerance + 1:
            prev = n
        else:
            clusters.append((start, prev))
            start = prev = n
    clusters.append((start, prev))
    return clusters


BULLET_LINE_RE = re.compile(r'^[-*]\s+\S.{0,38}$')


def _gap_is_bullet_only(source_lines_list, prev_hi, next_lo):
    """v2.6.4 (Corpus-Scale Gate Closure, MUST-FIX #2, short-bullet handling).

    Found on the real Chapter 02 chapter (not Chapter 05): a hypersensitivity-
    reaction drug list (Box 2.6) produced 3 OVER_INCLUSIVE false positives
    because short, one/two-word bulleted drug names ("- Penicillins",
    "- NSAIDs") fall under _anchor_units()'s min_len=8 anchor floor in
    several spots, so the tool "loses" a few lines in the middle of a
    perfectly contiguous, perfectly verbatim chunk and reports a spurious
    internal gap — not a real interleaved unrelated block (the genuine
    Chapter 05 L2-118 signature this check must NOT suppress).

    Deliberately conservative and NOT a silent auto-clear (per the task's
    explicit "where deterministic resolution is not safe, classify as
    requiring adjudication rather than silently passing it"): this function
    only ever answers "does this specific gap region consist ENTIRELY of
    short bullet lines, with no heading/table/box marker inside it" — a
    True answer downgrades nothing on its own, it only sets the
    `bullet_gap_only` flag `classify_precision()` attaches to its result,
    which callers use to route the finding to low-priority/likely-safe
    adjudication rather than clearing it outright. A single non-bullet,
    non-blank line anywhere in the gap (prose, a box title, a table row)
    fails the check and the gap is treated as a normal, full-priority
    OVER_INCLUSIVE signal.

    `prev_hi`/`next_lo` are 1-indexed matched line numbers bounding the gap
    (exclusive) — the lines actually in question are
    source_lines_list[prev_hi .. next_lo - 2] (0-indexed).
    """
    if source_lines_list is None:
        return False
    for ln in range(prev_hi + 1, next_lo):
        idx = ln - 1
        if idx < 0 or idx >= len(source_lines_list):
            continue
        line = source_lines_list[idx].strip()
        if not line:
            continue
        if re.match(r'^#{1,6}\s', line) or line.startswith('|'):
            return False
        if not BULLET_LINE_RE.match(line):
            return False
    return True


def classify_precision(declared_segments, matched_lines, total_units, unmatched,
                        gap_tolerance=GAP_TOLERANCE, match_rate_floor=MATCH_RATE_FLOOR,
                        source_lines_list=None):
    """Pure classification function — takes already-computed match data,
    returns a verdict + suggested corrected segments. Separated from
    locate_body_in_source() so the classification RULES are unit-testable
    without constructing full REPAIRED_S2.md fixtures for every case.

    `source_lines_list` (v2.6.4, optional, default None): the REPAIRED_S2.md
    source split into lines, needed only for the short-bullet-gap heuristic
    (see _gap_is_bullet_only). Omitting it (every pre-v2.6.4 call site, and
    every existing test that calls this function directly with synthetic
    line numbers) preserves the exact prior behavior — `bullet_gap_only` is
    simply always False in that case, never inferred."""
    match_rate = (total_units - unmatched) / total_units if total_units else 0.0
    if not matched_lines or match_rate < match_rate_floor:
        return {
            "verdict": "UNRESOLVED",
            "match_rate": round(match_rate, 2),
            "matched_anchor_count": len(matched_lines),
            "reason": "too few anchors matched anywhere in source to trust a comparison"
                      if matched_lines else "no anchors matched anywhere in source",
        }

    matched_lines = sorted(set(matched_lines))
    suggested = _cluster_lines(matched_lines, gap_tolerance)

    def covered(point):
        return any(lo <= point <= hi for lo, hi in declared_segments)

    outside = [n for n in matched_lines if not covered(point=n)] if declared_segments else list(matched_lines)

    # Over-inclusion signal: an INTERNAL gap between two-or-more matched
    # clusters that both fall WITHIN THE SAME declared segment — the
    # L2-118 signature (real content before AND after an unrelated
    # interleaved block, inside one contiguous "start-end" range).
    # Deliberately NOT triggered by mere edge-trimming (declared range a
    # couple of lines wider than a single matched cluster) — that's
    # expected noise from this tool's own under-anchoring at chunk
    # boundaries (heading lines are never used as anchors; see
    # _anchor_units), not a real metadata problem. Checked PER declared
    # segment, not across the whole declared_segments list: a chunk whose
    # source_lines is ALREADY a discontinuous, comma-separated range
    # (e.g. "1301-1307, 1334-1334" — the corrected form for exactly the
    # L2-118 case, after splicing the unrelated box out) has a large,
    # perfectly intentional gap BETWEEN its two segments; comparing across
    # segments would re-flag that deliberate exclusion as if it were the
    # problem it was written to fix. An earlier version compared clusters
    # against the declared_segments list as a whole and did exactly that.
    margin = gap_tolerance + 1
    internal_gap_found = False
    all_internal_gaps_bullet_only = True
    any_internal_gap_checked = False
    for d_lo, d_hi in declared_segments:
        in_seg = [n for n in matched_lines if d_lo - margin <= n <= d_hi + margin]
        if len(in_seg) < 2:
            continue
        clusters_in_seg = _cluster_lines(sorted(set(in_seg)), gap_tolerance)
        for (_, prev_hi), (next_lo, _) in zip(clusters_in_seg, clusters_in_seg[1:]):
            if next_lo - prev_hi - 1 > gap_tolerance:
                internal_gap_found = True
                any_internal_gap_checked = True
                if not _gap_is_bullet_only(source_lines_list, prev_hi, next_lo):
                    all_internal_gaps_bullet_only = False
    over_inclusive = bool(declared_segments) and not outside and internal_gap_found
    bullet_gap_only = bool(
        over_inclusive and source_lines_list is not None
        and any_internal_gap_checked and all_internal_gaps_bullet_only
    )

    if outside and over_inclusive:
        verdict = "UNDER_AND_OVER_INCLUSIVE"
    elif outside:
        verdict = "UNDER_INCLUSIVE"
    elif over_inclusive:
        verdict = "OVER_INCLUSIVE"
    else:
        verdict = "PRECISE"

    return {
        "verdict": verdict,
        "match_rate": round(match_rate, 2),
        "declared_segments": declared_segments,
        "suggested_segments": suggested,
        "lines_matched_outside_declared": outside,
        "bullet_gap_only": bullet_gap_only,
    }


def check_chunk_precision(chunk_block, repaired_s2_text):
    """Full pipeline for one chunk: locate + classify. Returns the
    classify_precision() dict plus chunk_id and chunk_level for reporting.

    `chunk_level` (v2.6.4) matters downstream because L1 macro chunks are
    hierarchical/overlapping BY DESIGN (Rule G, SKILL.md) -- an L1 chunk
    legitimately spans multiple L2 children with real gaps between them,
    which this checker's OVER_INCLUSIVE signal cannot distinguish from a
    genuine metadata defect. L1's own source_lines precision is therefore
    advisory/diagnostic only (useful for finding chunking bugs), never a
    trust-classification input -- see build_precision_summary()'s
    `levels` parameter, which defaults to L2-only for exactly this reason.
    """
    m = re.search(r'chunk_id:\s*(\S+)', chunk_block)
    chunk_id = m.group(1) if m else '?'
    lvl_m = re.search(r'chunk_level:\s*(\d)', chunk_block)
    chunk_level = lvl_m.group(1) if lvl_m else None
    body = _get_body(chunk_block)
    declared = _get_declared_segments(chunk_block)
    hint_line = None
    if declared:
        hint_line = (min(lo for lo, _ in declared) + max(hi for _, hi in declared)) / 2
    matched_lines, total_units, unmatched = locate_body_in_source(body, repaired_s2_text, hint_line=hint_line)
    result = classify_precision(declared, matched_lines, total_units, unmatched,
                                 source_lines_list=repaired_s2_text.splitlines())
    result["chunk_id"] = chunk_id
    result["chunk_level"] = chunk_level
    return result


def segments_to_source_lines_string(segments):
    """v2.6.5: delegates to the canonical stages.source_lines_parser
    serializer instead of a local ad hoc format string, so this module's
    output format matches every other source_lines writer in the
    pipeline (single-line segments render as "N", not "N-N"; comma-joined
    with no space, deterministic ordering)."""
    from pipeline.stages.source_lines_parser import serialize_source_lines
    return serialize_source_lines(segments)


# --- Adjudication (v2.6.4, Corpus-Scale Gate Closure, MUST-FIX #2) ---
#
# A checker finding is a CANDIDATE, never a verdict on its own (same posture
# as Stage 4.5d's clinical-fidelity candidates) -- a human (or, in this
# pipeline's actual usage, the calling agent acting as reviewer, same as
# every other manual-verification step in this pipeline) must record one of
# exactly two decisions before a non-PRECISE finding can be considered
# resolved:
#
#   CHECKER_FALSE_POSITIVE       -- the chunk's actual body content is fine;
#                                    only the checker's own anchor-matching
#                                    was fooled (e.g. a bullet_gap_only case
#                                    confirmed by reading the source). No
#                                    file needs to change.
#   HUMAN_CONFIRMED_METADATA_DEFECT -- the chunk's source_lines value really
#                                    is wrong (the Chapter 05 L2-097/L2-118
#                                    pattern). Requires the metadata to
#                                    actually be corrected (apply_corrections)
#                                    and this chunk re-checked before it may
#                                    be treated as resolved.
#
# This is deliberately a much lighter mechanism than Stage 4.5d's hash-locked
# adjudication manifest (pipeline/stages/adjudication_manifest.py) -- source_lines
# precision is a PROVENANCE/traceability concern, not a clinical-content
# concern, and the task scope calls for "an auditable adjudication artifact",
# not a second full manifest-validation subsystem. The candidate-set-hash /
# replay-refusal discipline that manifest system provides remains available
# and unmodified for anyone who wants that level of ceremony for source-lines
# review too; this module does not duplicate it.

ADJUDICATION_DECISION_VALUES = ("CHECKER_FALSE_POSITIVE", "HUMAN_CONFIRMED_METADATA_DEFECT")


def build_findings_set_hash(results):
    """v2.6.5 (Part 4, stale-adjudication prevention): a deterministic hash
    of the CHECKER'S OWN OUTPUT for a results set (chunk_id + verdict +
    declared_segments + suggested_segments per finding), independent of any
    `adjudication` field already recorded. Narrowly scoped to the exact
    failure this was added for: the v2.6.5 source_lines parser fix changed
    which segments/verdicts a chunk resolves to, which silently invalidated
    every pre-fix adjudication decision (a decision recorded against the
    OLD, buggy declared_segments no longer describes the finding a human
    actually reviewed). This hash changes whenever the underlying parser or
    chunk content changes the computed findings, so a caller can detect
    "the evidence I'm about to apply a decision to is not the evidence that
    was actually adjudicated" before accepting it. Deliberately NOT the
    full hash-locked manifest system in pipeline/stages/adjudication_manifest.py —
    see this module's docstring above for why that's out of scope here."""
    import hashlib
    import json as _json
    identity = sorted(
        (
            r.get("chunk_id"),
            r.get("verdict"),
            tuple(tuple(s) for s in (r.get("declared_segments") or [])),
            tuple(tuple(s) for s in (r.get("suggested_segments") or [])),
        )
        for r in results
    )
    canonical = _json.dumps(identity, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def apply_source_lines_adjudication(results, decisions, *, expected_findings_set_sha256=None):
    """`results`: a list of check_chunk_precision()-shaped dicts (each has at
    least `chunk_id` and `verdict`). `decisions`: {chunk_id: {"decision": ...,
    "rationale": ...}}, decision must be one of ADJUDICATION_DECISION_VALUES
    and rationale must be a non-blank string.

    `expected_findings_set_sha256` (optional, v2.6.5 Part 4): if provided,
    must equal `build_findings_set_hash(results)` or the call is refused
    with an error (same all-or-nothing behavior as any other error here) —
    this is the stale-adjudication guard: a caller who recorded decisions
    against one findings set (e.g. before a parser fix or a chunk edit)
    cannot silently replay them onto a DIFFERENT findings set computed
    afterward. Omitting this parameter preserves the pre-v2.6.5 behavior
    exactly (no hash check performed) for existing callers.

    Returns (updated_results, errors). Mutates and returns NEW dicts (does
    not mutate the caller's `results` list in place) -- errors is a list of
    human-readable strings; if errors is non-empty, updated_results is
    returned UNCHANGED (same all-or-nothing discipline as
    apply_validated_manifest() -- never a partial application).

    A resolved finding gets `result["adjudication"] = {"decision": ...,
    "rationale": ..., "adjudicated_at": <UTC ISO8601>}`. This function never
    changes `verdict` itself -- resolution status is tracked separately via
    the adjudication field, so the raw checker verdict a chunk originally
    received is never silently overwritten or lost.
    """
    from datetime import datetime, timezone

    errors = []
    if expected_findings_set_sha256 is not None:
        actual_hash = build_findings_set_hash(results)
        if actual_hash != expected_findings_set_sha256:
            errors.append(
                f"STALE ADJUDICATION REFUSED: expected findings-set hash "
                f"{expected_findings_set_sha256!r}, current results hash to "
                f"{actual_hash!r} -- the underlying source_lines parser or chunk "
                f"content has changed since these decisions were recorded; refusing "
                f"to replay them onto a different findings set."
            )
    by_id = {r.get("chunk_id"): r for r in results}
    for chunk_id, decision_info in decisions.items():
        if chunk_id not in by_id:
            errors.append(f"decision given for unknown chunk_id {chunk_id!r} "
                           f"(not present in the current results set)")
            continue
        decision = decision_info.get("decision")
        rationale = decision_info.get("rationale")
        if decision not in ADJUDICATION_DECISION_VALUES:
            errors.append(f"chunk {chunk_id!r}: invalid decision {decision!r} "
                           f"(must be one of {ADJUDICATION_DECISION_VALUES})")
        if not rationale or not str(rationale).strip():
            errors.append(f"chunk {chunk_id!r}: blank/missing rationale")

    if errors:
        return results, errors

    updated = [dict(r) for r in results]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for r in updated:
        chunk_id = r.get("chunk_id")
        if chunk_id in decisions:
            r["adjudication"] = {
                "decision": decisions[chunk_id]["decision"],
                "rationale": decisions[chunk_id]["rationale"],
                "adjudicated_at": now,
            }
    return updated, []


def _filter_by_level(results, levels):
    """A result missing `chunk_level` entirely (every synthetic result built
    directly in this module's own unit tests, and any caller that hasn't
    been updated to the v2.6.4 check_chunk_precision() shape) is always
    INCLUDED, never silently dropped -- level-filtering only applies once a
    result actually declares which level it came from."""
    return [r for r in results if r.get("chunk_level") is None or r.get("chunk_level") in levels]


def unresolved_findings(results, levels=("2",)):
    """Returns the list of chunk_ids that still block trusted certification:
    verdict != PRECISE AND no adjudication decision recorded yet. A
    CHECKER_FALSE_POSITIVE adjudication resolves a finding permanently (the
    body content was always fine). A HUMAN_CONFIRMED_METADATA_DEFECT
    adjudication does NOT resolve it here -- per the task's required gate
    policy ("confirmed defects must be repaired and rechecked"), a confirmed
    defect only stops being "unresolved" once source_lines is actually
    corrected and the chunk re-checked to PRECISE; recording the confirmation
    alone is not sufficient. Callers that want to distinguish "never looked
    at" from "confirmed broken, fix in progress" should inspect each
    unresolved chunk's `adjudication` field directly -- this function
    intentionally returns a flat list, not a categorized one, since both
    cases block trust identically today.

    `levels` (v2.6.4, default L2-only): L1 macro chunks are hierarchical/
    overlapping BY DESIGN (Rule G) and never ship to RAG_Optimised.md --
    their source_lines imprecision is a chunking-diagnostic signal, not a
    trust-blocking one. Pass levels=("1", "2") for a full diagnostic audit.
    """
    unresolved = []
    for r in _filter_by_level(results, levels):
        if r.get("verdict") == "PRECISE":
            continue
        adjudication = r.get("adjudication")
        if adjudication and adjudication.get("decision") == "CHECKER_FALSE_POSITIVE":
            continue
        unresolved.append(r.get("chunk_id"))
    return unresolved


def build_precision_summary(results, levels=("2",)):
    """Aggregate counts for disclosure in SourceLinesPrecision.md/.json,
    Stage 4.5d's source_mapping block, and corpus-trust classification.
    Always includes `tested: True` (a summary only ever gets built from a
    results list that came from an actual run) and `unresolved_count`
    (len(unresolved_findings(results, levels))) -- the two fields
    corpus_trust.py needs to decide CORPUS_TESTING_READY vs
    CORPUS_REVIEW_PENDING.

    `levels` (v2.6.4, default L2-only, same rationale as unresolved_findings):
    `chunks_checked`/`by_verdict`/`bullet_gap_only_count` are also scoped to
    `levels` so the summary is internally consistent (a report that says
    "162 chunks checked, 3 unresolved" when the 3 unresolved were computed
    from a 110-chunk L2-only subset would be misleading)."""
    scoped = _filter_by_level(results, levels)
    by_verdict = {}
    for r in scoped:
        by_verdict.setdefault(r.get("verdict"), 0)
        by_verdict[r.get("verdict")] += 1
    bullet_gap_count = sum(1 for r in scoped if r.get("bullet_gap_only"))
    unresolved = unresolved_findings(results, levels)
    return {
        "tested": True,
        "chunks_checked": len(scoped),
        "by_verdict": by_verdict,
        "bullet_gap_only_count": bullet_gap_count,
        "unresolved_count": len(unresolved),
        "unresolved_chunk_ids": unresolved,
    }


def apply_corrections(chunks_text, corrections):
    """corrections: {chunk_id: [(lo, hi), ...]} — explicit invocation only,
    never called automatically by check_chunk_precision(). Replaces each
    matched chunk's source_lines line with the corrected value; a
    chunk_id in `corrections` not found in chunks_text fails loudly via the
    returned unmatched list (same discipline as Stage 4.6's
    apply_manual_corrections / Stage 4.5d's apply_adjudication_decisions)."""
    blocks = re.findall(r'(---\nchunk_id:.*?\n---\n.*?)(?=\n---\nchunk_id:|\Z)', chunks_text, re.DOTALL)
    by_id = {}
    for b in blocks:
        m = re.search(r'chunk_id:\s*(\S+)', b)
        if m:
            by_id[m.group(1)] = b

    changed, unmatched, new_text = 0, [], chunks_text
    for chunk_id, segments in corrections.items():
        block = by_id.get(chunk_id)
        if block is None:
            unmatched.append(chunk_id)
            continue
        new_value = segments_to_source_lines_string(segments)
        new_block = re.sub(r'source_lines:\s*"?[\d,\s\-]+"?', f'source_lines: "{new_value}"', block, count=1)
        if new_block == block:
            unmatched.append(chunk_id)
            continue
        new_text = new_text.replace(block, new_block, 1)
        changed += 1
    return new_text, changed, unmatched
