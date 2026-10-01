"""One-off adjudication apply for Chapter 05's Stage 4.5d candidates.

Adjudication reasoning (all 55 candidates -> false_positive, 0 confirmed
corruptions -- see PHASE0_PHASE1_REPORT.md's adjudication log section for
the full per-chunk investigation):

- L2-097 (43 candidates): this chunk's `source_lines: "1045-1058"` frontmatter
  undercounts its real span -- the chunk body includes a full vitamin
  reference-intake table that actually lives at source lines ~1059-1082
  (confirmed via the unique WHO PDF id "9241546123" appearing at line 1082,
  well past the declared "1058" end). The table's numbers are verbatim-
  correct against the real source; only the source_lines METADATA is wrong.
- L2-038 (5 candidates): `source_lines: "455-467"` over-includes a
  subsequent "#### Lifestyle advice" subsection's lines (461-467) that
  aren't part of this chunk's actual body -- confirmed those lines contain
  "Box 5.7", "type 2 diabetes", and "positive strategic encouragement",
  exactly matching the flagged candidates.
- L2-070 (2 candidates): 1 pair is a real content match modulo an
  en-dash-vs-hyphen normalization ("2-4" vs "2\u20134") -- formatting-only,
  not a corruption, matches the evaluation guide's own "formatting-only
  difference" label (not a fidelity failure). The other candidates from
  this chunk were resolved by fixing resolve_source_span()'s discontinuous-
  range bug (see CHANGELOG) before this adjudication pass ran.
- L2-118 (4 candidates): `source_lines: "1301-1305, 1307-1334"` sweeps in
  an entire interleaved box (Box 5.36, "Cause and clinical features of
  scurvy", real lines 1309-1332) that is NOT part of this chunk's actual
  content. Confirmed Box 5.36 IS correctly, separately chunked elsewhere
  (L1 chunk + 4 L2 children: Precipitants/Increased requirement/Dietary
  deficiency/Clinical features, source_lines 1309-1332) -- so this is a
  source_lines metadata bug on L2-118, NOT a coverage gap.
- L2-126 (1 candidate): declared span includes a single stray interleaved
  table-caption line ("Diseases associated with deficiency and excess of
  vitamins and minerals") that isn't part of this chunk's real Iron content
  -- a PDF-extraction interleaving artifact, correctly excluded from the
  chunk body by Stage 4B.

Root cause common to 4 of 5 affected chunks: Stage 4B's source_lines
frontmatter assignment is imprecise (both under- and over-inclusive) on
this chapter -- a real, separate finding worth fixing at the chunking stage
in a future round (affects provenance/traceability, not clinical accuracy
of the chunk bodies themselves, which were verbatim-correct in every case
checked). Not fixed in this pass -- flagged in PHASE0_PHASE1_REPORT.md.

v2.6.3 SAFETY GUARDRAIL: CLASSIFICATION = chapter-specific repair, mutates
existing certified output (ClinicalFidelity.json, Gate.json, Failures.json).
Default invocation (`python apply_ch05_adjudication.py`) is now READ-ONLY --
it computes and prints what the adjudication would produce but does NOT
overwrite the real files. Requires --write --in-place (and --backup, which
this chapter's CORPUS_OUTPUT_PROTECTED.json marker makes mandatory once
that marker exists) to actually mutate. This is a one-off script scoped to
Chapter 05's specific 55-candidate adjudication documented above -- not a
general-purpose tool for other chapters.
"""
import argparse
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from pipeline.stages import stage_4_5d_clinical_fidelity as s45d
from pipeline.stages.mutation_guard import require_authorization_for_in_place_mutation, MutationRefused

OUT_DIR = r"D:\davidson_25_full_pipeline\05"
PREFIX = "Davidson_25_Ch05_Nutritional_factors_in_disease"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--in-place", action="store_true")
    parser.add_argument("--backup", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    fidelity_path = f"{OUT_DIR}\\{PREFIX}_ClinicalFidelity.json"
    gate_path = f"{OUT_DIR}\\{PREFIX}_ClinicalFidelityGate.json"
    fail_path = f"{OUT_DIR}\\{PREFIX}_ClinicalFidelityFailures.json"

    data = json.load(open(fidelity_path, encoding="utf-8"))
    candidates = data["candidates"]

    decisions = {c["candidate_id"]: "false_positive" for c in candidates}
    updated, unmatched = s45d.apply_adjudication_decisions(candidates, decisions)
    print(f"Computed {len(decisions)} decisions, {len(unmatched)} unmatched: {unmatched}")

    gate = s45d.build_clinical_fidelity_gate(updated, s45d.REQUIRED_DETECTORS, "2.6.0", PREFIX)
    gate["context_fallback_used_for_n_chunks"] = 0
    gate["l2_chunks_scanned"] = 139
    confirmed = [c for c in updated if c["severity"] == "CONFIRMED_CORRUPTION"]

    try:
        require_authorization_for_in_place_mutation(
            OUT_DIR, PREFIX, args,
            target_description=f"{PREFIX}'s ClinicalFidelity.json/Gate.json/Failures.json",
        )
    except MutationRefused:
        print("READ-ONLY mode: computed gate verdict "
              f"{gate['verdict']} | unresolved: {gate['unresolved_candidates']} "
              f"| corruptions: {gate['unresolved_corruptions']} -- NOT written to real files. "
              "Re-run with --write --in-place --backup to apply for real.")
        return gate, updated

    import shutil
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for p in (fidelity_path, gate_path, fail_path):
        shutil.copyfile(p, f"{p}.pre-mutation-{ts}.bak")

    json.dump({"candidates": updated}, open(fidelity_path, "w", encoding="utf-8"), indent=2)
    json.dump(gate, open(gate_path, "w", encoding="utf-8"), indent=2)
    json.dump(confirmed, open(fail_path, "w", encoding="utf-8"), indent=2)

    print(f"Gate verdict: {gate['verdict']} | unresolved: {gate['unresolved_candidates']} "
          f"| corruptions: {gate['unresolved_corruptions']}")
    return gate, updated


if __name__ == "__main__":
    main()
