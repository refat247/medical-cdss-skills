"""v2.6.6 -- read-only post-finalization invariant checker (Fail-Closed
Finalization, task item 7). Runs after any finalization/repair pass to
confirm every chapter the committed CORPUS_TRUST_STATUS.md currently lists
as CORPUS_TESTING_READY genuinely still satisfies every invariant that
classification implies. Two real historical defects motivate the specific
checks below:

  - Chapter 11-style: a mandatory evidence field
    (stage_completions["4.7"]["unresolved_completeness_clusters"], or the
    equivalent Stage 4.6/Stage 8 fields) missing or malformed, while the
    ledger still shows CORPUS_TESTING_READY from a stale prior computation.
  - Chapter 03-style: a protection marker filename mismatch -- a prefixed
    `{PREFIX}_CORPUS_OUTPUT_PROTECTED.json` on disk instead of (or alongside)
    the canonical bare `CORPUS_OUTPUT_PROTECTED.json`, so the chapter shows
    trusted but NOT protected, or protected-looking-but-wrong-file.
  - Chapter 11/15-style (v2.6.7): Stage 6's OWN internal chunk count is
    silently wrong -- `check_6_1_6_2()`'s block-splitting had a real blind
    spot (see pipeline/stages/stage_6_validation.py's v2.6.7 fix and
    REPOSITORY_PRODUCTION_READINESS_AUDIT.md Blocker 2) that dropped a
    file's last chunk when it was empty-body and the file lacked a trailing
    newline. Nothing in this checker previously re-derived Stage 6's chunk
    count from source -- it only checked that Stage 4.6/4.7/8 evidence
    fields were PRESENT, never that Stage 6's own already-computed
    `chunks_checked` value was actually CORRECT. `_check_stage6_chunk_count`
    below closes that gap: it independently re-parses the current
    `RAG_Optimised.md` with the (now-fixed) canonical parser and requires
    that re-derived count, `Stage6_Validation.md`'s declared "Chunks
    checked" figure, and the checkpoint's own
    `stage_completions["6"]["chunks_checked"]` field all agree.

Purely read-only: never writes, renames, or deletes anything. Exits non-zero
if ANY violation is found, printing every one with the exact chapter and the
exact failing invariant.

Usage:
    python verify_trusted_corpus_invariants.py <corpus_root>
"""
import argparse
import glob
import os
import re
import sys

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_DIR)

from pipeline.stages import trust_ledger  # noqa: E402
from pipeline.stages.mutation_guard import PROTECTION_MARKER_FILENAME, protection_marker_path  # noqa: E402
from pipeline.stages.stage_6_validation import check_6_1_6_2, _split_blocks  # noqa: E402


def _parse_stage6_report_chunks_checked(report_text):
    """Parses 'Chunks checked: N' out of a Stage6_Validation.md report
    (see rerun_stage6_ch05.py's own report-writing format, which every
    chapter's Stage6_Validation.md follows). Returns an int, or None if the
    line is missing or its value isn't a clean non-negative integer
    (malformed -- e.g. a string, blank, or negative number)."""
    m = re.search(r'Chunks checked:\s*(\S+)', report_text)
    if not m:
        return None
    raw = m.group(1).strip()
    if not re.fullmatch(r'\d+', raw):
        return None  # not a clean non-negative integer -- malformed
    return int(raw)


