"""Stage 4.5d — Clinical Fidelity Gate.

Two-phase design (constraint 3 / IMPLEMENTATION_MAP.md §3.2):
  Phase A: automated candidate detection (regex/diff, zero tokens) across the
           11 sub-checks in REQUIRED_DETECTORS below.
  Phase B: mandatory human adjudication for every CANDIDATE_MISMATCH — never
           auto-resolved (constraint 4). Mirrors the export/apply pattern
           already proven in stage_4_6_sonnet_verification.py's manual path.

Correction E: detectors take the chunk's own source_lines span (sliced
directly from REPAIRED_S2.md, the same mapping Stage 4.5/4.5c already use)
as the primary source-of-truth text to diff against. A five-word local
context window is fallback-only, used solely when source_lines is missing
or malformed on a chunk (should not happen if Stage 4B rule 3 was followed —
same defensive posture as Stage 4.7's disease_focus fallback).

Correction D: every result this module produces carries an explicit
truth_status block — a clean (0-candidate) result is MEASURED against a
DEFINED_PATTERN_SET_ONLY, never described as full semantic verification.

Correction F: boundary-loss candidates are classified into one of
CRITICAL_SEPARATION / SAFE_LINKED_SPLIT / INTENTIONAL_SECTION_SPLIT /
AMBIGUOUS. Only a VERIFIED CRITICAL_SEPARATION is a hard failure.
"""
import hashlib
import functools
import re
from collections import Counter
from datetime import datetime, timezone

SCHEMA_VERSION = "1.0"

TRUTH_STATUS = {
    "status_label": "MEASURED",
    "scope": "DEFINED_PATTERN_SET_ONLY",
    "semantic_completeness_claimed": False,
}

REQUIRED_DETECTORS = [
    "numeric", "unit", "inequality", "range", "dose", "duration",
    "frequency", "negation", "polarity", "sequence", "boundary_loss",
]

DECISION_VALUES = ("confirmed_corruption", "false_positive", "legitimate_paraphrase")


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------
# Correction E — source-span resolution: source_lines first, 5-word context
# fallback only when source_lines is missing/malformed.
# --------------------------------------------------------------------------

def resolve_source_span(repaired_s2_text, chunk_block, window_lines=5):
    """Returns (source_span_text, method) where method is "source_lines" or
    "context_fallback". Reuses the same source_lines frontmatter field
    Stage 4.5/4.5c/4.6 already rely on — no new tracking required.

    v2.6.5 (CATEGORY D emergency fix — see V2_6_5_EMERGENCY_INTEGRITY_FIX_REPORT.md):
    segment parsing is delegated entirely to the canonical
    stages.source_lines_parser module. The previous inline regex here
    handled multiple HYPHENATED ranges correctly (a v2.6.x-era fix for a
    Chapter 05 finding) but still silently dropped any comma-separated
    SINGLE-LINE segment (e.g. "1049-1053,1095" lost the ",1095" entirely,
    and a purely single-line value like "281" fell straight to the 5-word
    context fallback below). A seeded test proved this can silently hide a
    real clinical-content corruption living only in such a segment —
    classified CATEGORY D. This function is now a thin wrapper; do not
    reintroduce inline range-parsing regex here (see
    tests/test_no_duplicate_source_lines_parser.py).
    """
    from pipeline.stages.source_lines_parser import parse_source_lines_from_block, resolve_span_text
    parsed = parse_source_lines_from_block(chunk_block)
    if parsed.segments:
        span = resolve_span_text(repaired_s2_text, parsed.segments)
        if span:
            return span, "source_lines"
    # Fallback: five-word window is a last resort, only reached when
    # source_lines is absent/malformed — flagged in the caller's metadata
    # rather than silently treated as equivalent to a real span mapping.
    body_m = re.search(r'^(?:### Chunk[^\n]*\n)?---\n.*?\n---\n?(.*)$', chunk_block, re.DOTALL)
    body = body_m.group(1).strip() if body_m else chunk_block
    words = body.split()
    context = ' '.join(words[:5])
    return context, "context_fallback"


def _get_body(chunk_block):
    m = re.search(r'^(?:### Chunk[^\n]*\n)?---\n.*?\n---\n?(.*)$', chunk_block, re.DOTALL)
    return m.group(1).strip() if m else chunk_block


def _get_chunk_id(chunk_block):
    m = re.search(r'chunk_id:\s*(\S+)', chunk_block)
    return m.group(1) if m else '?'


# --------------------------------------------------------------------------
# Shared multiset-diff helper for checks 1-7 (numeric/unit/inequality/range/
# dose/duration/frequency) — all are "does this pattern class's token
# multiset survive from source span into chunk body" checks.
# --------------------------------------------------------------------------

def _norm_token(tok):
    """Canonical form of a matched token so equivalent spellings compare equal:
    case, internal whitespace, micro sign / ug, m2 vs m-squared, thousands separators."""
    s = tok.strip().lower()
    s = s.replace("\u00b5", "mc").replace("\u03bc", "mc")           # micro sign / Greek mu -> 'mc'
    s = re.sub(r"(?<![a-z])ug\b", "mcg", s)                             # 50 ug -> 50 mcg
    s = s.replace("m\u00b2", "m2")
    s = re.sub(r"(?<=\d),(?=\d{3}\b)", "", s)                         # 1,000 -> 1000
    s = re.sub(r"\s+", "", s)
    return s


