"""Canonical shared `source_lines` frontmatter parser/serializer (v2.6.5,
emergency correctness fix — see V2_6_5_EMERGENCY_INTEGRITY_FIX_REPORT.md).

BACKGROUND: prior to v2.6.5, at least four independent implementations each
parsed the `source_lines:` frontmatter field with their own regex, and every
one of them silently dropped comma-separated single-line segments (and, in
two cases, dropped every segment after the first):

  - pipeline/stages/stage_4_5d_clinical_fidelity.py :: resolve_source_span()
  - pipeline/stages/source_lines_precision.py :: _get_declared_segments()
  - run_stage_4_5d.py :: _l1_span()
  - stage_4_6_sonnet_verification.py :: _get_source_lines()

A seeded test proved this can produce a genuine FALSE NEGATIVE in Stage
4.5d's clinical-fidelity gate: a critical dose fact living only in a
trailing comma-separated single-line segment (e.g. `source_lines:
"10-12,50"`, with the safety-critical text on line 50) was silently
excluded from the span the detectors compare against, so a real, dangerous
corruption of that text (a paracetamol dose ceiling raised from 4g to 40g)
produced only a one-sided `added: 40g` candidate instead of the
unambiguous `missing: 4g` + `added: 40g` pair a correct parser gives — the
single-sided signal is far more likely to be misjudged as a benign false
positive by a reviewer. Classified CATEGORY D — EMERGENCY CORRECTNESS
DEFECT per the evaluation criteria (silent alteration of clinical meaning
going undetected, reproducible across every affected module).

This module is now the ONLY place `source_lines` strings are parsed or
serialized anywhere in this pipeline. `tests/test_no_duplicate_source_lines_parser.py`
fails the test suite if another independent parsing implementation is
ever reintroduced.
"""
import re
from dataclasses import dataclass, field
from typing import List, Tuple


class SourceLinesParseError(ValueError):
    """Raised by parse_source_lines(..., strict=True) when any token in the
    input could not be parsed as a valid single-line or range segment."""


