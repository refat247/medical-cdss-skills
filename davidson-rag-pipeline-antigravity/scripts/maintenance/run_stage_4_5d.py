"""Real invocation of Stage 4.5d against a chapter's chunks.md +
REPAIRED_S2.md. This is the logic SKILL.md's Stage 4.5d block wraps
(checkpoint calls added there); kept here as a standalone, directly-runnable
script so it can be used for the Chapter 05 regression run and reused for
future chapters without hand-pasting code into a session.

Usage:
    python run_stage_4_5d.py <OUTPUT_DIR> <PREFIX> [--write] [--in-place]
                              [--backup] [--dry-run]

v2.6.3 SAFETY GUARDRAIL: the CLI (`__main__`) is READ-ONLY / REPORT-ONLY by
default. Without --write, results are computed exactly as before but
written to <OUTPUT_DIR>/.dryrun_stage_4_5d/ instead of overwriting
{PREFIX}_ClinicalFidelity.md/.json/Failures.json/Gate.json in place -- this
is exactly the guardrail added after a real incident during v2.6.2 where
running this script directly against Chapter 05's real output regenerated
fresh, unadjudicated candidates and temporarily reverted a PASSING
corpus-certified gate to BLOCKED (see V2_6_2_STABILIZATION_REPORT.md §14).
--write alone is enough for a chapter with no existing Stage 4.5d outputs
yet. Overwriting EXISTING outputs additionally requires --in-place, and a
corpus-output-protected chapter (CORPUS_OUTPUT_PROTECTED.json present)
additionally requires --backup -- refused otherwise with a clear error.

Does NOT touch the checkpoint -- run via SKILL.md's Stage 4.5d block for the
real checkpointed flow; this script is for direct/regression invocation.

The underlying run_stage_4_5d(out_dir, prefix) function is UNCHANGED for
library/test callers (SKILL.md's checkpointed flow, the Chapter 05
integration regression tests) -- it still writes directly to out_dir,
write=True by default, since those callers already operate inside their
own explicitly-scoped, non-production directories (a tmp_path fixture, or
the checkpointed pipeline's own controlled flow). The safety guardrail
described above applies to the __main__ CLI entry point only, which is the
actual "direct runner against a real chapter" risk this release addresses.
"""
import sys
from pipeline.stages.chunk_blocks import split_chunk_blocks
import io
import os
import re
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pipeline.stages import stage_4_5d_clinical_fidelity as s45d
from pipeline.checkpoint_utils import PIPELINE_VERSION


def _parse_chunks(chunks_text):
    blocks = split_chunk_blocks(chunks_text)
    parsed = []
    for i, b in enumerate(blocks):
        cid = re.search(r'chunk_id:\s*(\S+)', b)
        lvl = re.search(r'chunk_level:\s*(\d)', b)
        df = re.search(r'disease_focus:\s*(.*)', b)
        src = re.search(r'source_lines:\s*"?([^"\n]+)"?', b)
        body_m = re.search(r'^(?:### Chunk[^\n]*\n)?---\n.*?\n---\n?(.*)$', b, re.DOTALL)
        parsed.append({
            "chunk_id": cid.group(1) if cid else '?',
            "level": lvl.group(1) if lvl else None,
            "disease_focus": df.group(1).strip() if df else '',
            "source_lines": src.group(1).strip() if src else '',
            "block": b,
            "body": body_m.group(1).strip() if body_m else '',
            "order": i,
        })
    return parsed


def _l1_span(source_lines):
    """v2.6.5 (CATEGORY D emergency fix): delegates to the canonical
    stages.source_lines_parser module. The previous inline regex here
    (re.match, not even re.findall) matched ONLY a hyphenated range sitting
    at the very start of the string and silently discarded every other
    segment — worse than the other three duplicate parsers, since it
    returned None entirely for a leading single-line value (e.g.
    "1049,1051-1053") even though later segments were well-formed. Returns
    the overall (min_start, max_end) envelope across every parsed segment
    — the correct generalization of "a single (start, end) span" once a
    source_lines value can legitimately contain more than one segment; see
    V2_6_5_EMERGENCY_INTEGRITY_FIX_REPORT.md. Do not reintroduce inline
    range-parsing regex here (see
    tests/test_no_duplicate_source_lines_parser.py)."""
    from pipeline.stages.source_lines_parser import parse_source_lines
    segments = parse_source_lines(source_lines).segments
    if not segments:
        return None
    return (min(s[0] for s in segments), max(s[1] for s in segments))