def _multiset_diff(source_span, chunk_body, patterns, check_name, chunk_id):
    """Compare token multisets on a NORMALISED key (so '5mg' == '5 mg', 'ug' == 'mcg'), but report the
    original matched text in the candidate so adjudicators see what the document actually says."""
    def collect(text):
        hits, shown = Counter(), {}
        for p in patterns:
            for m in re.finditer(p, text, re.I):
                raw = m.group(0).strip()
                k = _norm_token(raw)
                hits[k] += 1
                shown.setdefault(k, raw)
        return hits, shown

    src_hits, src_shown = collect(source_span)
    chunk_hits, chunk_shown = collect(chunk_body)

    candidates = []
    for token, src_count in src_hits.items():
        if chunk_hits.get(token, 0) < src_count:
            candidates.append(_candidate(
                check_name, chunk_id, source_value=src_shown[token], chunk_value=None, kind="missing",
            ))
    for token in chunk_hits:
        if src_hits.get(token, 0) == 0:
            candidates.append(_candidate(
                check_name, chunk_id, source_value=None, chunk_value=chunk_shown[token], kind="added",
            ))
    scanned = sum(src_hits.values())
    return candidates, scanned


def _candidate(check, chunk_id, source_value, chunk_value, kind, extra=None):
    """candidate_id is left as a placeholder (None) at creation time —
    real, guaranteed-unique IDs are assigned later by assign_candidate_ids()
    once the full candidate list for a chunk/run is known (v2.6.2; see that
    function's docstring for why creation-time IDs collided)."""
    rec = {
        "candidate_id": None,
        "check": check,
        "chunk_id": chunk_id,
        "source_value": source_value,
        "chunk_value": chunk_value,
        "kind": kind,
        "severity": "CANDIDATE_MISMATCH",
        "status_label": "MEASURED",
        "decision": None,
    }
    if extra:
        rec.update(extra)
    return rec


def _stable_hash(candidate, length=8):
    """Deterministic hash of a candidate's own normalized identifying
    fields — same candidate content always hashes the same way across
    repeated runs on unchanged input, so IDs stay reproducible, not just
    unique-per-run."""
    key = "|".join(str(candidate.get(k)) for k in
                   ("check", "chunk_id", "kind", "source_value", "chunk_value"))
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:length]


def assign_candidate_ids(candidates):
    """v2.6.2 fix (audit finding): the original candidate_id format
    (`4.5d-{check}-{chunk_id}-{source_or_chunk_value}`) collided whenever
    two distinct candidates shared check+chunk_id+value — e.g. two separate
    "missing '2'" findings on the same chunk from two different sentences
    both produced the exact same ID string, silently overwriting one
    another in any dict keyed by candidate_id (including
    apply_adjudication_decisions' own `by_id` lookup).

    New format: `4.5d-{check}-{chunk_id}-{ordinal}-{stable_hash}`. `ordinal`
    is assigned per (check, chunk_id) group, in the order candidates appear
    in the input list — guarantees uniqueness even for two candidates whose
    every OTHER field is identical, which a hash of content alone cannot
    do. Call this once, as a post-processing pass, over the full candidate
    list for a chunk (run_all_detectors_for_chunk, detect_boundary_loss) —
    not per-detector-call, so ordinals are assigned against the complete
    picture for that (check, chunk_id) group.

    Mutates each candidate's `candidate_id` in place and also returns the
    list, for convenient chaining."""
    counters = {}
    for c in candidates:
        group_key = (c["check"], c["chunk_id"])
        counters[group_key] = counters.get(group_key, 0) + 1
        ordinal = counters[group_key]
        c["candidate_id"] = f"4.5d-{c['check']}-{c['chunk_id']}-{ordinal}-{_stable_hash(c)}"
    return candidates


def migrate_legacy_candidate_ids(candidates):
    """Explicit, opt-in migration path for a `ClinicalFidelity.json` file
    written under the pre-v2.6.2 ID format. Re-assigns candidate_id via
    assign_candidate_ids() but touches NO other field — `decision`,
    `status_label`, `severity`, `re_verified` all carry forward unchanged,
    since adjudication decisions live on the record itself, not in an
    external ID-keyed index. Never called automatically; an operator
    re-IDs an existing file explicitly if/when they choose to."""
    return assign_candidate_ids(candidates)


# --------------------------------------------------------------------------
# Checks 1-4: numeric, unit, inequality, range
# --------------------------------------------------------------------------

NUMERIC_PATTERNS = [r'\b\d+(?:\.\d+)?\b']

# Compound-unit grammar: a mass/volume/amount atom optionally followed by any number of "/denominator"
# parts ("mg/kg", "mcg/kg/min", "mL/min/1.73m2", "mg per kg"). The negative lookahead stops the match
# from ending in the middle of a longer unit (the old alternation matched "5 mg" inside "5 mg/kg").
_UNIT_ATOM = (r"(?:mg|mcg|\u00b5g|\u03bcg|ug|ng|pg|kg|g|ml|dl|l|mmol|\u00b5mol|micromol|nmol|pmol|mol|"
              r"meq|units?|iu|u|mmhg|kpa|cmh2o)")
