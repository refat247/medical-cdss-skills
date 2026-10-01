"""Guard test (v2.6.5): fails the suite if a second, independent
`source_lines` range-parsing implementation is ever reintroduced anywhere
in this repository. pipeline/stages/source_lines_parser.py must be the ONLY place
that turns a `source_lines` string into line numbers or (start, end)
segments -- every pre-v2.6.5 duplicate of this logic silently dropped
comma-separated single-line segments, a confirmed Category D defect (see
V2_6_5_EMERGENCY_INTEGRITY_FIX_REPORT.md).

This test does not try to parse Python semantically; it greps for the
specific regex *shapes* that characterize a from-scratch source_lines
range parser (a hyphen-range capture pattern applied near a
`source_lines` frontmatter read). New code that needs to parse
`source_lines` must import from pipeline.stages.source_lines_parser instead of
writing a new regex -- if this test starts failing on legitimate new code,
that new code should be migrated to the shared parser, not exempted.
"""
import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANONICAL_PARSER_FILE = os.path.join("stages", "source_lines_parser.py")

# Regex *shapes* that indicate someone hand-rolled a hyphen-range parser
# for source_lines, independent of the canonical module. These are the
# literal patterns found in the four pre-v2.6.5 duplicate implementations.
SUSPICIOUS_PATTERNS = [
    r"""r['"]\(\\d\+\)\\s\*-\\s\*\(\\d\+\)['"]""",   # r'(\d+)\s*-\s*(\d+)'
    r"""r['"]\(\\d\+\)-\(\\d\+\)['"]""",              # r'(\d+)-(\d+)'
    r"""source_lines:\\s\*['"]?\\?\(\\d\+\)-\\?\(\\d\+\)['"]?['"]""",  # inline source_lines+range combo, e.g. stage_4_6_sonnet_verification.py's _get_source_lines()
]

EXCLUDED_DIRS = {".git", "__pycache__", ".pytest_cache", "tests"}
EXCLUDED_PREFIXES = ("_v2_6_2_backup", "_v2_6_3_backup", "_v2_6_4_", "_phase0_phase1_backup",
                      "_source_lines_fix_backup", "_pre_v2_6_3_sync_backup", "_v2_6_5_evidence")


def _iter_python_files():
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        rel_dir = os.path.relpath(dirpath, REPO_ROOT)
        # prune excluded dirs and any timestamped/versioned backup snapshot dir
        dirnames[:] = [
            d for d in dirnames
            if d not in EXCLUDED_DIRS and not d.startswith(EXCLUDED_PREFIXES)
        ]
        if rel_dir == ".":
            rel_dir = ""
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            rel_path = os.path.join(rel_dir, fn) if rel_dir else fn
            yield rel_path, os.path.join(dirpath, fn)


def test_no_independent_source_lines_range_parser_exists():
    offenders = []
    for rel_path, abs_path in _iter_python_files():
        norm_rel = rel_path.replace("\\", "/")
        if norm_rel == CANONICAL_PARSER_FILE.replace("\\", "/"):
            continue
        try:
            text = open(abs_path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for pat in SUSPICIOUS_PATTERNS:
            if re.search(pat, text):
                offenders.append((norm_rel, pat))

    assert not offenders, (
        "Found a hand-rolled source_lines range-parsing regex outside the canonical "
        "pipeline/stages/source_lines_parser.py module. Every source_lines-parsing call site "
        "must use stages.source_lines_parser.parse_source_lines() (or "
        "parse_source_lines_from_block()) instead of re-implementing range parsing. "
        f"Offenders: {offenders}"
    )


def test_canonical_parser_module_exists_and_exports_expected_api():
    from pipeline.stages.source_lines_parser import (
        parse_source_lines, parse_source_lines_from_block, serialize_source_lines,
        resolve_span_text, extract_source_lines_value, SourceLinesParseError,
    )
    assert callable(parse_source_lines)
    assert callable(serialize_source_lines)