def _check_stage6_chunk_count(output_dir, chapter_dir, prefix, checkpoint):
    """v2.6.7 addition: independently re-derives the actual L2 chunk count
    from the chapter's current `RAG_Optimised.md` (using the fixed
    check_6_1_6_2 parser) and requires it to equal BOTH the chapter's own
    `Stage6_Validation.md` declared count AND the checkpoint's
    `stage_completions["6"]["chunks_checked"]` field. Any missing file,
    missing/malformed checkpoint field, or any pairwise disagreement among
    the three is a violation -- this is the cross-check that would have
    caught the Chapter 11/15 defect automatically instead of requiring a
    manual audit to find it."""
    violations = []
    rag_matches = glob.glob(os.path.join(output_dir, f"{prefix}_RAG_Optimised.md"))
    if not rag_matches:
        violations.append(
            f"{chapter_dir} [STAGE-6-CHUNK-COUNT-DEFECT]: no {prefix}_RAG_Optimised.md found -- "
            "cannot independently re-derive the Stage 6 chunk count at all."
        )
        return violations
    with open(rag_matches[0], encoding="utf-8") as f:
        rag_text = f.read()
    _, fresh_count = check_6_1_6_2(rag_text)

    report_path = os.path.join(output_dir, f"{prefix}_Stage6_Validation.md")
    report_count = None
    if not os.path.exists(report_path):
        violations.append(
            f"{chapter_dir} [STAGE-6-CHUNK-COUNT-DEFECT]: no {prefix}_Stage6_Validation.md found."
        )
    else:
        with open(report_path, encoding="utf-8") as f:
            report_text = f.read()
        report_count = _parse_stage6_report_chunks_checked(report_text)
        if report_count is None:
            violations.append(
                f"{chapter_dir} [STAGE-6-CHUNK-COUNT-DEFECT]: {prefix}_Stage6_Validation.md's "
                "'Chunks checked' value is missing or not a clean non-negative integer."
            )

    stage_6 = (checkpoint or {}).get("stage_completions", {}).get("6", {}) or {}
    checkpoint_count = stage_6.get("chunks_checked")
    if "chunks_checked" not in stage_6:
        violations.append(
            f"{chapter_dir} [STAGE-6-CHUNK-COUNT-DEFECT]: "
            'stage_completions["6"]["chunks_checked"] is not present in the checkpoint at all.'
        )
    elif not isinstance(checkpoint_count, int) or isinstance(checkpoint_count, bool) or checkpoint_count < 0:
        violations.append(
            f"{chapter_dir} [STAGE-6-CHUNK-COUNT-DEFECT]: "
            f'stage_completions["6"]["chunks_checked"] is malformed (got {checkpoint_count!r}, '
            "expected a non-negative int)."
        )
        checkpoint_count = None

    counts = {"fresh re-derived count": fresh_count}
    if report_count is not None:
        counts["Stage6_Validation.md declared count"] = report_count
    if checkpoint_count is not None:
        counts["checkpoint chunks_checked"] = checkpoint_count

    distinct = set(counts.values())
    if len(distinct) > 1:
        violations.append(
            f"{chapter_dir} [STAGE-6-CHUNK-COUNT-DEFECT] [CHAPTER-11-15-STYLE]: Stage 6 chunk counts "
            f"disagree -- {counts}. The parser fix (v2.6.7) re-derives the true count independently; "
            "any disagreement means the checkpoint and/or Stage6_Validation.md is stale and Stage 6 "
            "must be re-run for this chapter."
        )
    return violations


_RELATED_CHUNKS_LINE_RE = re.compile(r'^related_chunks:\s*(.*)$', re.M)
_STAGE_5_4_LABEL = "[STAGE-5.4-OUTPUT-PERSISTENCE-DEFECT]"


def _parse_related_chunks_value(raw):
    """Parses a `related_chunks: [...]` line's value into a list of chunk id
    strings, or returns None if the value is not valid Python-list-like
    syntax (must be a single `[...]` bracketed, comma-separated list --
    possibly empty). None is the caller's signal for "malformed", distinct
    from a genuinely empty list (`[]` parses to `[]`, a valid, clean state)."""
    raw = raw.strip()
    m = re.fullmatch(r'\[(.*)\]', raw, re.DOTALL)
    if m is None:
        return None
    inner = m.group(1).strip()
    if not inner:
        return []
    return [tok.strip() for tok in inner.split(',')]


def _parse_l2_chunks_for_5_4(text):
    """Splits text (chunks.md or RAG_Optimised.md content) into L2 blocks
    using the same v2.6.7-fixed, frontmatter-boundary-robust parser Stage 6
    uses (`_split_blocks`), then extracts, per chunk_id: disease_focus, the
    list of raw `related_chunks:` line values found (0, 1, or >1 -- more
    than 1 is a duplicate-field defect, not silently collapsed to the
    last/first match), and the parsed related_chunks list (None if
    malformed or absent).

    Returns (info_by_id, structural_errors) where info_by_id maps
    chunk_id -> {"disease_focus": str, "raw_values": [str, ...],
    "parsed": list|None}. structural_errors carries any chunk whose
    frontmatter never closes (same malformed-block class Stage 6 itself
    surfaces) -- never silently dropped."""
    blocks, malformed = _split_blocks(text)
    info_by_id = {}
    for b in blocks:
        if not re.search(r'chunk_level:\s*2', b):
            continue
        cid_m = re.search(r'chunk_id:\s*(.+)', b)
        cid = cid_m.group(1).strip() if cid_m else '?'
        dfm = re.search(r'disease_focus:\s*(.*)', b)
        disease_focus = dfm.group(1).strip() if dfm else ''
        raw_values = [v for v in _RELATED_CHUNKS_LINE_RE.findall(b)]
        parsed = _parse_related_chunks_value(raw_values[0]) if len(raw_values) == 1 else None
        info_by_id[cid] = {
            "disease_focus": disease_focus,
            "raw_values": raw_values,
            "parsed": parsed,
        }
    return info_by_id, malformed