_UNIT_DEN = (r"(?:kg|m2|m\u00b2|dl|ml|l|min|h|hr|hrs|hour|day|d|24\s*h|1\.73\s*m2|1\.73\s*m\u00b2)")
_COMPOUND_UNIT = rf"(?:{_UNIT_ATOM}(?:\s*(?:/|per)\s*{_UNIT_DEN})*|%)"

UNIT_PATTERNS = [
    rf"(?<![\w.])\d+(?:[.,]\d+)*\s*{_COMPOUND_UNIT}(?![\w/])",
]

INEQUALITY_PATTERNS = [
    r'[<>≤≥]', r'\bless than\b', r'\bgreater than\b', r'\bat least\b',
    r'\bat most\b', r'\bor more\b', r'\bor fewer\b',
    r'\bbelow\b', r'\babove\b', r'\bno more than\b', r'\bno less than\b',
    r'\bup to\b', r'\bmaximum of\b', r'\bminimum of\b', r'>=|<=|=<|=>',
]

RANGE_PATTERNS = [r'\b\d+(?:\.\d+)?\s*[-\u2013\u2014\u2212]\s*\d+(?:\.\d+)?\b', r'\b\d+(?:\.\d+)?\s+to\s+\d+(?:\.\d+)?\b']


def detect_numeric(source_span, chunk_body, chunk_id):
    return _multiset_diff(source_span, chunk_body, NUMERIC_PATTERNS, "numeric", chunk_id)


def detect_unit(source_span, chunk_body, chunk_id):
    return _multiset_diff(source_span, chunk_body, UNIT_PATTERNS, "unit", chunk_id)


def detect_inequality(source_span, chunk_body, chunk_id):
    return _multiset_diff(source_span, chunk_body, INEQUALITY_PATTERNS, "inequality", chunk_id)


def detect_range(source_span, chunk_body, chunk_id):
    return _multiset_diff(source_span, chunk_body, RANGE_PATTERNS, "range", chunk_id)


# --------------------------------------------------------------------------
# Check 5: dose — composite of numeric+unit anchored near a drug-name-shaped
# token (capitalized word immediately preceding the dose pattern). Reuses
# Stage 4.5b's existing DOSING pattern list rather than duplicating it.
# --------------------------------------------------------------------------

DOSE_PATTERNS = [
    rf"(?<![\w.])\d+(?:[.,]\d+)*\s*{_UNIT_ATOM}(?:\s*(?:/|per)\s*{_UNIT_DEN})*(?![\w/])",
    r'\b(?:once|twice|three times)\s+(?:daily|weekly)',
    r'\b(?:loading|maintenance)\s+dose\b',
]


def detect_dose(source_span, chunk_body, chunk_id):
    return _multiset_diff(source_span, chunk_body, DOSE_PATTERNS, "dose", chunk_id)


# --------------------------------------------------------------------------
# Checks 6-7: duration, frequency
# --------------------------------------------------------------------------

DURATION_PATTERNS = [r'\b\d+\s*(?:day|week|month|year|hour|min)s?\b', r'\b\d+\s*(?:d|wks?|hrs?)\b']

FREQUENCY_PATTERNS = [
    r'\b(?:once|twice|three times)\s+(?:daily|weekly)\b',
    r'\bevery\s+\d+\s*(?:hours?|hrs?|h)\b',
    r'\b(?:once|twice|two times|three times|four times|[1-4] times)\s+(?:a\s+day|a\s+week|per\s+day)\b',
    r'\bfour times\s+daily\b', r'\bq\.?\d+h\b', r'\bq\.?[dw]\.?\b',
    r'\bbd\b', r'\bbid\b', r'\btds\b', r'\btid\b', r'\bqds\b', r'\bqid\b', r'\bod\b',
    r'\bnocte\b', r'\bmane\b', r'\bprn\b',
]


def detect_duration(source_span, chunk_body, chunk_id):
    return _multiset_diff(source_span, chunk_body, DURATION_PATTERNS, "duration", chunk_id)


def detect_frequency(source_span, chunk_body, chunk_id):
    return _multiset_diff(source_span, chunk_body, FREQUENCY_PATTERNS, "frequency", chunk_id)


# --------------------------------------------------------------------------
# Checks 8-9: negation, polarity — paired-term flip detection. Regex cannot
# prove semantic negation/polarity is preserved (see module docstring and
# IMPLEMENTATION_MAP.md Risk 5) — this can only ever produce a CANDIDATE,
# routed to mandatory human adjudication, never an auto-clear or auto-fail.
# --------------------------------------------------------------------------

NEGATION_PAIRS = [
    ("not indicated", "indicated"), ("not recommended", "recommended"),
    ("contraindicated", "permitted"), ("should not", "should"),
]

POLARITY_PAIRS = [
    ("increase", "decrease"), ("increases", "decreases"),
    ("positive", "negative"), ("associated with", "not associated with"),
    ("before", "after"),
]


