"""v2.6.3 — immutable Chapter 05 adjudication manifest + validation
(Safety Guardrails release, requirements 4 & 5).

Before this module existed, the only record of Stage 4.5d's Chapter 05
adjudication was a Python script (`scripts/chapter_repairs/apply_ch05_adjudication.py`) containing
a blanket `{c["candidate_id"]: "false_positive" for c in candidates}`
comprehension plus prose comments explaining the reasoning. That is
executable code, not an independently auditable evidence artifact -- it
proves what the script DOES, not what a reviewer actually decided and why,
and nothing stops it from silently applying "false_positive" to a
candidate set that has since changed (a different scan, a different
chapter, a regenerated chunk set after an unrelated edit).

The manifest (see `tests/fixtures/ch05_regression/clinical_fidelity_adjudication_manifest.json`)
is the sanctioned replacement: one JSON record per candidate, each with an
explicit decision AND a non-empty rationale, locked to the exact source
file, chunks file, and candidate set it was reviewed against via sha256
hashes. `validate_manifest()` refuses to let decisions be replayed against
anything else. `apply_validated_manifest()` never partially applies an
invalid manifest -- validation failure means zero decisions are applied,
full stop.

IMPORTANT — what this module does NOT prove: a green `validate_manifest()`
result proves the manifest's decisions are being applied to the SAME
candidate set they were reviewed against (schema/hash/count/ID integrity).
It does NOT independently verify that the recorded clinical/editorial
DECISIONS themselves are correct -- that judgment call is the manifest
author's, recorded in each candidate's `rationale` field for human/future
review, not re-derived or re-validated by this module. See the manifest's
own `reviewer_role` field for exactly who made that call and in what
capacity -- do not infer a credential this module does not assert.
"""
import hashlib
import json

from pipeline.stages.stage_4_5d_clinical_fidelity import apply_adjudication_decisions, DECISION_VALUES

SCHEMA_VERSION = "1.0"
REQUIRED_CANDIDATE_FIELDS = (
    "candidate_id", "detector", "chunk_id", "mismatch_kind",
    "source_value", "chunk_value", "source_context", "chunk_context",
    "decision", "rationale", "re_verified",
)
REQUIRED_MANIFEST_FIELDS = (
    "schema_version", "chapter", "pipeline_version", "source_sha256",
    "chunks_sha256", "candidate_set_sha256", "review_status", "reviewed_at",
    "reviewer_role", "candidates",
)

# Identity fields used to compute the candidate-set hash -- deliberately a
# SUBSET of a raw Stage 4.5d candidate dict (which also carries severity/
# status_label/decision once adjudicated). Hashing only the pre-adjudication
# identity fields means the same hash is reproducible whether the candidate
# list has already been decided or not, so a manifest can be validated
# against either a fresh (undecided) Stage 4.5d run or an already-decided
# one without the hash drifting just because adjudication ran.
_IDENTITY_FIELDS = ("candidate_id", "chunk_id", "source_value", "chunk_value")


def _candidate_identity(candidate):
    """Normalizes field-name differences between a raw Stage 4.5d candidate
    dict (`check`, `kind`) and a manifest candidate dict (`detector`,
    `mismatch_kind`) so both shapes hash identically for the same
    underlying candidate."""
    detector = candidate.get("detector", candidate.get("check"))
    mismatch_kind = candidate.get("mismatch_kind", candidate.get("kind"))
    return {
        "candidate_id": candidate.get("candidate_id"),
        "detector": detector,
        "chunk_id": candidate.get("chunk_id"),
        "mismatch_kind": mismatch_kind,
        "source_value": candidate.get("source_value"),
        "chunk_value": candidate.get("chunk_value"),
    }


