"""v2.6.4 -- Corpus-Scale Gate Closure, MUST-FIX #3 (part 2, staleness
prevention). Regenerates the trust ledger in memory from the REAL corpus
and compares it against the committed `CORPUS_TRUST_STATUS.md`. This is the
mechanism that makes ledger staleness a CI-visible test failure instead of
a silent gap discovered months later (exactly what happened after Chapter
02 completed and was never added to the hand-maintained file).

This test is EXPECTED to fail (genuine RED) any time a chapter's real
classification changes and the committed file hasn't been regenerated yet
via `python generate_corpus_trust_ledger.py <root> --write --in-place`. That
is the intended, correct behavior -- do not "fix" a failure here by loosening
the comparison; fix it by regenerating and committing the ledger for real.
"""
import os
import re

import pytest

from pipeline.stages.trust_ledger import build_corpus_trust_ledger

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS_ROOT = os.path.abspath(os.path.join(REPO_DIR, ".."))
LEDGER_PATH = os.path.join(CORPUS_ROOT, "CORPUS_TRUST_STATUS.md")


def _skip_unless_real_corpus_present():
    if not os.path.exists(LEDGER_PATH):
        pytest.skip("Real CORPUS_TRUST_STATUS.md not present in this environment")


def _committed_classifications():
    """Extracts {chapter_dir: classification} pairs from the committed
    markdown table -- tolerant of either the old hand-written table shape
    (columns: Chapter | Directory | Checkpoint? | Classification | Reason)
    or the new generator's table shape (Chapter | Checkpoint? |
    Classification | Trusted? | Protected? | Reasons), since this test's
    job is to detect CONTENT drift, not enforce one exact rendering.

    Keys off whichever cell contains a backtick-wrapped directory-like
    token (e.g. `` `25_AI_H/` `` or a bare `05`) rather than the free-text
    chapter-label cell, which collapses distinct legacy variants like
    `25_AI_C`/`25_AI_H` down to the same leading "25" otherwise."""
    text = open(LEDGER_PATH, encoding="utf-8").read()
    pairs = {}
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue

        chapter_key = None
        for cell in cells:
            m = re.search(r'`([0-9]{2}(?:_[A-Za-z0-9]+)*)/?`', cell)
            if m:
                chapter_key = m.group(1)
                break
        if chapter_key is None:
            m = re.match(r'^([0-9]{2}(?:_[A-Za-z0-9]+)*)\b', cells[0])
            chapter_key = m.group(1) if m else None
        if chapter_key is None:
            continue

        classification_cell = None
        for cell in cells[1:]:
            m = re.search(r'\*\*`?([A-Z][A-Z_]{5,})`?', cell)  # real classifications are long ALL_CAPS tokens
            if m:
                classification_cell = m.group(1)
                break
        if classification_cell is None:
            continue
        pairs[chapter_key] = classification_cell
    return pairs


def test_regenerated_ledger_matches_committed_status_for_every_real_chapter():
    _skip_unless_real_corpus_present()
    ledger = build_corpus_trust_ledger(CORPUS_ROOT)
    committed = _committed_classifications()

    mismatches = []
    for record in ledger["chapters"]:
        chapter_dir = record["chapter_dir"]
        # Match a committed row whose chapter cell CONTAINS this directory
        # name (committed rows historically use "05 — Nutritional factors...",
        # generated rows use the bare directory name "05").
        matched_key = next((k for k in committed if chapter_dir in k or k in chapter_dir), None)
        if matched_key is None:
            mismatches.append(f"{chapter_dir}: MISSING from committed CORPUS_TRUST_STATUS.md "
                               f"(regenerated ledger says {record['classification']})")
            continue
        if committed[matched_key] != record["classification"]:
            mismatches.append(f"{chapter_dir}: committed says {committed[matched_key]!r}, "
                               f"regenerated ledger says {record['classification']!r}")

    assert not mismatches, (
        "CORPUS_TRUST_STATUS.md is STALE relative to real repository evidence:\n  "
        + "\n  ".join(mismatches)
        + "\n\nRegenerate and commit it: python generate_corpus_trust_ledger.py "
          f"{CORPUS_ROOT!r} --write --in-place"
    )