def _paired_term_diff(source_span, chunk_body, pairs, check_name, chunk_id):
    src_l, chunk_l = source_span.lower(), chunk_body.lower()
    candidates = []
    scanned = 0
    for term_a, term_b in pairs:
        a_pat = r'\b' + re.escape(term_a) + r'\b'
        b_pat = r'\b' + re.escape(term_b) + r'\b'
        # term_a often CONTAINS term_b as a substring (e.g. "not indicated"
        # contains the word "indicated") -- checking b_pat against the raw
        # text would spuriously find term_b inside every term_a occurrence.
        # Strip term_a matches out first, then check for a genuinely
        # standalone term_b elsewhere in what's left.
        src_b_scope = re.sub(a_pat, ' ', src_l)
        chunk_b_scope = re.sub(a_pat, ' ', chunk_l)
        src_has_a, src_has_b = bool(re.search(a_pat, src_l)), bool(re.search(b_pat, src_b_scope))
        chunk_has_a, chunk_has_b = bool(re.search(a_pat, chunk_l)), bool(re.search(b_pat, chunk_b_scope))
        if src_has_a or src_has_b:
            scanned += 1
        # Flip: source asserts one term, chunk asserts only the OPPOSITE term.
        if src_has_a and not src_has_b and chunk_has_b and not chunk_has_a:
            candidates.append(_candidate(
                check_name, chunk_id, source_value=term_a, chunk_value=term_b, kind="flipped",
                extra={"clinically_consequential": True},
            ))
        elif src_has_b and not src_has_a and chunk_has_a and not chunk_has_b:
            candidates.append(_candidate(
                check_name, chunk_id, source_value=term_b, chunk_value=term_a, kind="flipped",
                extra={"clinically_consequential": True},
            ))
        # Dropped: source asserts a term, chunk asserts neither — lower
        # confidence than a flip (could be legitimate paraphrase/omission),
        # still routed to human review, never auto-cleared.
        elif src_has_a and not chunk_has_a and not chunk_has_b:
            candidates.append(_candidate(
                check_name, chunk_id, source_value=term_a, chunk_value=None, kind="missing",
            ))
        elif src_has_b and not chunk_has_b and not chunk_has_a:
            candidates.append(_candidate(
                check_name, chunk_id, source_value=term_b, chunk_value=None, kind="missing",
            ))
    return candidates, scanned



# --------------------------------------------------------------------------
# Sentence-aligned flip detection (second-sweep 1.4). The whole-chunk pair test above misses a flip
# whenever the opposite term still appears elsewhere in the chunk ("A is contraindicated. B is
# permitted." -> "A is permitted. B is permitted." has 'permitted' in both). Here each SOURCE sentence
# is aligned to its best-overlapping CHUNK sentence and polarity is compared sentence-to-sentence.
# Still only ever produces a CANDIDATE for human adjudication.
# --------------------------------------------------------------------------

NEGATION_MARKERS = [
    r"do not", r"does not", r"did not", r"must not", r"should not", r"shall not", r"cannot", r"can not",
    r"not recommended", r"not indicated", r"not advised", r"not required", r"not associated with",
    r"contraindicated", r"avoid(?:ed|ing)?", r"never", r"no role for", r"no evidence", r"no benefit",
    r"unsafe", r"inadvisable", r"discourage[d]?", r"no\s+indication",
]
_NEG_RE = re.compile(r"(?<!\w)(?:" + "|".join(NEGATION_MARKERS) + r")(?!\w)", re.I)

POLARITY_REGEX_PAIRS = [
    (r"increas(?:e|es|ed|ing)|rise[sn]?|rising|elevat(?:e|es|ed|ion)|higher|raise[sd]?", r"decreas(?:e|es|ed|ing)|fall[s]?|falling|fell|reduc(?:e|es|ed|tion)|lower(?:s|ed)?|drop(?:s|ped)?"),
    (r"positive", r"negative"),
    (r"before", r"after"),
    (r"above", r"below"),
    (r"improv(?:e|es|ed|ement)", r"worsen(?:s|ed|ing)?|deteriorat(?:e|es|ed|ion)"),
    (r"sensitive", r"resistant"),
    (r"present", r"absent"),
]

_STOP = set("a an the is are was were be been being of in on at to for with by from as and or it its this that these those "
            "there their them they he she his her we you i not no".split())


def _sentences(text):
    parts = re.split(r"(?<=[.!?;])\s+(?=[A-Z0-9\[(])|\n{2,}|\n(?=[-*\u2022]\s)", text)
    return [s.strip() for s in parts if s and s.strip()]


@functools.lru_cache(maxsize=20000)
def _content_words_cached(sentence, drop_key):
    s = sentence.lower()
    for rx in drop_key:
        s = re.sub(rx, " ", s, flags=re.I)
    # trailing punctuation is not part of the word ("cephalosporins." == "cephalosporins")
    return frozenset(w for w in (x.rstrip(".-/") for x in re.findall(r"[a-z0-9][a-z0-9.\-/]*", s))
                     if w not in _STOP and len(w) > 1)


def _content_words(sentence, drop_regexes):
    return _content_words_cached(sentence, tuple(drop_regexes))