def _build_source_mapping(out_dir, prefix, *, l2_count, fallback_count, malformed_count):
    """v2.6.3 (requirement 7) — Stage 4.5d relies heavily on source_lines
    for span resolution, but nothing in the gate output used to disclose
    HOW MUCH it actually relied on it, or whether that reliance was ever
    independently precision-checked. This is advisory-only disclosure, not
    a new gate: source_lines_precision_gate_status is always
    "ADVISORY_ONLY" here, and semantic_completeness_claimed is always
    False -- Stage 4.5d's detectors were never able to prove semantic
    completeness (see SKILL.md's known limitations) and this field exists
    so nothing downstream can mistake a clean gate for that stronger claim.

    Pulls precision counts from {prefix}_SourceLinesPrecision.json when
    present (written by run_source_lines_precision.py, a separate advisory
    script -- see its module docstring); when absent, discloses that
    precision was simply never tested rather than guessing or omitting the
    fields entirely.
    """
    precision_path = os.path.join(out_dir, f"{prefix}_SourceLinesPrecision.json")
    precision_tested = os.path.exists(precision_path)
    over_inclusive = under_inclusive = unresolved = None
    if precision_tested:
        try:
            with open(precision_path, encoding="utf-8") as f:
                precision_data = json.load(f)
            results = precision_data.get("results", [])
            over_inclusive = sum(1 for r in results if r.get("verdict") in
                                  ("OVER_INCLUSIVE", "UNDER_AND_OVER_INCLUSIVE"))
            under_inclusive = sum(1 for r in results if r.get("verdict") in
                                   ("UNDER_INCLUSIVE", "UNDER_AND_OVER_INCLUSIVE"))
            unresolved = sum(1 for r in results if r.get("verdict") == "UNRESOLVED")
        except (json.JSONDecodeError, OSError):
            precision_tested = False  # file present but unreadable -- treat as untested, don't guess

    return {
        "chunks_using_source_lines": l2_count - fallback_count,
        "chunks_using_context_fallback": fallback_count,
        "chunks_with_malformed_source_lines": malformed_count,
        "source_lines_precision_gate_status": "ADVISORY_ONLY",
        "semantic_completeness_claimed": False,
        "source_lines_precision_tested": precision_tested,
        "source_lines_over_inclusive_count": over_inclusive,
        "source_lines_under_inclusive_count": under_inclusive,
        "source_lines_unresolved_count": unresolved,
    }