def build_candidate_set_hash(candidates):
    """Deterministic sha256 over the candidate set's IDENTITY fields only
    (never severity/decision/status_label/rationale -- those are the
    manifest's own payload, not part of "which scan is this"). Sorted by
    candidate_id so hash is independent of list order. Accepts either raw
    Stage 4.5d candidates or manifest-shaped candidates (see
    _candidate_identity)."""
    identities = sorted((_candidate_identity(c) for c in candidates),
                         key=lambda d: d["candidate_id"] or "")
    canonical = json.dumps(identities, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _error(errors, msg):
    errors.append(msg)


def validate_manifest(manifest, *, source_sha256, chunks_sha256, current_candidates,
                       legacy_id_map=None):
    """Validates `manifest` against the CURRENT evidence: the chapter's
    real source file hash, real chunks file hash, and the candidate set a
    fresh Stage 4.5d run actually produced (`current_candidates`, raw
    Stage 4.5d shape -- `check`/`kind`, not yet adjudicated).

    `legacy_id_map` (optional): {old_candidate_id: new_candidate_id} for
    candidates whose ID scheme changed between when the manifest was
    written and now. A manifest candidate_id found in this map is treated
    as referring to the mapped current ID -- but only ever explicitly, via
    this parameter; never inferred by fuzzy-matching content. Every
    substitution actually used is recorded in the returned result's
    `legacy_ids_converted` list so it's visible in whatever log consumes
    this, not silently applied.

    Returns a structured result dict:
    {"valid": bool, "errors": [...], "warnings": [...],
     "legacy_ids_converted": [...], "checked": {...}}
    Never raises for a validation failure -- only for a fundamentally
    malformed manifest (not a dict, candidates not a list) that isn't a
    validation-domain concern at all.
    """
    if not isinstance(manifest, dict):
        raise TypeError("manifest must be a dict")
    if not isinstance(manifest.get("candidates"), list):
        raise TypeError("manifest['candidates'] must be a list")

    errors = []
    warnings = []
    legacy_ids_converted = []
    legacy_id_map = legacy_id_map or {}

    for field in REQUIRED_MANIFEST_FIELDS:
        if field not in manifest:
            _error(errors, f"manifest missing required field: {field!r}")

    if manifest.get("schema_version") != SCHEMA_VERSION:
        _error(errors, f"schema_version {manifest.get('schema_version')!r} != "
                        f"supported {SCHEMA_VERSION!r}")

    if manifest.get("source_sha256") != source_sha256:
        _error(errors, f"source_sha256 mismatch: manifest has "
                        f"{manifest.get('source_sha256')!r}, current source is {source_sha256!r} "
                        f"-- this manifest was reviewed against a DIFFERENT source file.")

    if manifest.get("chunks_sha256") != chunks_sha256:
        _error(errors, f"chunks_sha256 mismatch: manifest has "
                        f"{manifest.get('chunks_sha256')!r}, current chunks are {chunks_sha256!r} "
                        f"-- this manifest was reviewed against a DIFFERENT chunk set.")

    current_hash = build_candidate_set_hash(current_candidates)
    if manifest.get("candidate_set_sha256") != current_hash:
        _error(errors, f"candidate_set_sha256 mismatch: manifest has "
                        f"{manifest.get('candidate_set_sha256')!r}, current candidate set hashes to "
                        f"{current_hash!r} -- refusing to replay decisions onto a DIFFERENT scan.")

    manifest_candidates = manifest.get("candidates", [])
    current_ids = {c.get("candidate_id") for c in current_candidates}

    seen_ids = set()
    for mc in manifest_candidates:
        cid = mc.get("candidate_id")
        if cid in seen_ids:
            _error(errors, f"duplicate candidate_id in manifest: {cid!r}")
        seen_ids.add(cid)

        for field in REQUIRED_CANDIDATE_FIELDS:
            if field not in mc:
                _error(errors, f"candidate {cid!r} missing required field: {field!r}")
                continue

        decision = mc.get("decision")
        if decision not in DECISION_VALUES:
            _error(errors, f"candidate {cid!r} has invalid decision: {decision!r} "
                            f"(must be one of {sorted(DECISION_VALUES)})")

        rationale = mc.get("rationale")
        if not rationale or not str(rationale).strip():
            _error(errors, f"candidate {cid!r} has a blank/missing rationale")

        if decision == "confirmed_corruption" and "re_verified" not in mc:
            _error(errors, f"candidate {cid!r} is confirmed_corruption but has no "
                            f"re_verified status recorded")
        if decision == "confirmed_corruption" and mc.get("re_verified") is not True:
            warnings.append(f"candidate {cid!r} is confirmed_corruption and NOT YET "
                             f"re-verified (re_verified={mc.get('re_verified')!r}) -- "
                             f"still an open/unresolved corruption, correctly so if the "
                             f"fix hasn't landed yet.")

        resolved_cid = cid
        if cid not in current_ids and cid in legacy_id_map:
            mapped = legacy_id_map[cid]
            if mapped in current_ids:
                legacy_ids_converted.append({"legacy_id": cid, "converted_to": mapped})
                resolved_cid = mapped
            else:
                _error(errors, f"legacy_id_map maps {cid!r} -> {mapped!r}, but {mapped!r} "
                                f"is not in the current candidate set either")

        if resolved_cid not in current_ids:
            _error(errors, f"manifest candidate_id {cid!r} does not match any candidate in "
                            f"the current scan (unknown/extra candidate, or a stale ID with no "
                            f"legacy_id_map entry)")

    manifest_ids_resolved = set()
    for mc in manifest_candidates:
        cid = mc.get("candidate_id")
        resolved = cid
        for conv in legacy_ids_converted:
            if conv["legacy_id"] == cid:
                resolved = conv["converted_to"]
        manifest_ids_resolved.add(resolved)

    missing_decisions = current_ids - manifest_ids_resolved
    if missing_decisions:
        _error(errors, f"{len(missing_decisions)} current candidate(s) have no decision in "
                        f"the manifest: {sorted(missing_decisions)}")

    if len(manifest_candidates) != len(current_candidates):
        warnings.append(f"manifest has {len(manifest_candidates)} candidate(s), current scan "
                         f"has {len(current_candidates)} -- counts differ (see missing/unknown "
                         f"errors above for specifics, if any).")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "legacy_ids_converted": legacy_ids_converted,
        "checked": {
            "source_sha256_ok": manifest.get("source_sha256") == source_sha256,
            "chunks_sha256_ok": manifest.get("chunks_sha256") == chunks_sha256,
            "candidate_set_sha256_ok": manifest.get("candidate_set_sha256") == current_hash,
            "candidate_count_manifest": len(manifest_candidates),
            "candidate_count_current": len(current_candidates),
        },
    }