def _align(src_words, chunk_sents, drop_regexes, min_overlap=0.5, src_sentence=None):
    """Best chunk sentence for a source sentence by content-word overlap (fraction of the source's words).
    An identical sentence always wins, so repeated/near-duplicate sentences never mis-align on ties."""
    best, best_score = None, 0.0
    if not src_words:
        return None
    if src_sentence is not None:
        want = " ".join(src_sentence.split())
        for cs in chunk_sents:
            if " ".join(cs.split()) == want:
                return cs
    for cs in chunk_sents:
        cw = _content_words(cs, drop_regexes)
        score = len(src_words & cw) / len(src_words)
        if score > best_score:
            best, best_score = cs, score
    return best if best_score >= min_overlap else None


def _sentence_negation_flips(source_span, chunk_body, chunk_id):
    cands, scanned = [], 0
    chunk_sents = _sentences(chunk_body)
    drop = [_NEG_RE.pattern, r"\b(?:permitted|indicated|recommended|safe|appropriate)\b"]
    for ss in _sentences(source_span):
        src_neg = bool(_NEG_RE.search(ss))
        src_words = _content_words(ss, drop)
        if len(src_words) < 2 and not (src_words and len(ss.split()) <= 8):
            continue
        match = _align(src_words, chunk_sents, drop, src_sentence=ss)
        if match is None:
            continue
        scanned += 1
        if bool(_NEG_RE.search(match)) != src_neg:
            # re-bulleted text: "X: avoid Y." -> "X:" + "- Avoid Y." keeps the negation in a neighbouring sentence
            if src_neg and any(_NEG_RE.search(cs) and _content_words(cs, drop) and _content_words(cs, drop) <= src_words
                               for cs in chunk_sents):
                continue
            cands.append(_candidate("negation", chunk_id, source_value=ss[:120], chunk_value=match[:120],
                                    kind="flipped", extra={"clinically_consequential": True}))
    return cands, scanned


def _sentence_polarity_flips(source_span, chunk_body, chunk_id):
    cands, scanned = [], 0
    chunk_sents = _sentences(chunk_body)
    for a, b in POLARITY_REGEX_PAIRS:
        a_re = re.compile(r"(?<!\w)(?:" + a + r")(?!\w)", re.I)
        b_re = re.compile(r"(?<!\w)(?:" + b + r")(?!\w)", re.I)
        for ss in _sentences(source_span):
            sa, sb = bool(a_re.search(ss)), bool(b_re.search(ss))
            if sa == sb:                       # neither, or both (ambiguous): not a clean polarity statement
                continue
            src_words = _content_words(ss, [a_re.pattern, b_re.pattern])
            if len(src_words) < 2:
                continue
            match = _align(src_words, chunk_sents, [a_re.pattern, b_re.pattern], src_sentence=ss)
            if match is None:
                continue
            scanned += 1
            ca, cb = bool(a_re.search(match)), bool(b_re.search(match))
            if (sa and cb and not ca) or (sb and ca and not cb):
                cands.append(_candidate("polarity", chunk_id, source_value=ss[:120], chunk_value=match[:120],
                                        kind="flipped", extra={"clinically_consequential": True}))
    return cands, scanned


def _merge(base, extra):
    c1, s1 = base
    c2, s2 = extra
    seen = {(c["source_value"], c["chunk_value"], c["kind"]) for c in c1}
    out = list(c1)
    for c in c2:
        if (c["source_value"], c["chunk_value"], c["kind"]) not in seen:
            out.append(c)
    return out, max(s1, s1 + s2)


def detect_negation(source_span, chunk_body, chunk_id):
    return _merge(_paired_term_diff(source_span, chunk_body, NEGATION_PAIRS, "negation", chunk_id),
                  _sentence_negation_flips(source_span, chunk_body, chunk_id))


def detect_polarity(source_span, chunk_body, chunk_id):
    return _merge(_paired_term_diff(source_span, chunk_body, POLARITY_PAIRS, "polarity", chunk_id),
                  _sentence_polarity_flips(source_span, chunk_body, chunk_id))


# --------------------------------------------------------------------------
# Check 10: sequence — ordered-marker preservation. Detects that the SET of
# sequence markers survives AND that markup-order matches; a genuine
# within-chunk step reorder is always a candidate, never auto-cleared
# (constraint 4 — regex cannot verify clinical step order is correct, only
# that the textual order changed or didn't).
# --------------------------------------------------------------------------

SEQUENCE_MARKER_PATTERNS = [
    r'\bfirst-line\b', r'\bsecond-line\b', r'\binitial\b', r'\bconfirmatory\b',
    r'\bthen\b', r'\bfollowed by\b', r'^\s*\d+\.\s',
]


def _ordered_markers(text, patterns):
    """Lowercased at capture time: comparing marker SETS/order across
    source and chunk must not be defeated by incidental case differences
    ("First-line" vs "first-line") that carry no clinical meaning — only
    genuine reordering or a genuinely missing marker should surface."""
    hits = []
    for p in patterns:
        for m in re.finditer(p, text, re.I | re.MULTILINE):
            hits.append((m.start(), m.group(0).strip().lower()))
    hits.sort(key=lambda h: h[0])
    return [h[1] for h in hits]