def _check_stage_5_4_persistence(output_dir, chapter_dir, prefix, checkpoint):
    """v2.6.8 addition (Chapter 11 related_chunks restoration task, Part 6):
    for any chapter whose checkpoint claims Stage 5.4 COMPLETED, independently
    re-derives the real on-disk state of `related_chunks` from both
    `chunks.md` and `RAG_Optimised.md` and confirms it actually matches that
    claim. This is the general-shape structural gap the Chapter 11 audit
    (CH11_RELATED_CHUNKS_CONTRACT_AUDIT.md) identified: a stage's checkpoint
    can say COMPLETED with a specific linked_chunks count while a later,
    unrelated chunk-file mutation silently erases the field it wrote, and
    nothing previously re-checked that claim against current file content.

    A chapter where Stage 5.4 was never run at all (no "5.4" key, or present
    but not COMPLETED) is explicitly NOT a violation of this check -- that is
    a legitimate, different state (Stage 5.4 simply hasn't run yet), and this
    function returns an empty list immediately for it.
    """
    stage_5_4 = (checkpoint or {}).get("stage_completions", {}).get("5.4")
    if not stage_5_4 or stage_5_4.get("status") != "COMPLETED":
        return []

    violations = []

    chunks_matches = glob.glob(os.path.join(output_dir, f"{prefix}_chunks.md"))
    if not chunks_matches:
        violations.append(
            f"{chapter_dir} {_STAGE_5_4_LABEL}: Stage 5.4 is COMPLETED in the checkpoint but no "
            f"{prefix}_chunks.md exists at all -- cannot verify its output."
        )
        return violations
    with open(chunks_matches[0], encoding="utf-8") as f:
        chunks_text = f.read()
    chunks_info, chunks_malformed = _parse_l2_chunks_for_5_4(chunks_text)
    for m in chunks_malformed:
        violations.append(f"{chapter_dir} {_STAGE_5_4_LABEL}: chunks.md malformed block -- {m}")

    real_l2_count = len(chunks_info)

    rag_matches = glob.glob(os.path.join(output_dir, f"{prefix}_RAG_Optimised.md"))
    if not rag_matches:
        violations.append(
            f"{chapter_dir} {_STAGE_5_4_LABEL}: Stage 5.4 is COMPLETED but "
            f"{prefix}_RAG_Optimised.md is missing entirely -- cannot cross-check related_chunks "
            "persistence into the shipped RAG output."
        )
        rag_info = {}
    else:
        with open(rag_matches[0], encoding="utf-8") as f:
            rag_text = f.read()
        rag_info, rag_malformed = _parse_l2_chunks_for_5_4(rag_text)
        for m in rag_malformed:
            violations.append(f"{chapter_dir} {_STAGE_5_4_LABEL}: RAG_Optimised.md malformed block -- {m}")

    # (1)/(5): checkpoint linked_chunks must equal the real L2 count.
    linked_chunks = stage_5_4.get("linked_chunks")
    if linked_chunks != real_l2_count:
        violations.append(
            f"{chapter_dir} {_STAGE_5_4_LABEL}: checkpoint stage_completions['5.4']['linked_chunks'] "
            f"({linked_chunks!r}) does not equal the real L2 chunk count in chunks.md "
            f"({real_l2_count})."
        )

    # (2): total absence -- every L2 chunk in chunks.md must have a
    # related_chunks field. (Chapter-11 scenario: 0 of N have it.)
    missing_in_chunks = [cid for cid, info in chunks_info.items() if len(info["raw_values"]) == 0]
    if missing_in_chunks:
        if len(missing_in_chunks) == real_l2_count and real_l2_count > 0:
            violations.append(
                f"{chapter_dir} {_STAGE_5_4_LABEL}: Stage 5.4 is COMPLETED but ALL {real_l2_count} "
                "L2 chunks in chunks.md are missing related_chunks entirely -- total output loss "
                "(the Chapter 11 defect shape: a completed stage's output has vanished from the "
                "current file content)."
            )
        else:
            violations.append(
                f"{chapter_dir} {_STAGE_5_4_LABEL}: {len(missing_in_chunks)}/{real_l2_count} L2 "
                f"chunk(s) in chunks.md are missing related_chunks while others have it -- partial "
                f"field loss. Missing: {missing_in_chunks[:10]}"
                + (" ..." if len(missing_in_chunks) > 10 else "")
            )

    # Duplicate related_chunks lines within a single chunk block.
    duplicated = [cid for cid, info in chunks_info.items() if len(info["raw_values"]) > 1]
    if duplicated:
        violations.append(
            f"{chapter_dir} {_STAGE_5_4_LABEL}: chunk(s) with duplicate related_chunks lines in "
            f"chunks.md: {duplicated}"
        )

    # Malformed (not valid Python-list-like syntax) values, for chunks that
    # do have exactly one related_chunks line.
    malformed_values = [
        cid for cid, info in chunks_info.items()
        if len(info["raw_values"]) == 1 and info["parsed"] is None
    ]
    if malformed_values:
        violations.append(
            f"{chapter_dir} {_STAGE_5_4_LABEL}: chunk(s) with a malformed (not valid list syntax) "
            f"related_chunks value in chunks.md: {malformed_values}"
        )

    # (3): every corresponding L2 chunk in RAG_Optimised.md must also have
    # exactly one related_chunks field.
    if rag_matches:
        missing_in_rag = [
            cid for cid in chunks_info
            if cid in rag_info and len(rag_info[cid]["raw_values"]) == 0
        ]
        if missing_in_rag:
            violations.append(
                f"{chapter_dir} {_STAGE_5_4_LABEL}: chunk(s) present with related_chunks in "
                f"chunks.md but missing it from RAG_Optimised.md: {missing_in_rag[:10]}"
                + (" ..." if len(missing_in_rag) > 10 else "")
            )
        not_in_rag_at_all = [cid for cid in chunks_info if cid not in rag_info]
        if not_in_rag_at_all:
            violations.append(
                f"{chapter_dir} {_STAGE_5_4_LABEL}: L2 chunk(s) in chunks.md not found at all in "
                f"RAG_Optimised.md: {not_in_rag_at_all[:10]}"
                + (" ..." if len(not_in_rag_at_all) > 10 else "")
            )

        # (4): values must match between the two files, for chunks present
        # in both with a cleanly-parsed value in each.
        mismatched = []
        for cid, info in chunks_info.items():
            r_info = rag_info.get(cid)
            if r_info is None:
                continue
            if info["parsed"] is None or r_info["parsed"] is None:
                continue
            if sorted(info["parsed"]) != sorted(r_info["parsed"]):
                mismatched.append(cid)
        if mismatched:
            violations.append(
                f"{chapter_dir} {_STAGE_5_4_LABEL}: chunk(s) whose related_chunks value differs "
                f"between chunks.md and RAG_Optimised.md: {mismatched[:10]}"
                + (" ..." if len(mismatched) > 10 else "")
            )

    # Remaining relationship-integrity checks operate on chunks.md's cleanly
    # parsed values only (a chunk with a malformed/missing value already
    # produced a violation above and is skipped here to avoid noise).
    valid_ids = set(chunks_info.keys())
    clean = {cid: info for cid, info in chunks_info.items() if info["parsed"] is not None}

    invalid_refs = []
    self_refs = []
    cross_disease_refs = []
    for cid, info in clean.items():
        for ref in info["parsed"]:
            if ref == cid:
                self_refs.append(cid)
                continue
            if ref not in valid_ids:
                invalid_refs.append((cid, ref))
                continue
            ref_info = chunks_info.get(ref)
            if ref_info is not None and ref_info["disease_focus"] != info["disease_focus"]:
                cross_disease_refs.append((cid, ref))

    if invalid_refs:
        violations.append(
            f"{chapter_dir} {_STAGE_5_4_LABEL}: related_chunks reference(s) to non-existent chunk "
            f"id(s): {invalid_refs[:10]}" + (" ..." if len(invalid_refs) > 10 else "")
        )
    if self_refs:
        violations.append(
            f"{chapter_dir} {_STAGE_5_4_LABEL}: chunk(s) with a self-reference in related_chunks: "
            f"{self_refs[:10]}" + (" ..." if len(self_refs) > 10 else "")
        )
    if cross_disease_refs:
        violations.append(
            f"{chapter_dir} {_STAGE_5_4_LABEL}: cross-disease_focus related_chunks reference(s) "
            f"found (same-disease heuristic violated): {cross_disease_refs[:10]}"
            + (" ..." if len(cross_disease_refs) > 10 else "")
        )

    # Symmetry: under the same-disease heuristic, if A links to B, B must
    # link back to A (only checked for pairs that are otherwise valid,
    # same-disease references, to avoid double-reporting an already-flagged
    # invalid/cross-disease ref as also "asymmetric").
    asymmetric = []
    for cid, info in clean.items():
        for ref in info["parsed"]:
            if ref == cid or ref not in valid_ids:
                continue
            ref_info = chunks_info.get(ref)
            if ref_info is None or ref_info["disease_focus"] != info["disease_focus"]:
                continue
            ref_parsed = ref_info["parsed"]
            if ref_parsed is None or cid not in ref_parsed:
                asymmetric.append((cid, ref))
    if asymmetric:
        violations.append(
            f"{chapter_dir} {_STAGE_5_4_LABEL}: asymmetric same-disease related_chunks "
            f"relationship(s) (A links to B but B does not link back to A): {asymmetric[:10]}"
            + (" ..." if len(asymmetric) > 10 else "")
        )

    return violations