def apply_validated_manifest(manifest, current_candidates, *, source_sha256, chunks_sha256,
                              legacy_id_map=None):
    """Validates first; applies decisions to `current_candidates` (mutates
    in place, same contract as apply_adjudication_decisions) ONLY if valid.
    An invalid manifest results in ZERO decisions applied -- never a
    partial application of the ones that happened to check out.

    Returns (updated_candidates_or_None, validation_result). When
    validation_result["valid"] is False, the first element is the
    ORIGINAL, unmodified `current_candidates` (still a valid list to work
    with, just not adjudicated) -- never None and never partially mutated,
    so a careless caller that forgets to check ["valid"] still can't ship
    a half-applied manifest silently.
    """
    result = validate_manifest(
        manifest, source_sha256=source_sha256, chunks_sha256=chunks_sha256,
        current_candidates=current_candidates, legacy_id_map=legacy_id_map,
    )
    if not result["valid"]:
        return current_candidates, result

    legacy_id_map = legacy_id_map or {}
    decisions = {}
    rationale_by_id = {}
    re_verified_by_id = {}
    for mc in manifest["candidates"]:
        cid = mc["candidate_id"]
        resolved_cid = cid
        for conv in result["legacy_ids_converted"]:
            if conv["legacy_id"] == cid:
                resolved_cid = conv["converted_to"]
        decisions[resolved_cid] = mc["decision"]
        rationale_by_id[resolved_cid] = mc["rationale"]
        re_verified_by_id[resolved_cid] = mc.get("re_verified", False)

    updated, unmatched = apply_adjudication_decisions(current_candidates, decisions)
    if unmatched:
        # Should be unreachable given validate_manifest() already confirmed
        # every ID resolves -- if it ever fires, treat as a hard integrity
        # bug rather than silently proceeding with a partial application.
        raise RuntimeError(f"apply_validated_manifest: manifest passed validation but "
                            f"{len(unmatched)} decision(s) still failed to apply: {unmatched}")

    by_id = {c["candidate_id"]: c for c in updated}
    for cid, rationale in rationale_by_id.items():
        by_id[cid]["rationale"] = rationale
        by_id[cid]["re_verified"] = re_verified_by_id[cid]

    return updated, result