def detect_sequence(source_span, chunk_body, chunk_id):
    src_order = _ordered_markers(source_span, SEQUENCE_MARKER_PATTERNS)
    chunk_order = _ordered_markers(chunk_body, SEQUENCE_MARKER_PATTERNS)
    scanned = len(src_order)
    candidates = []

    src_counter, chunk_counter = Counter(src_order), Counter(chunk_order)
    for marker, count in src_counter.items():
        if chunk_counter.get(marker, 0) < count:
            candidates.append(_candidate(
                "sequence", chunk_id, source_value=marker, chunk_value=None, kind="missing",
            ))
    # Same marker SET present but order differs -> reorder candidate.
    # Never auto-cleared even if this check finds nothing -- absence of a
    # detected reorder is not proof the clinical order is correct (constraint 4).
    if src_counter == chunk_counter and src_order and src_order != chunk_order:
        candidates.append(_candidate(
            "sequence", chunk_id, source_value=" -> ".join(src_order),
            chunk_value=" -> ".join(chunk_order), kind="reordered",
            extra={"clinically_consequential": True},
        ))
    return candidates, scanned


# --------------------------------------------------------------------------
# Check 11: boundary-loss (correction F) — operates across a chunk PAIR
# (or a single chunk split-check), not a single source/chunk-body diff like
# checks 1-10. Classifies every finding into one of four buckets; only a
# VERIFIED CRITICAL_SEPARATION is a hard failure.
# --------------------------------------------------------------------------

# Capitalised words that start a sentence are not drug names ("Take Digoxin 5 mg" used to pair "Take" with the dose).
_NOT_A_DRUG = frozenset({
    "Give", "Take", "The", "This", "That", "These", "Those", "Use", "Start", "Stop", "Add", "Avoid", "Consider", "Dose",
    "Doses", "Dosing", "Initial", "Usual", "Maximum", "Minimum", "Total", "Daily", "Single", "Each", "Per", "Then", "Increase",
    "Reduce", "Titrate", "Administer", "Prescribe", "Adults", "Adult", "Children", "Child", "Patients", "Patient", "If", "In",
    "For", "With", "Without", "Up", "After", "Before", "Once", "Twice", "Or", "And", "At", "On", "To", "Of", "A", "An",
})

DRUG_DOSE_ADJACENCY_RE = re.compile(
    r'\b([A-Z][a-z]+(?:in|ol|ide|ate|azole|cillin|mycin)?)\b[^.\n]{0,40}?'
    r'(?<![\w.])(\d+(?:\.\d+)?\s*(?:mg|mcg|g|mL|units?|IU)\b)', re.MULTILINE,
)


_DOSE_RE = re.compile(r'(?<![\w.])(\d+(?:\.\d+)?\s*(?:mg|mcg|g|mL|units?|IU)\b)')
_CAP_WORD_RE = re.compile(r'\b([A-Z][a-z]+(?:in|ol|ide|ate|azole|cillin|mycin)?)\b')