def run_stage_4_5d(out_dir, prefix, write_dir=None):
    """write_dir (v2.6.3): where the 4 output files land. Defaults to
    out_dir (original, pre-2.6.3 behavior -- unchanged for every existing
    library/test caller). The CLI entry point (_cli_main, below) passes a
    report-only temp subdirectory here when the caller hasn't authorized
    an in-place mutation, so results are always computed the same way but
    only land in the real chapter directory when explicitly authorized."""
    write_dir = write_dir or out_dir
    rep_path = os.path.join(out_dir, f"{prefix}_REPAIRED_S2.md")
    chunk_path = os.path.join(out_dir, f"{prefix}_chunks.md")
    from pipeline.stages.stage_4_parse import sanitize_chunk_text
    repaired = sanitize_chunk_text(open(rep_path, encoding='utf-8').read())   # chunks are sanitized by 4B
    chunks_text = open(chunk_path, encoding='utf-8').read()

    parsed = _parse_chunks(chunks_text)
    l1s = [c for c in parsed if c["level"] == "1"]
    l2s = [c for c in parsed if c["level"] == "2"]

    all_candidates = []
    detectors_run = set()

    # Checks 1-10: per L2 chunk, against its resolved source span.
    fallback_count = 0
    malformed_source_lines_count = 0
    for c in l2s:
        span, method = s45d.resolve_source_span(repaired, c["block"])
        if method == "context_fallback":
            fallback_count += 1
            # v2.6.3 (requirement 7): a chunk that HAD a source_lines value
            # but still fell back to context matching means that value was
            # unusable (malformed/unparseable/pointed at nothing resolvable)
            # -- distinct from a chunk that simply never had source_lines at
            # all. Both count toward chunks_using_context_fallback, but only
            # this subset is "malformed" for disclosure purposes.
            if c["source_lines"]:
                malformed_source_lines_count += 1
        cands, scanned_by_check = s45d.run_all_detectors_for_chunk(span, c["body"], c["chunk_id"])
        all_candidates.extend(cands)
        detectors_run.update(scanned_by_check.keys())

    # Check 11: boundary-loss, per L1 section against its child L2 chunks
    # (child = L2 whose source_lines range falls inside the L1's range).
    for l1 in l1s:
        span = _l1_span(l1["source_lines"])
        if not span:
            continue
        lo, hi = span
        children = []
        for c in l2s:
            c_span = _l1_span(c["source_lines"])
            if c_span and lo <= c_span[0] and c_span[1] <= hi:
                children.append({"chunk_id": c["chunk_id"], "body": c["body"],
                                  "disease_focus": c["disease_focus"], "order": c["order"],
                                  "source_lines": c_span})
        if children:
            # v2.6.2: pass repaired_s2_text so detect_boundary_loss can
            # actually reach INTENTIONAL_SECTION_SPLIT from real heading
            # evidence, not just AMBIGUOUS/SAFE/CRITICAL.
            cands, _scanned = s45d.detect_boundary_loss(l1["body"], children, repaired_s2_text=repaired, scope=l1["chunk_id"])
            all_candidates.extend(cands)
    detectors_run.add("boundary_loss")
    # one global uniqueness pass: ids are (check, chunk_id, ordinal, hash); duplicates across sections used to collide
    s45d.assign_candidate_ids(all_candidates)

    gate = s45d.build_clinical_fidelity_gate(
        all_candidates, sorted(detectors_run), PIPELINE_VERSION, prefix,
    )
    gate["context_fallback_used_for_n_chunks"] = fallback_count
    gate["l2_chunks_scanned"] = len(l2s)
    gate["source_mapping"] = _build_source_mapping(
        out_dir, prefix, l2_count=len(l2s), fallback_count=fallback_count,
        malformed_count=malformed_source_lines_count,
    )

    md_path = os.path.join(write_dir, f"{prefix}_ClinicalFidelity.md")
    json_path = os.path.join(write_dir, f"{prefix}_ClinicalFidelity.json")
    fail_path = os.path.join(write_dir, f"{prefix}_ClinicalFidelityFailures.json")
    gate_path = os.path.join(write_dir, f"{prefix}_ClinicalFidelityGate.json")

    by_check = {}
    for c in all_candidates:
        by_check.setdefault(c["check"], []).append(c)

    md_lines = [f"# Stage 4.5d Clinical Fidelity — {prefix}",
                f"L2 chunks scanned: {len(l2s)} | Candidates found: {len(all_candidates)}",
                f"Context-fallback used (no source_lines): {fallback_count} chunk(s)",
                f"Detectors run: {sorted(detectors_run)}",
                f"VERDICT: {gate['verdict']}", ""]
    for check in s45d.REQUIRED_DETECTORS:
        items = by_check.get(check, [])
        md_lines.append(f"## {check} ({len(items)} candidate(s))")
        for c in items[:20]:
            md_lines.append(f"  - [{c['candidate_id']}] {c['kind']}: "
                             f"source={c['source_value']!r} chunk={c['chunk_value']!r}")
        if len(items) > 20:
            md_lines.append(f"  ... and {len(items) - 20} more")
    from pipeline.checkpoint_utils import format_markdown_provenance_header, attach_json_provenance
    prov_md = format_markdown_provenance_header(rep_path or prefix, "4.5d")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(prov_md + '\n'.join(md_lines))

    cand_dict = attach_json_provenance({"candidates": all_candidates}, prefix, "4.5d")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(cand_dict, f, indent=2)

    confirmed_failures = [c for c in all_candidates if c.get("severity") == "CONFIRMED_CORRUPTION"]
    fail_dict = attach_json_provenance({"failures": confirmed_failures}, prefix, "4.5d")
    with open(fail_path, 'w', encoding='utf-8') as f:
        json.dump(fail_dict, f, indent=2)

    gate = attach_json_provenance(gate, prefix, "4.5d")
    with open(gate_path, 'w', encoding='utf-8') as f:
        json.dump(gate, f, indent=2)

    print(f"Stage 4.5d -> {gate_path} | VERDICT: {gate['verdict']} | "
          f"candidates: {len(all_candidates)} | unresolved: {gate['unresolved_candidates']}")
    return gate, all_candidates