def _committed_classifications(corpus_root):
    """Parses the committed CORPUS_TRUST_STATUS.md table -- the same
    lightweight row-parsing approach tests/test_trust_ledger_staleness.py
    uses -- to find every chapter CURRENTLY DECLARED CORPUS_TESTING_READY,
    independent of what a fresh recomputation says (that comparison is
    exactly what this script exists to make)."""
    path = os.path.join(corpus_root, "CORPUS_TRUST_STATUS.md")
    declared = {}
    if not os.path.exists(path):
        return declared
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|\n").split("|")]
            if len(cells) < 4:
                continue
            chapter_cell, _checkpoint, classification_cell = cells[0], cells[1], cells[2]
            if chapter_cell in ("Chapter", "---") or set(chapter_cell) <= {"-"}:
                continue
            classification = classification_cell.strip("*").strip()
            if classification:
                declared[chapter_cell] = classification
    return declared


def check_chapter(corpus_root, chapter_dir, declared_classification):
    """Returns a list of violation strings (empty if none)."""
    violations = []
    output_dir = os.path.join(corpus_root, chapter_dir)
    prefix = trust_ledger._derive_prefix(output_dir)
    if prefix is None:
        violations.append(f"{chapter_dir}: declared {declared_classification!r} in "
                           "CORPUS_TRUST_STATUS.md but no recognizable pipeline output "
                           "(*_CHECKPOINT.json etc.) exists in this directory at all.")
        return violations

    # --- Marker filename inventory (Chapter-03-style check).
    canonical_path = protection_marker_path(output_dir)
    canonical_exists = os.path.exists(canonical_path)
    prefixed_conflicts = sorted(
        os.path.basename(m) for m in glob.glob(os.path.join(output_dir, f"*{PROTECTION_MARKER_FILENAME}"))
        if os.path.basename(m) != PROTECTION_MARKER_FILENAME
    )
    if prefixed_conflicts:
        violations.append(
            f"{chapter_dir} [CHAPTER-03-STYLE MARKER DEFECT]: found prefixed marker file(s) "
            f"{prefixed_conflicts} in this directory. The canonical bare filename mutation_guard.py "
            f"and the trust ledger actually check for is {PROTECTION_MARKER_FILENAME!r} -- a prefixed "
            "file is silently ignored by every real protection/classification check, exactly the "
            "Chapter 03 defect."
        )
    if not canonical_exists:
        violations.append(
            f"{chapter_dir}: no canonical {PROTECTION_MARKER_FILENAME} marker found in this "
            "directory."
        )

    # --- Fresh recomputation vs committed ledger.
    fresh_record = trust_ledger.build_chapter_trust_record(output_dir, chapter_dir)
    if fresh_record is None:
        violations.append(f"{chapter_dir}: declared {declared_classification!r} but a fresh "
                           "trust_ledger recomputation returns no record at all for this directory.")
        return violations

    if fresh_record["classification"] != declared_classification:
        violations.append(
            f"{chapter_dir} [LEDGER/RECOMPUTED MISMATCH]: CORPUS_TRUST_STATUS.md declares "
            f"{declared_classification!r}, but a fresh recomputation from current repository "
            f"evidence gives {fresh_record['classification']!r}. Reasons: {fresh_record['reasons']}. "
            "The committed ledger is stale -- regenerate it with generate_corpus_trust_ledger.py "
            "--write --in-place."
        )

    if not fresh_record["trusted_for_downstream_use"]:
        violations.append(
            f"{chapter_dir} [CHAPTER-11-STYLE EVIDENCE DEFECT]: declared "
            f"{declared_classification!r} but fresh trusted_for_downstream_use is False. "
            f"Reasons: {fresh_record['reasons']}"
        )

    if not fresh_record["protection_marker_present"]:
        violations.append(
            f"{chapter_dir}: declared CORPUS_TESTING_READY / trusted, but "
            "protection_marker_present is False (no canonical marker was found by the ledger's own "
            "read_protection_marker() check)."
        )

    if fresh_record.get("retrieval_ready", False) is not False:
        violations.append(
            f"{chapter_dir}: retrieval_ready must always be False for this pipeline (no retrieval "
            f"is implemented) -- got {fresh_record.get('retrieval_ready')!r}."
        )

    # --- Stage 4.6/4.7/8 evidence completeness (explicit re-check, in
    # addition to the classification/trust checks above, so a violation
    # names the exact stage even if trusted_for_downstream_use happens to
    # still read True from a stale cached value somewhere else).
    checkpoint, _ = trust_ledger.corpus_trust.load_checkpoint_for_classification(output_dir, prefix)
    if checkpoint is not None:
        sc = checkpoint.get("stage_completions", {})
        stage_4_6 = sc.get("4.6", {}) or {}
        stage_4_7 = sc.get("4.7", {}) or {}
        if stage_4_6.get("status") != "COMPLETED":
            violations.append(f"{chapter_dir}: Stage 4.6 status is not 'COMPLETED' "
                               f"(got {stage_4_6.get('status')!r}).")
        if "unresolved_completeness_clusters" not in stage_4_7:
            violations.append(
                f"{chapter_dir} [CHAPTER-11-STYLE EVIDENCE DEFECT]: "
                'stage_completions["4.7"]["unresolved_completeness_clusters"] is not present at all.'
            )
        elif stage_4_7.get("unresolved_completeness_clusters") != 0:
            violations.append(f"{chapter_dir}: Stage 4.7 unresolved_completeness_clusters != 0 "
                               f"(got {stage_4_7.get('unresolved_completeness_clusters')!r}).")

        violations.extend(_check_stage6_chunk_count(output_dir, chapter_dir, prefix, checkpoint))
        violations.extend(_check_stage_5_4_persistence(output_dir, chapter_dir, prefix, checkpoint))

    return violations


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus_root", help="Root directory containing chapter subdirectories.")
    args = parser.parse_args(argv)

    # A verifier that checked nothing must not say "all invariants hold" (exit 0).
    if not os.path.isdir(args.corpus_root):
        print(f"ERROR: corpus root does not exist or is not a directory: {args.corpus_root}")
        return 2
    if not os.path.exists(os.path.join(args.corpus_root, "CORPUS_TRUST_STATUS.md")):
        print(f"ERROR: no CORPUS_TRUST_STATUS.md in {args.corpus_root} -- nothing to verify against "
              f"(generate the ledger first).")
        return 2

    declared = _committed_classifications(args.corpus_root)
    trusted_declared = {k: v for k, v in declared.items() if v == "CORPUS_TESTING_READY"}

    all_violations = []
    for chapter_cell, classification in sorted(trusted_declared.items()):
        # chapter_dir cells are the bare directory name in this pipeline's
        # generated ledger rows (see pipeline/stages/trust_ledger.py's render function).
        chapter_dir = chapter_cell
        violations = check_chapter(args.corpus_root, chapter_dir, classification)
        all_violations.extend(violations)

    if not trusted_declared:
        print("No chapters currently declared CORPUS_TESTING_READY in CORPUS_TRUST_STATUS.md.")

    print(f"Checked {len(trusted_declared)} chapter(s) declared CORPUS_TESTING_READY: "
          f"{sorted(trusted_declared.keys())}")

    if all_violations:
        print(f"\n{len(all_violations)} INVARIANT VIOLATION(S) FOUND:\n")
        for v in all_violations:
            print(f"  - {v}")
        return 1

    print("\nAll invariants hold for every currently-trusted chapter.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