def _drug_dose_pairs(text):
    """(drug, dose) pairs: for each dose, the NEAREST capitalised non-sentence-starter word within 40 characters to
    its left on the same line. (Pairing from the left by regex consumed 'Give' and then missed 'Aspirin'.)"""
    pairs = []
    for m in _DOSE_RE.finditer(text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        window = text[max(line_start, m.start() - 40):m.start()]
        window = window[window.rfind(".") + 1:] if "." in window else window       # stay inside the sentence
        words = [w for w in _CAP_WORD_RE.findall(window) if w not in _NOT_A_DRUG]
        if words:
            pairs.append((words[-1], m.group(1)))
    return pairs


def _contains_token(haystack, token):
    """Whole-token containment: '10 mg' must not be found inside '110 mg' (the old `in` test did exactly that)."""
    return re.search(r'(?<![\w.])' + re.escape(token) + r'(?![\w])', haystack) is not None


def classify_boundary(same_chunk, same_disease_focus, adjacent_chunk_ids,
                       split_at_declared_heading):
    """Pure classification function (correction F) — takes already-computed
    booleans about a drug/dose (or disease/criterion) pair that spans two
    chunks, returns one of the four required labels. Kept separate from the
    detector below so the classification RULES are unit-testable without
    constructing full chunk text fixtures for every case."""
    if same_chunk:
        return None  # not a split at all -- nothing to classify
    if split_at_declared_heading:
        return "INTENTIONAL_SECTION_SPLIT"
    if same_disease_focus and adjacent_chunk_ids:
        return "SAFE_LINKED_SPLIT"
    if not same_disease_focus:
        return "CRITICAL_SEPARATION"
    return "AMBIGUOUS"


def _heading_exists_between(repaired_s2_text, end_of_first, start_of_second):
    """True if a Markdown heading line (any depth, `#` through `######`)
    genuinely sits between two chunks' source spans — used to decide
    `INTENTIONAL_SECTION_SPLIT` from real structural evidence (v2.6.2),
    not mere chunk adjacency. `end_of_first`/`start_of_second` are
    1-indexed source line numbers; a heading is "between" them only if it
    falls strictly inside the gap (no gap at all -> never intentional by
    this signal, since there's nothing to be "at a boundary" of)."""
    if repaired_s2_text is None or end_of_first is None or start_of_second is None:
        return False
    if start_of_second <= end_of_first + 1:
        return False  # no gap between the two spans
    lines = repaired_s2_text.splitlines()
    lo_idx, hi_idx = end_of_first, start_of_second - 1  # 0-indexed gap window
    for i in range(max(0, lo_idx), min(len(lines), hi_idx)):
        if re.match(r'^#{1,6}\s', lines[i]):
            return True
    return False


def detect_boundary_loss(l1_body, l2_chunks, repaired_s2_text=None, scope=""):
    """l2_chunks: list of dicts {chunk_id, body, disease_focus, order,
    (optional) source_lines: (lo, hi)} for every L2 chunk belonging to this
    L1 section, in document order. Finds drug-name/dose adjacency pairs in
    the L1 body (the pre-chunking source) and checks whether both halves
    survive intact within a SINGLE L2 chunk; if not, classifies the split
    via classify_boundary().

    `repaired_s2_text` (v2.6.2, optional): when provided alongside each
    chunk's `source_lines`, enables real `INTENTIONAL_SECTION_SPLIT`
    detection — a chunk_boundary.py audit finding was that this
    classification was implemented and unit-tested in classify_boundary()
    but never actually reachable, because this function always passed
    `split_at_declared_heading=False`. Fixed: when both chunks carry
    `source_lines`, checks whether a real Markdown heading line sits in the
    source gap between them (`_heading_exists_between`) — actual structural
    evidence, not an inference from mere chunk adjacency. Omitting
    `repaired_s2_text` (the default) preserves the prior behavior exactly
    (`split_at_declared_heading` always False) for callers/tests that don't
    need or have real source text."""
    candidates = []
    scanned = 0
    prefix = f"{scope}:" if scope else ""     # keeps ids unique across L1 sections (they collided on "?")
    for drug, dose in _drug_dose_pairs(l1_body):
        scanned += 1
        intact = any(_contains_token(c["body"], drug) and _contains_token(c["body"], dose) for c in l2_chunks)
        if intact:
            continue
        drug_chunks = [c for c in l2_chunks if _contains_token(c["body"], drug)]
        dose_chunks = [c for c in l2_chunks if _contains_token(c["body"], dose)]
        if not drug_chunks or not dose_chunks:
            # One half missing entirely from every L2 chunk -- this is a
            # Stage 4.5c coverage-gap shaped problem, not a boundary-loss
            # shaped one; still surfaced here as AMBIGUOUS so it isn't
            # silently dropped, but not auto-classified as a drug/dose split.
            candidates.append(_candidate(
                "boundary_loss", f"{prefix}?", source_value=f"{drug} {dose}", chunk_value=None,
                kind="incomplete", extra={"boundary_classification": "AMBIGUOUS"},
            ))
            continue
        c1, c2 = drug_chunks[0], dose_chunks[0]
        same_disease = c1.get("disease_focus") and c1.get("disease_focus") == c2.get("disease_focus")
        adjacent = abs(c1.get("order", 0) - c2.get("order", 0)) == 1

        split_at_heading = False
        c1_span, c2_span = c1.get("source_lines"), c2.get("source_lines")
        if repaired_s2_text is not None and c1_span and c2_span:
            if c1_span[1] <= c2_span[0]:
                split_at_heading = _heading_exists_between(repaired_s2_text, c1_span[1], c2_span[0])
            else:
                split_at_heading = _heading_exists_between(repaired_s2_text, c2_span[1], c1_span[0])

        classification = classify_boundary(
            same_chunk=False, same_disease_focus=same_disease,
            adjacent_chunk_ids=adjacent, split_at_declared_heading=split_at_heading,
        )
        candidates.append(_candidate(
            "boundary_loss", f"{prefix}{c1['chunk_id']}/{c2['chunk_id']}",
            source_value=f"{drug} {dose}", chunk_value=None, kind="split",
            extra={
                "boundary_classification": classification,
                "clinically_consequential": classification == "CRITICAL_SEPARATION",
            },
        ))
    assign_candidate_ids(candidates)
    return candidates, scanned


DETECTOR_FUNCS = {
    "numeric": detect_numeric, "unit": detect_unit, "inequality": detect_inequality,
    "range": detect_range, "dose": detect_dose, "duration": detect_duration,
    "frequency": detect_frequency, "negation": detect_negation, "polarity": detect_polarity,
    "sequence": detect_sequence,
    # "boundary_loss" intentionally excluded from DETECTOR_FUNCS: its
    # signature (l1_body, l2_chunks) differs from the other ten (source_span,
    # chunk_body, chunk_id) since it operates across a chunk group, not a
    # single chunk -- run_all_detectors_for_chunk() below documents this.
}


def run_all_detectors_for_chunk(source_span, chunk_body, chunk_id):
    """Runs the ten single-chunk detectors (everything except boundary_loss,
    which needs the whole L1 group -- run separately per L1 section via
    detect_boundary_loss). Returns (all_candidates, scanned_by_check)."""
    all_candidates = []
    scanned_by_check = {}
    for check, fn in DETECTOR_FUNCS.items():
        candidates, scanned = fn(source_span, chunk_body, chunk_id)
        all_candidates.extend(candidates)
        scanned_by_check[check] = scanned
    assign_candidate_ids(all_candidates)
    return all_candidates, scanned_by_check


# --------------------------------------------------------------------------
# Phase B — manual adjudication protocol (mirrors stage_4_6's
# export_for_manual_review / apply_manual_corrections pattern).
# --------------------------------------------------------------------------

def export_candidates_for_review(candidates, batch_size=25):
    lines = []
    for c in candidates:
        lines.append(
            f"[{c['candidate_id']}] check={c['check']} chunk={c['chunk_id']} kind={c['kind']}\n"
            f"  source_value={c['source_value']!r}\n"
            f"  chunk_value={c['chunk_value']!r}\n"
        )
    batches = []
    for i in range(0, len(lines), batch_size):
        batches.append('\n'.join(lines[i:i + batch_size]))
    return batches


def apply_adjudication_decisions(candidates, decisions):
    """decisions: {candidate_id: decision} where decision in DECISION_VALUES.
    Mutates severity/decision/status_label in place on the matching
    candidate dicts. Returns (updated_candidates, unmatched_ids) — a
    decision for a candidate_id that doesn't exist fails loudly via the
    returned list rather than silently no-op'ing (same discipline as
    apply_manual_corrections in stage_4_6_sonnet_verification.py)."""
    by_id = {c["candidate_id"]: c for c in candidates}
    unmatched = []
    for cid, decision in decisions.items():
        if decision not in DECISION_VALUES:
            unmatched.append(cid)
            continue
        c = by_id.get(cid)
        if c is None:
            unmatched.append(cid)
            continue
        c["decision"] = decision
        c["status_label"] = "VERIFIED"
        if decision == "confirmed_corruption":
            c["severity"] = "CONFIRMED_CORRUPTION"
        else:
            c["severity"] = "RESOLVED_NOT_A_CORRUPTION"
    return candidates, unmatched


def unresolved_confirmed_corruptions(candidates):
    """CONFIRMED_CORRUPTION that hasn't yet been re-verified clean after a
    splice-fix (tracked via a separate 're_verified' boolean the caller sets
    once the fix + re-scan round-trip completes, mirroring Stage 4.5's
    splice-fix-then-recheck pattern)."""
    return [c for c in candidates if c["severity"] == "CONFIRMED_CORRUPTION" and not c.get("re_verified")]


def unresolved_candidates(candidates):
    """Any candidate that has not yet been through adjudication at all —
    distinct from unresolved_confirmed_corruptions (confirmed but not yet
    fixed). Correction C requires Stage 6 to check BOTH counts separately,
    since an unadjudicated candidate is not yet classified as a confirmed
    failure and must not be conflated with one."""
    return [c for c in candidates if c["status_label"] != "VERIFIED"]


# --------------------------------------------------------------------------
# Correction C — {PREFIX}_ClinicalFidelityGate.json
# --------------------------------------------------------------------------

def build_clinical_fidelity_gate(candidates, detectors_run, pipeline_version, chapter,
                                  required_detectors=None):
    required = list(required_detectors or REQUIRED_DETECTORS)
    not_tested = [d for d in required if d not in detectors_run]
    unresolved = unresolved_candidates(candidates)
    unresolved_corrupt = unresolved_confirmed_corruptions(candidates)

    if not_tested:
        verdict = "NOT_TESTED"
    elif unresolved or unresolved_corrupt:
        verdict = "BLOCKED"
    else:
        verdict = "PASS"

    return {
        "schema_version": SCHEMA_VERSION,
        "pipeline_version": pipeline_version,
        "chapter": chapter,
        "generated_at": _now(),
        "verdict": verdict,
        "unresolved_candidates": len(unresolved),
        "unresolved_corruptions": len(unresolved_corrupt),
        "detectors_run": sorted(detectors_run),
        "required_detectors": sorted(required),
        "detectors_not_tested": sorted(not_tested),
        "truth_status": dict(TRUTH_STATUS),
        "candidate_count": len(candidates),
    }


def decide_checkpoint_action(gate):
    """CP-02 branch for Stage 4.5d, driven off the same gate dict Stage 6
    re-checks (correction C — single source of truth for the verdict).
    "pending_manual" when candidates still need adjudication (stage stays
    IN_PROGRESS); "blocked" when confirmed corruptions remain unfixed;
    "complete" only on a real PASS; "failed" if required detectors didn't
    run at all (NOT_TESTED is never silently treated as passing)."""
    if gate["verdict"] == "NOT_TESTED":
        return "failed", {"reason": f"detectors not run: {gate['detectors_not_tested']}"}
    if gate["verdict"] == "BLOCKED":
        if gate["unresolved_candidates"] > 0:
            return "pending_manual", {"unresolved_candidates": gate["unresolved_candidates"]}
        return "blocked", {"unresolved_corruptions": gate["unresolved_corruptions"]}
    return "complete", {
        "candidate_count": gate["candidate_count"],
        "truth_status": gate["truth_status"],
    }