def _cli_main(argv):
    import argparse
    from pipeline.stages.mutation_guard import (
        add_mutation_cli_args, is_protected, require_authorization_for_in_place_mutation,
        MutationRefused,
    )

    parser = argparse.ArgumentParser(
        description="Run Stage 4.5d clinical fidelity detection against a chapter's "
                     "chunks.md + REPAIRED_S2.md. Read-only/report-only by default (v2.6.3).",
    )
    parser.add_argument("out_dir", help="Chapter output directory (contains REPAIRED_S2.md, chunks.md).")
    parser.add_argument("prefix", help="Chapter file prefix, e.g. Davidson_25_Ch05_Nutritional_factors_in_disease.")
    add_mutation_cli_args(parser)
    args = parser.parse_args(argv)

    out_dir, prefix = args.out_dir, args.prefix
    existing_outputs = [
        os.path.join(out_dir, f"{prefix}_ClinicalFidelity.md"),
        os.path.join(out_dir, f"{prefix}_ClinicalFidelity.json"),
        os.path.join(out_dir, f"{prefix}_ClinicalFidelityFailures.json"),
        os.path.join(out_dir, f"{prefix}_ClinicalFidelityGate.json"),
    ]
    outputs_already_exist = any(os.path.exists(p) for p in existing_outputs)

    if outputs_already_exist:
        try:
            require_authorization_for_in_place_mutation(
                out_dir, prefix, args,
                target_description=f"{prefix}'s existing Stage 4.5d outputs "
                                    f"(ClinicalFidelity.md/.json, Failures.json, Gate.json)",
            )
        except MutationRefused:
            print("Refusing to overwrite existing Stage 4.5d outputs. "
                  "Running in READ-ONLY mode instead -- results below are computed but NOT "
                  "written to the real output files. Re-run with --write "
                  "(and --in-place, and --backup if this chapter is protected) to apply for real.")
            report_dir = os.path.join(out_dir, ".dryrun_stage_4_5d")
            os.makedirs(report_dir, exist_ok=True)
            gate, candidates = run_stage_4_5d(out_dir, prefix, write_dir=report_dir)
            print(f"[DRY RUN] Stage 4.5d results written to {report_dir} only -- "
                  f"real chapter outputs untouched.")
            return

        # Authorized (write + in_place + backup-if-protected all present) --
        # back up the existing outputs before run_stage_4_5d overwrites them
        # in place (spec step 1: "create a timestamped backup" before any
        # in-place mutation of an existing output).
        import shutil as _shutil
        from datetime import datetime, timezone as _tz
        ts = datetime.now(_tz.utc).strftime("%Y%m%dT%H%M%SZ")
        for p in existing_outputs:
            if os.path.exists(p):
                _shutil.copyfile(p, f"{p}.pre-mutation-{ts}.bak")
        print(f"Backed up {sum(1 for p in existing_outputs if os.path.exists(p))} "
              f"existing Stage 4.5d output file(s) before in-place mutation.")
    elif not args.write:
        print("No existing Stage 4.5d outputs found -- this would be a first-time run. "
              "Still refusing without --write (v2.6.3 default is always read-only unless "
              "explicitly authorized). Writing results to a report-only location instead.")
        report_dir = os.path.join(out_dir, ".dryrun_stage_4_5d")
        os.makedirs(report_dir, exist_ok=True)
        gate, candidates = run_stage_4_5d(out_dir, prefix, write_dir=report_dir)
        print(f"[DRY RUN] Stage 4.5d results written to {report_dir} only.")
        return

    run_stage_4_5d(out_dir, prefix)


if __name__ == "__main__":
    # v2.6.2: moved out of module scope (was unconditional on import) --
    # rebinding sys.stdout at IMPORT time broke repeated imports under
    # pytest (its capture fixture swaps stdout per-test; a module-level
    # rebind pins a reference to whatever buffer existed at first import,
    # which pytest later closes). Only needed for direct CLI invocation's
    # Windows-console Unicode handling, so scope it to that path only.
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    _cli_main(sys.argv[1:])