@dataclass
class ParsedSourceLines:
    """segments: normalized, sorted, duplicate-free, non-overlapping list of
    (start, end) INCLUSIVE tuples with start <= end for every entry.
    errors: human-readable strings describing every malformed token found
    (empty list when the input was fully well-formed). A malformed token
    contributes NO segment -- it is never silently coerced into a guessed
    range (this is the core fix: previous implementations either silently
    dropped valid single-line tokens, or silently accepted garbage like
    "1049- 1053-1060" as if it were "1049-1053").
    """
    segments: List[Tuple[int, int]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def line_set(self):
        """Every individual 1-indexed line number covered, as a sorted list."""
        out = set()
        for lo, hi in self.segments:
            out.update(range(lo, hi + 1))
        return sorted(out)


_SINGLE_RE = re.compile(r'^\s*(\d+)\s*$')
_RANGE_RE = re.compile(r'^\s*(\d+)\s*-\s*(\d+)\s*$')
# Matches "source_lines: <value>" or "source_lines: "<value>"" frontmatter lines.
_FRONTMATTER_RE = re.compile(r'source_lines:\s*"?([^"\n]+)"?')


def _merge_segments(segments):
    """Sorts and merges overlapping/adjacent/duplicate segments into the
    minimal equivalent normalized form. [(1,3),(2,4)] -> [(1,4)];
    [(5,5),(5,5)] -> [(5,5)]; [(1,3),(10,12)] stays two segments (no gap)."""
    if not segments:
        return []
    ordered = sorted(segments)
    merged = [ordered[0]]
    for lo, hi in ordered[1:]:
        last_lo, last_hi = merged[-1]
        if lo <= last_hi + 1:  # overlapping or contiguous -> merge
            merged[-1] = (last_lo, max(last_hi, hi))
        else:
            merged.append((lo, hi))
    return merged


def parse_source_lines(raw, *, strict=False) -> ParsedSourceLines:
    """Parses a raw source_lines VALUE (not a whole frontmatter block --
    use extract_source_lines_value() first if you have a full chunk block)
    into a ParsedSourceLines.

    Grammar per comma-separated token (whitespace around commas/dashes is
    always tolerated):
      - a bare integer:      "281"          -> segment (281, 281)
      - a hyphenated range:  "1049-1053"    -> segment (1049, 1053)
      - anything else (reversed range, missing operand, double dash, a
        token that doesn't cleanly match either grammar) is MALFORMED:
        excluded from segments, recorded in errors, never silently
        coerced or partially matched.

    Reversed ranges ("1053-1049", start > end) are explicitly malformed --
    never silently swapped, since doing so would hide a real metadata
    defect rather than surface it (Rule: "validation of reversed or
    malformed ranges", not "auto-repair of reversed ranges").

    Segments are merged/deduplicated and returned sorted ascending
    (normalized ordering) regardless of input order.

    strict=True raises SourceLinesParseError (listing every malformed
    token) instead of returning a result with a non-empty `errors` list --
    use this at any call site where a malformed value must hard-fail
    rather than degrade gracefully.
    """
    result = ParsedSourceLines()
    if raw is None:
        return result
    raw = raw.strip()
    if not raw:
        return result

    tokens = raw.split(',')
    segments = []
    for token in tokens:
        token_stripped = token.strip()
        if not token_stripped:
            continue  # a blank segment from "1049,,1053" is not an error --
            # nothing was lost, just an empty separator; the surrounding
            # non-blank tokens are still parsed normally.

        m_single = _SINGLE_RE.match(token)
        if m_single:
            n = int(m_single.group(1))
            segments.append((n, n))
            continue

        m_range = _RANGE_RE.match(token)
        if m_range:
            lo, hi = int(m_range.group(1)), int(m_range.group(2))
            if lo > hi:
                result.errors.append(
                    f"reversed range {token_stripped!r} (start {lo} > end {hi}) -- "
                    f"not auto-corrected, excluded from segments"
                )
                continue
            segments.append((lo, hi))
            continue

        result.errors.append(f"unparseable token {token_stripped!r} in source_lines value {raw!r}")

    result.segments = _merge_segments(segments)

    if strict and result.errors:
        raise SourceLinesParseError(
            f"source_lines value {raw!r} contains malformed token(s): {'; '.join(result.errors)}"
        )
    return result


def extract_source_lines_value(chunk_block):
    """Pulls the raw source_lines VALUE string out of a full chunk block
    (frontmatter + body), or None if the field is absent. Does not parse
    it -- pass the result to parse_source_lines()."""
    m = _FRONTMATTER_RE.search(chunk_block)
    return m.group(1).strip() if m else None


def parse_source_lines_from_block(chunk_block, *, strict=False) -> ParsedSourceLines:
    """Convenience: extract_source_lines_value() + parse_source_lines() in
    one call, for the common case of having a full chunk block."""
    raw = extract_source_lines_value(chunk_block)
    return parse_source_lines(raw, strict=strict)


def serialize_source_lines(segments) -> str:
    """Deterministic serialization: sorted ascending, merged/deduplicated,
    single-line segments rendered as a bare integer, ranges as "N-M",
    comma-joined with no surrounding whitespace. The inverse of
    parse_source_lines() (round-trips: parse(serialize(parse(x).segments))
    == parse(x) for any x, malformed tokens aside)."""
    merged = _merge_segments(list(segments))
    parts = []
    for lo, hi in merged:
        parts.append(str(lo) if lo == hi else f"{lo}-{hi}")
    return ",".join(parts)


def resolve_span_text(full_text, segments, *, window_lines=0):
    """Given the full source text (e.g. REPAIRED_S2.md contents) and a list
    of (start, end) 1-indexed inclusive line-number segments, returns the
    concatenated text of every referenced line, in segment order, joined
    with newlines. `window_lines` is unused (kept for call-site
    compatibility with the old resolve_source_span() context-fallback
    parameter; the canonical parser has no fallback mode -- callers that
    need a fallback for a totally absent/empty source_lines field must
    implement that at the call site, not inside the shared parser)."""
    lines = full_text.splitlines()
    out_segments = []
    for lo, hi in segments:
        clamped_lo, clamped_hi = max(1, lo), min(len(lines), hi)
        if clamped_lo > clamped_hi:
            continue
        out_segments.append('\n'.join(lines[clamped_lo - 1:clamped_hi]))
    return '\n'.join(out_segments)
