#!/usr/bin/env python3
"""Build the reader review packet from scanner output and one semantic review.

The model writes only the bounded semantic-review JSON. This program validates
that review against the untouched scanner inventory, merges decisions by
scan-local control ID, escapes untrusted text, and renders every reader file.
It never reads the audited source tree and never applies a proposed change.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import html
import json
import os
import re
import shutil
import stat
import sys
import tempfile
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

# Running the shipped black-box tool should not modify its installed package.
sys.dont_write_bytecode = True

from render_harness_map import (
    DECISION_LABELS,
    group_setup_stations,
    markdown_text,
    render_html,
    render_markdown,
)


SCHEMA_VERSION = "1.0"
MAX_INPUT_BYTES = 25_000_000
MAX_REVIEW_BYTES = 1_000_000
MAX_QUICK_DECISIONS = 50
MAX_MAINTAINER_DECISIONS = 500
MAX_UNREVIEWED_CONTROLS = 5_000
MAX_COVERAGE_GAPS = 50
MAX_MODEL_RECOMMENDATIONS = 20

EXPECTED_SCANNER_SAFETY = {
    "audited_text_treatment": "UNTRUSTED_DATA",
    "target_writes": False,
    "network_access": False,
    "symlink_traversal": False,
    "content_excerpts_emitted": False,
    "secret_paths_recorded": False,
}

DECISION_CODES = frozenset(DECISION_LABELS)
EVIDENCE_STATES = frozenset({
    "VERIFIED",
    "USER_REPORTED",
    "INFERRED",
    "INACCESSIBLE",
    "NOT_APPLICABLE",
})
REVIEW_MODES = frozenset({"QUICK_CHECK", "MAINTAINER_AUDIT"})
EDITIONS = frozenset({"CLAUDE", "CODEX"})

REVIEW_FIELDS = frozenset({
    "schema_version",
    "edition",
    "review_mode",
    "baseline",
    "runtime",
    "profile_date",
    "semantic_files_reviewed",
    "decisions",
    "unreviewed_control_ids",
    "coverage_gaps",
    "shared_core",
    "model_recommendations",
})
DECISION_FIELDS = frozenset({
    "control_id",
    "reader_name",
    "decision",
    "evidence_state",
    "current_effect",
    "proposed_change",
    "reason",
    "must_survive",
    "risk_if_wrong",
    "rollback",
})
GAP_FIELDS = frozenset({"area", "evidence_state", "detail"})
RECOMMENDATION_FIELDS = frozenset({
    "recommendation",
    "status",
    "evidence_state",
    "evidence",
    "why_here",
    "would_disprove",
})

PRIVATE_PATH_PATTERNS = (
    re.compile(r"(?i)(?<![A-Za-z0-9:/])/(?:[A-Za-z0-9._~-]+/)+[A-Za-z0-9._~-]+"),
    re.compile(r"(?i)(?<![A-Za-z0-9:/])/(?:Users|home|root|private|tmp|var|Volumes|mnt|opt|etc|srv|Library|Applications|System|workspace|workspaces|data)\b"),
    re.compile(r"(?i)(?<![A-Za-z0-9])~/(?:[^\s<>\"'|]*)?"),
    re.compile(r"(?i)\b[A-Z]:[\\/][^\s<>\"'|]*"),
    re.compile(r"(?i)(?<![\\])\\\\[^\\\s]+\\[^\s<>\"'|]*"),
)

SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----", re.I),
    re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{16,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}\b", re.I),
    re.compile(
        r"(?i)\b(?:api[_-]?key|secret|token|password|passwd|client[_-]?secret|access[_-]?key[_-]?id)\s*[:=]\s*[\"']?[^\s\"']{8,}"
    ),
)

ACTIVE_PAYLOAD_PATTERNS = (
    re.compile(r"<\s*/?\s*[A-Za-z][^>]*>"),
    re.compile(r"!?\[[^\]\n]*\]\([^\)\n]+\)"),
    re.compile(r"(?m)^\s{0,3}#{1,6}\s+\S"),
    re.compile(r"(?i)\b(?:https?|ftp|file|mailto|javascript|data|vbscript|vscode|command|shell):(?:/{0,2})\S+"),
)


class PacketError(ValueError):
    """Raised when the packet inputs violate the public release contract."""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def derive_review_id(scope_hash: str, map_hash: str) -> str:
    """Bind an approval namespace to the two untouched scanner baselines."""
    return f"HARNESS-{map_hash[:10].upper()}-{scope_hash[:10].upper()}"


def proposal_digest(item: dict[str, Any], map_hash: str, review_id: str) -> str:
    """Bind the exact proposal to its review namespace and map baseline."""
    canonical = json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(
        review_id.encode("ascii") + b"\x00" + map_hash.encode("ascii") + b"\x00" + canonical
    ).hexdigest()


def derive_change_id(item: dict[str, Any], map_hash: str, review_id: str) -> str:
    """Bind one 128-bit approval ID to the exact proposal and review."""
    return f"CHANGE-{proposal_digest(item, map_hash, review_id)[:32].upper()}"


def read_json(path: Path, maximum_bytes: int, label: str) -> tuple[bytes, dict[str, Any]]:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0)
    no_follow = getattr(os, "O_NOFOLLOW", None)
    if no_follow is None:
        raise PacketError("this platform cannot safely open packet inputs without following links")
    flags |= no_follow
    descriptor: int | None = None
    try:
        descriptor = os.open(path, flags)
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise PacketError(f"{label} must be a regular file")
        if metadata.st_size > maximum_bytes:
            raise PacketError(f"{label} exceeds the {maximum_bytes}-byte limit")
        chunks: list[bytes] = []
        remaining = maximum_bytes + 1
        while remaining:
            chunk = os.read(descriptor, min(1_048_576, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
        if len(payload) > maximum_bytes:
            raise PacketError(f"{label} grew beyond the {maximum_bytes}-byte limit while being read")
    except OSError as exc:
        raise PacketError(f"{label} could not be read ({exc.__class__.__name__})") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
    try:
        decoded = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PacketError(f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(decoded, dict):
        raise PacketError(f"{label} must contain one JSON object")
    return payload, decoded


def private_paths(value: str) -> list[str]:
    matches: list[str] = []
    for pattern in PRIVATE_PATH_PATTERNS:
        matches.extend(match.group(0) for match in pattern.finditer(value))
    return matches


def first_private_path(value: object) -> str | None:
    if isinstance(value, str):
        found = private_paths(value)
        return found[0] if found else None
    if isinstance(value, dict):
        for key, item in value.items():
            found = first_private_path(key) or first_private_path(item)
            if found:
                return found
    if isinstance(value, list):
        for item in value:
            found = first_private_path(item)
            if found:
                return found
    return None


def review_strings(value: object) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from review_strings(key)
            yield from review_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from review_strings(item)


def reject_unsafe_review_text(review: dict[str, Any]) -> None:
    for value in review_strings(review):
        if private_paths(value):
            raise PacketError("semantic review contains an absolute private path")
        if any(pattern.search(value) for pattern in SECRET_PATTERNS):
            raise PacketError("semantic review contains secret-like material")
        if any(pattern.search(value) for pattern in ACTIVE_PAYLOAD_PATTERNS):
            raise PacketError("semantic review contains active markup or a URI payload")


def path_is_within(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def validate_locations(
    target_root: Path,
    receipt_path: Path,
    scope_path: Path,
    map_path: Path,
    review_path: Path,
    output_dir: Path,
) -> tuple[Path, Path, Path, Path, Path, Path]:
    if target_root.is_symlink():
        raise PacketError("target root must not be a symlink")
    target = target_root.expanduser().resolve()
    if not target.is_dir():
        raise PacketError("target root must be an existing directory")

    raw_inputs = tuple(
        path.expanduser().absolute()
        for path in (receipt_path, scope_path, map_path, review_path)
    )
    resolved_inputs = tuple(path.resolve() for path in raw_inputs)
    if len(set(resolved_inputs)) != len(resolved_inputs):
        raise PacketError("scan receipt, scope, map, and semantic review must be different files")
    output = output_dir.expanduser().resolve(strict=False)
    if path_is_within(output, target):
        raise PacketError("packet output must be outside the audited target")
    if output.exists() or output.is_symlink():
        raise PacketError("packet output must not already exist")
    for label, path in zip(
        ("scan receipt", "scope", "map", "semantic review"), resolved_inputs, strict=True
    ):
        if path_is_within(path, target):
            raise PacketError(f"{label} output must be outside the audited target")
        if path_is_within(path, output):
            raise PacketError(f"packet output collides with the {label} input")
    return target, raw_inputs[0], raw_inputs[1], raw_inputs[2], raw_inputs[3], output


def require_exact_fields(value: object, required: frozenset[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PacketError(f"{label} must be an object")
    actual = frozenset(value)
    missing = sorted(required - actual)
    extra = sorted(actual - required)
    if missing:
        raise PacketError(f"{label} is missing fields: {', '.join(missing)}")
    if extra:
        raise PacketError(f"{label} has unsupported fields: {', '.join(extra)}")
    return value


def require_string(value: object, label: str, *, maximum: int, pattern: str | None = None) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PacketError(f"{label} must be a non-empty string")
    if len(value) > maximum or any(ord(character) < 32 and character not in "\n\t\r" for character in value):
        raise PacketError(f"{label} must be {maximum} characters or fewer and contain no control bytes")
    if pattern and re.fullmatch(pattern, value) is None:
        raise PacketError(f"{label} has an invalid format")
    return value


def require_enum(value: object, allowed: frozenset[str], label: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise PacketError(f"{label} must be one of: {', '.join(sorted(allowed))}")
    return value


def require_list(value: object, label: str, maximum: int) -> list[Any]:
    if not isinstance(value, list):
        raise PacketError(f"{label} must be an array")
    if len(value) > maximum:
        raise PacketError(f"{label} exceeds its {maximum}-item limit")
    return value


def runtime_value(runtime: object, field: str) -> tuple[str, str]:
    if not isinstance(runtime, dict):
        raise PacketError("scanner runtime metadata is missing")
    item = runtime.get(field)
    if not isinstance(item, dict):
        raise PacketError(f"scanner runtime {field} metadata is missing")
    value = require_string(item.get("value"), f"scanner runtime {field}", maximum=160)
    evidence = require_enum(item.get("evidence_state"), EVIDENCE_STATES, f"scanner runtime {field} evidence")
    return value, evidence


def validate_relative_source_path(value: object, label: str) -> str:
    path = require_string(value, label, maximum=1_000)
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts or "\\" in path or path in {"", "."}:
        raise PacketError(f"{label} must be a target-relative scanner path")
    return path


def validate_scanner_inputs(
    scope: dict[str, Any], inventory: dict[str, Any], target_root: Path
) -> dict[str, dict[str, Any]]:
    if first_private_path(scope) or first_private_path(inventory):
        raise PacketError("scanner input contains a private absolute path; rescan with the public scanner")
    if scope.get("schema_version") != SCHEMA_VERSION or inventory.get("schema_version") != SCHEMA_VERSION:
        raise PacketError(f"scanner inputs must use schema version {SCHEMA_VERSION}")
    scan_id = scope.get("scan_id")
    if not isinstance(scan_id, str) or re.fullmatch(r"scan-[a-f0-9]{32}", scan_id) is None:
        raise PacketError("scope input is missing a valid scanner-generated scan ID")
    if inventory.get("scan_id") != scan_id:
        raise PacketError("scope and map scan IDs do not match")
    for field in ("generated_at", "target", "reported_runtime", "safety", "coverage", "counts", "blind_spots"):
        if scope.get(field) != inventory.get(field):
            raise PacketError(f"scope and map {field.replace('_', ' ')} records do not match")
    if scope.get("safety") != EXPECTED_SCANNER_SAFETY:
        raise PacketError("scanner safety receipt does not match the immutable safe contract")
    target = scope.get("target")
    if not isinstance(target, dict):
        raise PacketError("scanner target receipt is missing")
    if target.get("label") != target_root.name or target.get("absolute_path_emitted") is not False:
        raise PacketError("target root does not match the scanner target receipt")
    if "root_fingerprint" in target:
        raise PacketError("public scanner output must not contain a path-derived verifier")
    if inventory.get("decisions") != []:
        raise PacketError("map input is already enriched; supply the untouched scanner inventory JSON")
    setup = inventory.get("setup_map")
    if not isinstance(setup, dict) or not isinstance(setup.get("controls"), list):
        raise PacketError("map input must contain setup_map.controls")
    counts = scope.get("counts")
    summary = setup.get("summary")
    if not isinstance(counts, dict) or not isinstance(summary, dict):
        raise PacketError("scanner counts or setup summary are missing")
    if counts.get("visible_controls") != summary.get("visible_controls"):
        raise PacketError("scanner visible-control counts do not match")
    if counts.get("inspected_bytes") != summary.get("inspected_bytes"):
        raise PacketError("scanner inspected-byte counts do not match")
    if summary.get("undecided_controls") != counts.get("visible_controls"):
        raise PacketError("untouched scanner map must leave every visible control undecided")

    controls: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(setup["controls"]):
        if not isinstance(item, dict):
            raise PacketError(f"scanner control {index} must be an object")
        control_id = require_string(item.get("id"), f"scanner control {index} id", maximum=160)
        if control_id in controls:
            raise PacketError(f"duplicate scanner control ID: {control_id}")
        validate_relative_source_path(item.get("path"), f"scanner control {control_id} path")
        digest = item.get("sha256")
        if not isinstance(digest, str) or re.fullmatch(r"[a-f0-9]{64}", digest) is None:
            raise PacketError(f"scanner control {control_id} is missing a valid SHA-256 baseline")
        decision = item.get("decision")
        if not isinstance(decision, dict) or decision.get("status") != "UNDECIDED":
            raise PacketError("map input has semantic control decisions; supply the untouched scanner inventory JSON")
        controls[control_id] = item
    return controls


def validate_local_scan_receipt(
    receipt: dict[str, Any],
    target_root: Path,
    scope: dict[str, Any],
    scope_hash: str,
    map_hash: str,
) -> None:
    fields = frozenset({
        "schema_version",
        "scan_id",
        "generated_at",
        "target_root",
        "scope_sha256",
        "map_sha256",
        "safety",
    })
    require_exact_fields(receipt, fields, "local scan receipt")
    if receipt["schema_version"] != SCHEMA_VERSION:
        raise PacketError("local scan receipt schema version does not match")
    if receipt["scan_id"] != scope.get("scan_id"):
        raise PacketError("local scan receipt and scanner outputs have different scan IDs")
    if receipt["generated_at"] != scope.get("generated_at"):
        raise PacketError("local scan receipt and scope timestamps do not match")
    if receipt["target_root"] != str(target_root):
        raise PacketError("target root does not match the local scan receipt")
    if receipt["scope_sha256"] != scope_hash or receipt["map_sha256"] != map_hash:
        raise PacketError("local scan receipt does not match the scanner file hashes")
    if receipt["safety"] != EXPECTED_SCANNER_SAFETY:
        raise PacketError("local scan receipt safety does not match the immutable safe contract")


def validate_coverage_gap(value: object, index: int) -> dict[str, Any]:
    item = require_exact_fields(value, GAP_FIELDS, f"coverage_gaps[{index}]")
    require_string(item["area"], f"coverage_gaps[{index}].area", maximum=160)
    require_enum(item["evidence_state"], EVIDENCE_STATES, f"coverage_gaps[{index}].evidence_state")
    require_string(item["detail"], f"coverage_gaps[{index}].detail", maximum=1_000)
    return item


def validate_review(
    review: dict[str, Any],
    controls: dict[str, dict[str, Any]],
    scope: dict[str, Any],
    scope_hash: str,
    map_hash: str,
) -> None:
    require_exact_fields(review, REVIEW_FIELDS, "semantic review")
    if review["schema_version"] != SCHEMA_VERSION:
        raise PacketError(f"semantic review must use schema version {SCHEMA_VERSION}")
    require_enum(review["edition"], EDITIONS, "edition")
    mode = require_enum(review["review_mode"], REVIEW_MODES, "review_mode")

    baseline = require_exact_fields(review["baseline"], frozenset({"scope_sha256", "map_sha256"}), "baseline")
    if baseline["scope_sha256"] != scope_hash:
        raise PacketError("semantic review scope baseline hash does not match the scanner file")
    if baseline["map_sha256"] != map_hash:
        raise PacketError("semantic review map baseline hash does not match the scanner file")

    runtime = require_exact_fields(
        review["runtime"],
        frozenset({"surface", "surface_evidence_state", "model", "model_evidence_state"}),
        "runtime",
    )
    scanner_surface, scanner_surface_evidence = runtime_value(scope.get("reported_runtime"), "surface")
    scanner_model, scanner_model_evidence = runtime_value(scope.get("reported_runtime"), "model")
    expected_runtime = {
        "surface": scanner_surface,
        "surface_evidence_state": scanner_surface_evidence,
        "model": scanner_model,
        "model_evidence_state": scanner_model_evidence,
    }
    if runtime != expected_runtime:
        raise PacketError("semantic review runtime metadata must exactly match the scanner metadata")

    profile_date = require_string(review["profile_date"], "profile_date", maximum=10, pattern=r"\d{4}-\d{2}-\d{2}")
    try:
        date.fromisoformat(profile_date)
    except ValueError as exc:
        raise PacketError("profile_date must be a real ISO date") from exc

    decision_limit = MAX_QUICK_DECISIONS if mode == "QUICK_CHECK" else MAX_MAINTAINER_DECISIONS
    decisions = require_list(review["decisions"], "decisions", decision_limit)
    if not isinstance(review["semantic_files_reviewed"], int) or isinstance(review["semantic_files_reviewed"], bool):
        raise PacketError("semantic_files_reviewed must be an integer")
    if review["semantic_files_reviewed"] != len(decisions):
        raise PacketError("semantic_files_reviewed must equal the number of decisions")
    if controls and not decisions:
        raise PacketError("at least one visible control must receive a semantic decision")

    reviewed_ids: list[str] = []
    for index, value in enumerate(decisions):
        item = require_exact_fields(value, DECISION_FIELDS, f"decisions[{index}]")
        control_id = require_string(item["control_id"], f"decisions[{index}].control_id", maximum=160)
        reviewed_ids.append(control_id)
        require_string(item["reader_name"], f"decisions[{index}].reader_name", maximum=160)
        require_enum(item["decision"], DECISION_CODES, f"decisions[{index}].decision")
        require_enum(item["evidence_state"], EVIDENCE_STATES, f"decisions[{index}].evidence_state")
        require_string(item["current_effect"], f"decisions[{index}].current_effect", maximum=500)
        require_string(item["proposed_change"], f"decisions[{index}].proposed_change", maximum=1_000)
        require_string(item["reason"], f"decisions[{index}].reason", maximum=1_000)
        require_string(item["must_survive"], f"decisions[{index}].must_survive", maximum=500)
        require_string(item["risk_if_wrong"], f"decisions[{index}].risk_if_wrong", maximum=500)
        require_string(item["rollback"], f"decisions[{index}].rollback", maximum=500)
    if len(reviewed_ids) != len(set(reviewed_ids)):
        raise PacketError("each scanner control may receive only one semantic decision")

    unreviewed = require_list(review["unreviewed_control_ids"], "unreviewed_control_ids", MAX_UNREVIEWED_CONTROLS)
    for index, control_id in enumerate(unreviewed):
        require_string(control_id, f"unreviewed_control_ids[{index}]", maximum=160)
    if len(unreviewed) != len(set(unreviewed)):
        raise PacketError("unreviewed_control_ids must be unique")
    reviewed = set(reviewed_ids)
    unreviewed_set = set(unreviewed)
    if reviewed & unreviewed_set:
        raise PacketError("a control cannot be both reviewed and unreviewed")
    known = set(controls)
    unknown = sorted((reviewed | unreviewed_set) - known)
    if unknown:
        raise PacketError(f"semantic review refers to unknown control IDs: {', '.join(unknown)}")
    missing = sorted(known - (reviewed | unreviewed_set))
    if missing:
        raise PacketError(f"semantic review omits scanner control IDs: {', '.join(missing)}")

    gaps = require_list(review["coverage_gaps"], "coverage_gaps", MAX_COVERAGE_GAPS)
    for index, value in enumerate(gaps):
        validate_coverage_gap(value, index)
    if unreviewed and not gaps:
        raise PacketError("unreviewed controls require a plain-language coverage gap")

    shared = require_exact_fields(
        review["shared_core"], frozenset({"outcome", "context", "authority", "acceptance"}), "shared_core"
    )
    for key in ("outcome", "context", "authority", "acceptance"):
        require_string(shared[key], f"shared_core.{key}", maximum=1_000)

    recommendations = require_list(
        review["model_recommendations"], "model_recommendations", MAX_MODEL_RECOMMENDATIONS
    )
    for index, value in enumerate(recommendations):
        item = require_exact_fields(value, RECOMMENDATION_FIELDS, f"model_recommendations[{index}]")
        require_string(item["recommendation"], f"model_recommendations[{index}].recommendation", maximum=500)
        require_enum(item["status"], frozenset({"SUPPORTED", "UNTESTED"}), f"model_recommendations[{index}].status")
        require_enum(item["evidence_state"], EVIDENCE_STATES, f"model_recommendations[{index}].evidence_state")
        require_string(item["evidence"], f"model_recommendations[{index}].evidence", maximum=500)
        require_string(item["why_here"], f"model_recommendations[{index}].why_here", maximum=1_000)
        require_string(item["would_disprove"], f"model_recommendations[{index}].would_disprove", maximum=500)


def merge_inventory(
    inventory: dict[str, Any], review: dict[str, Any], scope_hash: str, map_hash: str, review_id: str
) -> dict[str, Any]:
    original_safety = copy.deepcopy(inventory.get("safety"))
    original_coverage = copy.deepcopy(inventory.get("coverage"))
    original_run_map = copy.deepcopy(inventory.get("run_map"))
    original_run_trace = copy.deepcopy(inventory.get("run_trace"))
    original_hashes = {
        item["id"]: item["sha256"] for item in inventory["setup_map"]["controls"]
    }

    enriched = copy.deepcopy(inventory)
    decisions_by_id = {item["control_id"]: item for item in review["decisions"]}
    generated_change_ids = [
        derive_change_id(item, map_hash, review_id)
        for item in review["decisions"]
        if item["decision"] != "KEEP"
    ]
    if len(generated_change_ids) != len(set(generated_change_ids)):
        raise PacketError("generated change IDs are not unique")
    top_level_decisions: list[dict[str, Any]] = []
    for control in enriched["setup_map"]["controls"]:
        item = decisions_by_id.get(control["id"])
        if item is None:
            continue
        control["decision"] = {
            "status": item["decision"],
            "reason": item["reason"],
            "evidence_state": item["evidence_state"],
        }
        control["semantic_review"] = {
            "reader_name": item["reader_name"],
            "current_effect": item["current_effect"],
            "proposed_change": item["proposed_change"],
            "must_survive": item["must_survive"],
            "risk_if_wrong": item["risk_if_wrong"],
            "rollback": item["rollback"],
        }
        if item["decision"] != "KEEP":
            control["semantic_review"]["change_id"] = derive_change_id(item, map_hash, review_id)
        top_level_decisions.append({
            "control": item["reader_name"],
            "control_id": item["control_id"],
            "decision": item["decision"],
            "reason": item["reason"],
            "evidence_state": item["evidence_state"],
            **(
                {"change_id": derive_change_id(item, map_hash, review_id)}
                if item["decision"] != "KEEP"
                else {}
            ),
        })
    enriched["decisions"] = top_level_decisions
    enriched["setup_map"]["summary"]["undecided_controls"] = len(review["unreviewed_control_ids"])
    enriched["review_packet"] = {
        "review_id": review_id,
        "edition": review["edition"],
        "review_mode": review["review_mode"],
        "profile_date": review["profile_date"],
        "baseline_scope_sha256": scope_hash,
        "baseline_map_sha256": map_hash,
        "semantic_files_reviewed": review["semantic_files_reviewed"],
        "unreviewed_controls": len(review["unreviewed_control_ids"]),
    }
    semantic_blind_spots = [
        {
            "id": f"semantic-review-gap-{index:03d}",
            "evidence_state": item["evidence_state"],
            "detail": f"{item['area']}: {item['detail']}",
        }
        for index, item in enumerate(review["coverage_gaps"], start=1)
    ]
    enriched["blind_spots"] = copy.deepcopy(inventory.get("blind_spots", [])) + semantic_blind_spots

    if enriched.get("safety") != original_safety:
        raise PacketError("internal error: merge altered scanner safety")
    if enriched.get("coverage") != original_coverage:
        raise PacketError("internal error: merge altered scanner coverage")
    if enriched.get("run_map") != original_run_map or enriched.get("run_trace") != original_run_trace:
        raise PacketError("internal error: merge altered scanner run evidence")
    enriched_hashes = {
        item["id"]: item["sha256"] for item in enriched["setup_map"]["controls"]
    }
    if enriched_hashes != original_hashes:
        raise PacketError("internal error: merge altered scanner control hashes")
    return enriched


def md(value: object, fallback: str = "UNKNOWN") -> str:
    return markdown_text(value, fallback)


def reported_runtime(scope: dict[str, Any]) -> tuple[str, str, str, str]:
    surface, surface_evidence = runtime_value(scope.get("reported_runtime"), "surface")
    model, model_evidence = runtime_value(scope.get("reported_runtime"), "model")
    return surface, surface_evidence, model, model_evidence


def gap_lines(scope: dict[str, Any], review: dict[str, Any]) -> list[str]:
    items: list[dict[str, Any]] = []
    for item in scope.get("blind_spots", []):
        if isinstance(item, dict):
            items.append({
                "area": item.get("id", "Scanner blind spot"),
                "evidence_state": item.get("evidence_state", "INACCESSIBLE"),
                "detail": item.get("detail", "No detail supplied."),
            })
    items.extend(review["coverage_gaps"])
    if not items:
        return ["No additional gap was recorded. This does not make hidden vendor state visible."]
    return [
        f"- **{md(item.get('area'))} ({md(item.get('evidence_state'))}):** {md(item.get('detail'))}"
        for item in items
    ]


def render_scope_markdown(
    scope: dict[str, Any], review: dict[str, Any], scope_hash: str, map_hash: str, review_id: str
) -> str:
    surface, surface_evidence, model, model_evidence = reported_runtime(scope)
    counts = scope.get("counts") if isinstance(scope.get("counts"), dict) else {}
    coverage = [item for item in scope.get("coverage", []) if isinstance(item, dict)]
    lines = [
        "# Scope and Coverage",
        "",
        f"Review ID: {review_id}  ",
        f"Target: {md(scope.get('target', {}).get('label'))}  ",
        f"Edition: {md(review['edition'].title())}  ",
        f"Reported surface: {md(surface)} ({md(surface_evidence)})  ",
        f"Reported model: {md(model)} ({md(model_evidence)})  ",
        f"Baseline scope SHA-256: `{scope_hash}`  ",
        f"Baseline map SHA-256: `{map_hash}`",
        "",
        "## What was reviewed",
        "",
        f"- Visible controls: {md(counts.get('visible_controls', 0))}",
        f"- Controls semantically reviewed: {md(review['semantic_files_reviewed'])}",
        f"- Controls left unreviewed: {md(len(review['unreviewed_control_ids']))}",
        f"- Review mode: {md(review['review_mode'])}",
        "- Change permission: READ ONLY. This packet proposes changes; it applies none.",
        "",
        "## Coverage",
        "",
        "| Area | Evidence | What that supports |",
        "|---|---|---|",
    ]
    if coverage:
        for item in coverage:
            lines.append(
                f"| {md(item.get('area'))} | {md(item.get('evidence_state'))} | {md(item.get('detail'))} |"
            )
    else:
        lines.append("| Coverage not supplied | INACCESSIBLE | The scanner did not declare coverage. |")
    lines.extend(["", "## What I Could Not See", "", *gap_lines(scope, review), ""])
    return "\n".join(lines)


def decision_label(code: str) -> str:
    return f"{DECISION_LABELS[code]} ({code})"


def render_decisions_markdown(
    scope: dict[str, Any], controls: dict[str, dict[str, Any]], review: dict[str, Any], review_id: str
) -> str:
    surface, _, model, _ = reported_runtime(scope)
    prioritized = [item for item in review["decisions"] if item["decision"] != "KEEP"]
    if not prioritized:
        prioritized = review["decisions"]
    lines = [
        "# What Stays and What Changes",
        "",
        f"Review ID: {review_id}  ",
        f"Target: {md(scope.get('target', {}).get('label'))}  ",
        f"Edition and surface: {md(review['edition'].title())} — {md(surface)}  ",
        f"Model: {md(model)}  ",
        f"Inventory generated: {md(scope.get('generated_at'))}  ",
        f"Semantic files reviewed: {md(review['semantic_files_reviewed'])} of {md(len(controls))} visible controls  ",
        f"Unreviewed material: {md(len(review['unreviewed_control_ids']))} controls",
        "",
        "## The three changes to review first",
        "",
    ]
    if prioritized:
        for item in prioritized[:3]:
            control = controls[item["control_id"]]
            lines.extend([
                f"### {md(item['reader_name'])}",
                "",
                f"- Decision: {md(decision_label(item['decision']))}",
                f"- What you may notice now: {md(item['current_effect'])}",
                f"- What would change: {md(item['proposed_change'])}",
                f"- Evidence: {md(item['evidence_state'])}; {md(control['id'])}; {md(control['path'])}; `{control['sha256']}`",
                f"- What must survive: {md(item['must_survive'])}",
                f"- Risk if wrong: {md(item['risk_if_wrong'])}",
                f"- Rollback: {md(item['rollback'])}",
                "",
            ])
    else:
        lines.extend(["No visible controls were available for a semantic decision.", ""])

    lines.extend([
        "## Full decision register",
        "",
        "| Control ID | Source and hash | Decision | Evidence | Reason | Risk | Rollback |",
        "|---|---|---|---|---|---|---|",
    ])
    for item in review["decisions"]:
        control = controls[item["control_id"]]
        lines.append(
            f"| {md(item['control_id'])} | {md(control['path'])}<br>`{control['sha256']}` | "
            f"{md(decision_label(item['decision']))} | {md(item['evidence_state'])} | {md(item['reason'])} | "
            f"{md(item['risk_if_wrong'])} | {md(item['rollback'])} |"
        )
    if not review["decisions"]:
        lines.append("| No reviewed control | Not applicable | Not applicable | NOT_APPLICABLE | No decision. | None | None |")
    lines.extend(["", "## What I Could Not See", "", *gap_lines(scope, review), ""])
    return "\n".join(lines)


def render_model_markdown(scope: dict[str, Any], review: dict[str, Any]) -> str:
    surface, surface_evidence, model, model_evidence = reported_runtime(scope)
    shared = review["shared_core"]
    lines = [
        "# What This Model Needs",
        "",
        f"Edition: {md(review['edition'].title())}  ",
        f"Product surface: {md(surface)} ({md(surface_evidence)})  ",
        f"Model and settings: {md(model)} ({md(model_evidence)})  ",
        f"Profile date: {md(review['profile_date'])}",
        "",
        "## Keep shared",
        "",
        f"- Outcome: {md(shared['outcome'])}",
        f"- Context: {md(shared['context'])}",
        f"- Authority: {md(shared['authority'])}",
        f"- Acceptance: {md(shared['acceptance'])}",
        "",
        "## Change for this surface or model",
        "",
        "| Recommendation | Status and evidence | Why it applies here | What would disprove it |",
        "|---|---|---|---|",
    ]
    for item in review["model_recommendations"]:
        lines.append(
            f"| {md(item['recommendation'])} | {md(item['status'])}; {md(item['evidence_state'])}; {md(item['evidence'])} | "
            f"{md(item['why_here'])} | {md(item['would_disprove'])} |"
        )
    if not review["model_recommendations"]:
        lines.append("| No supported difference declared | UNTESTED | Shared controls remain shared. | A dated test or visible surface mechanic. |")
    lines.extend(["", "## What I Could Not See", "", *gap_lines(scope, review), ""])
    return "\n".join(lines)


def change_rows(
    review: dict[str, Any], map_hash: str, review_id: str
) -> list[tuple[str, dict[str, Any]]]:
    changes = [item for item in review["decisions"] if item["decision"] != "KEEP"]
    return [(derive_change_id(item, map_hash, review_id), item) for item in changes]


def render_review_markdown(
    scope: dict[str, Any],
    controls: dict[str, dict[str, Any]],
    review: dict[str, Any],
    map_hash: str,
    review_id: str,
) -> str:
    lines = [
        "# Review Before Changing Anything",
        "",
        f"Review ID: {review_id}  ",
        f"Target: {md(scope.get('target', {}).get('label'))}  ",
        f"Baseline map SHA-256: `{map_hash}`  ",
        "Permission mode: READ ONLY UNTIL INDIVIDUAL APPROVAL",
        "",
        "To approve, return this same file or reply with the review ID plus the exact change IDs and `APPROVED` or `REJECTED`. Approval of one item never approves the batch.",
        "",
        "| Change ID | Control IDs | Current source hashes | Exact proposed change | Protection that must survive | Risk | Rollback | Decision |",
        "|---|---|---|---|---|---|---|---|",
    ]
    rows = change_rows(review, map_hash, review_id)
    for change_id, item in rows:
        control = controls[item["control_id"]]
        lines.append(
            f"| {change_id} | {md(item['control_id'])} | `{control['sha256']}` | {md(item['proposed_change'])} | "
            f"{md(item['must_survive'])} | {md(item['risk_if_wrong'])} | {md(item['rollback'])} | PROPOSED |"
        )
    if not rows:
        lines.append("| No change proposed | Not applicable | Not applicable | Every reviewed control stays as-is. | Existing protections | None | Not applicable | PROPOSED |")
    lines.extend([
        "",
        "## Apply gate",
        "",
        "Before applying an approved item:",
        "",
        "1. verify the review ID and baseline map hash;",
        "2. re-hash every affected source and stop if it changed;",
        "3. create a recoverable copy, patch, or replacement bundle;",
        "4. apply only rows marked `APPROVED`;",
        "5. run the named preservation and finish checks;",
        "6. stop and record any failed check.",
        "",
        "## What I Could Not See",
        "",
        *gap_lines(scope, review),
        "",
    ])
    return "\n".join(lines)


def make_approval_manifest(
    scope: dict[str, Any],
    controls: dict[str, dict[str, Any]],
    review: dict[str, Any],
    scope_hash: str,
    map_hash: str,
    review_id: str,
) -> dict[str, Any]:
    changes = []
    for item in review["decisions"]:
        if item["decision"] == "KEEP":
            continue
        control = controls[item["control_id"]]
        changes.append({
            "change_id": derive_change_id(item, map_hash, review_id),
            "control_id": item["control_id"],
            "source_path": control["path"],
            "source_sha256": control["sha256"],
            "proposal_sha256": proposal_digest(item, map_hash, review_id),
            "proposed_change": item["proposed_change"],
            "must_survive": item["must_survive"],
            "risk_if_wrong": item["risk_if_wrong"],
            "rollback": item["rollback"],
            "decision": "PROPOSED",
        })
    ids = [item["change_id"] for item in changes]
    if len(ids) != len(set(ids)):
        raise PacketError("generated approval manifest has duplicate change IDs")
    return {
        "schema_version": "1.0",
        "review_id": review_id,
        "scan_id": scope["scan_id"],
        "baseline": {"scope_sha256": scope_hash, "map_sha256": map_hash},
        "permission_mode": "READ_ONLY_UNTIL_INDIVIDUAL_APPROVAL",
        "changes": changes,
    }


def reader_html(value: object, fallback: str = "Unknown") -> str:
    """Escape one value for the reader-facing report."""
    if value is None:
        rendered = fallback
    elif isinstance(value, (str, int, float, bool)):
        rendered = str(value).strip() or fallback
    else:
        rendered = fallback
    return html.escape(rendered, quote=True)


def render_reader_report(
    scope: dict[str, Any],
    controls: dict[str, dict[str, Any]],
    review: dict[str, Any],
    map_hash: str,
    review_id: str,
) -> str:
    """Render the one report an ordinary reader needs to open."""
    surface, surface_evidence, model, model_evidence = reported_runtime(scope)
    control_list = list(controls.values())
    stations = group_setup_stations(control_list)
    keepers = [item for item in review["decisions"] if item["decision"] == "KEEP"]
    changes = [item for item in review["decisions"] if item["decision"] != "KEEP"]

    station_cards = "".join(
        '<article class="station">'
        f'<p class="count">{len(item["controls"])}</p>'
        f'<h3>{reader_html(item["title"])}</h3>'
        f'<p>{reader_html(item["description"])}</p>'
        "</article>"
        for item in stations
    )

    helping = "".join(
        '<article class="item good">'
        f'<h3>{reader_html(item["reader_name"])}</h3>'
        f'<p>{reader_html(item["current_effect"])}</p>'
        f'<p class="why">Why it stays: {reader_html(item["reason"])}</p>'
        "</article>"
        for item in keepers[:8]
    ) or '<p class="empty">Nothing was marked as a clear keeper in the part of the setup this review could see.</p>'

    drag = "".join(
        '<article class="item warn">'
        f'<h3>{reader_html(item["reader_name"])}</h3>'
        f'<p>{reader_html(item["current_effect"])}</p>'
        "</article>"
        for item in changes
    ) or '<p class="empty">This review found no supported cleanup to recommend.</p>'

    recommendations = []
    for number, item in enumerate(changes, start=1):
        recommendations.append(
            '<article class="recommendation">'
            f'<div class="number" aria-hidden="true">{number}</div>'
            '<div>'
            f'<p class="action">{reader_html(DECISION_LABELS[item["decision"]])}</p>'
            f'<h3>{reader_html(item["reader_name"])}</h3>'
            f'<p>{reader_html(item["proposed_change"])}</p>'
            f'<p class="why">Why: {reader_html(item["reason"])}</p>'
            '<details><summary>What this protects</summary>'
            f'<p><strong>Must survive:</strong> {reader_html(item["must_survive"])}</p>'
            f'<p><strong>Risk if wrong:</strong> {reader_html(item["risk_if_wrong"])}</p>'
            f'<p><strong>Undo:</strong> {reader_html(item["rollback"])}</p>'
            "</details></div></article>"
        )
    recommendation_html = "".join(recommendations) or (
        '<p class="empty">There is nothing to approve. The review recommends leaving the visible setup alone.</p>'
    )

    model_cards = "".join(
        '<article class="item model">'
        f'<h3>{reader_html(item["recommendation"])}</h3>'
        f'<p>{reader_html(item["why_here"])}</p>'
        f'<p class="why">Evidence: {reader_html(item["evidence_state"])} — {reader_html(item["evidence"])}</p>'
        "</article>"
        for item in review["model_recommendations"]
    ) or '<p class="empty">No model-specific change was supported by the evidence available to this review.</p>'

    gap_items: list[dict[str, Any]] = []
    for item in scope.get("blind_spots", []):
        if isinstance(item, dict):
            gap_items.append({
                "area": item.get("id", "Hidden setup"),
                "detail": item.get("detail", "No detail supplied."),
            })
    for item in review["coverage_gaps"]:
        gap_items.append({"area": item.get("area"), "detail": item.get("detail")})
    gaps = "".join(
        f'<li><strong>{reader_html(item["area"])}</strong><span>{reader_html(item["detail"])}</span></li>'
        for item in gap_items
    ) or '<li><strong>No additional gap was recorded.</strong><span>Hidden product state may still exist.</span></li>'

    approval_copy = (
        "Reply in chat: Approve 1 and 3. Leave 2."
        if changes
        else "No approval is needed because no change was proposed."
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Your AI Setup, Explained</title>
  <style>
    :root {{ color-scheme:light; --ink:#17211b; --muted:#59645e; --paper:#f6f4ee; --panel:#fff; --line:#d7ddd8; --green:#195b42; --green-soft:#e7f2ec; --amber:#7a4300; --amber-soft:#fff1dc; --blue:#164f75; --blue-soft:#e8f2f8; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--paper); color:var(--ink); font:16px/1.55 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
    header,main,footer {{ width:min(980px,calc(100% - 2rem)); margin-inline:auto; }}
    header {{ padding:3.5rem 0 1.5rem; }}
    h1 {{ margin:.2rem 0 .8rem; font-size:clamp(2.2rem,6vw,4.6rem); line-height:1; letter-spacing:-.045em; }}
    h2 {{ margin:0 0 .4rem; font-size:clamp(1.5rem,3vw,2.2rem); }}
    h3 {{ margin:.1rem 0 .35rem; line-height:1.25; }}
    p {{ margin:.35rem 0; }}
    section {{ margin:1rem 0; padding:clamp(1.1rem,3vw,2rem); background:var(--panel); border:1px solid var(--line); border-radius:16px; }}
    .eyebrow,.action {{ color:var(--green); font-size:.82rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }}
    .lede {{ max-width:68ch; color:var(--muted); font-size:1.12rem; }}
    .badge {{ display:inline-block; padding:.35rem .65rem; border-radius:999px; color:var(--green); background:var(--green-soft); font-weight:750; }}
    .summary {{ display:grid; grid-template-columns:repeat(3,1fr); gap:.7rem; margin-top:1.4rem; }}
    .summary div {{ padding:1rem; background:var(--panel); border:1px solid var(--line); border-radius:12px; }}
    .summary strong,.count {{ display:block; color:var(--green); font-size:1.8rem; font-weight:850; }}
    .runtime {{ margin-top:.8rem; color:var(--muted); }}
    .stations {{ display:grid; grid-template-columns:repeat(5,1fr); gap:.65rem; margin-top:1.2rem; }}
    .station {{ padding:1rem; border-top:4px solid var(--green); border-radius:10px; background:#f8faf8; }}
    .station p:last-child {{ color:var(--muted); font-size:.88rem; }}
    .grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:.75rem; margin-top:1rem; }}
    .item {{ padding:1rem; border-radius:11px; }}
    .good {{ background:var(--green-soft); }} .warn {{ background:var(--amber-soft); }} .model {{ background:var(--blue-soft); }}
    .why {{ color:var(--muted); font-size:.92rem; }}
    .recommendation {{ display:grid; grid-template-columns:2.5rem 1fr; gap:1rem; padding:1.15rem 0; border-top:1px solid var(--line); }}
    .number {{ display:grid; place-items:center; width:2.4rem; height:2.4rem; color:white; background:var(--green); border-radius:50%; font-size:1.2rem; font-weight:850; }}
    details {{ margin-top:.7rem; }} summary {{ cursor:pointer; color:var(--green); font-weight:700; }}
    .reply {{ margin:1.2rem 0 0; padding:1rem; border-left:6px solid var(--green); background:var(--green-soft); font-size:1.08rem; }}
    .gaps {{ padding:0; list-style:none; }} .gaps li {{ display:grid; grid-template-columns:minmax(130px,1fr) 3fr; gap:1rem; padding:.8rem 0; border-top:1px solid var(--line); }}
    .gaps span {{ color:var(--muted); }} .empty {{ color:var(--muted); }}
    footer {{ padding:1rem 0 3rem; color:var(--muted); font-size:.85rem; }}
    @media(max-width:760px) {{ .summary,.stations,.grid {{ grid-template-columns:1fr; }} .gaps li {{ grid-template-columns:1fr; gap:.15rem; }} }}
  </style>
</head>
<body>
  <header>
    <p class="eyebrow">Clean My AI Harness</p>
    <h1>Your AI setup, explained</h1>
    <p class="badge">Read-only review — nothing changed</p>
    <p class="lede">This is the setup your AI could see around this project: the standing rules, skills, context, permissions, and checks that can shape its work before and after you type a prompt.</p>
    <div class="summary" aria-label="Review summary">
      <div><strong>{len(control_list)}</strong>visible parts</div>
      <div><strong>{len(keepers)}</strong>clear keepers</div>
      <div><strong>{len(changes)}</strong>changes to review</div>
    </div>
    <p class="runtime">Reviewed for {reader_html(surface)} ({reader_html(surface_evidence)}) using {reader_html(model)} ({reader_html(model_evidence)}).</p>
  </header>
  <main>
    <section>
      <h2>What shapes your AI</h2>
      <p class="lede">Most people build this setup a rule at a time without realizing they are building a system. Here is the part this review could see.</p>
      <div class="stations">{station_cards}</div>
    </section>
    <section>
      <h2>What is helping</h2>
      <p class="lede">These parts protect the work or give the AI useful context. The audit recommends keeping them.</p>
      <div class="grid">{helping}</div>
    </section>
    <section>
      <h2>What may be getting in the way</h2>
      <p class="lede">These are not automatically bad. They are the places where old rules, duplication, early loading, or soft requirements may be making the setup harder to use.</p>
      <div class="grid">{drag}</div>
    </section>
    <section>
      <h2>What this model needs</h2>
      <p class="lede">Claude and Codex do not expose or use the surrounding setup in exactly the same way. These recommendations are specific to the product and model this review could identify.</p>
      <div class="grid">{model_cards}</div>
    </section>
    <section>
      <h2>What I recommend</h2>
      <p class="lede">Nothing below has been changed. Each number is a separate choice.</p>
      {recommendation_html}
      <p class="reply"><strong>{reader_html(approval_copy)}</strong> You can also approve one item at a time or leave everything alone.</p>
    </section>
    <section>
      <h2>What I could not see</h2>
      <p class="lede">This keeps the report honest. A missing item is a limit of the review, not proof that it does not exist.</p>
      <ul class="gaps">{gaps}</ul>
    </section>
  </main>
  <footer>Review {reader_html(review_id)} · evidence kept in the hidden .clean-my-ai-harness folder · baseline {reader_html(map_hash[:12])}</footer>
</body>
</html>
"""


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n").encode("utf-8")


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def build_packet(
    target_root: Path,
    receipt_path: Path,
    scope_path: Path,
    map_path: Path,
    review_path: Path,
    output_dir: Path,
) -> dict[str, str]:
    target_root, receipt_path, scope_path, map_path, review_path, output_dir = validate_locations(
        target_root, receipt_path, scope_path, map_path, review_path, output_dir
    )
    _, receipt = read_json(receipt_path, MAX_REVIEW_BYTES, "local scan receipt JSON")
    scope_bytes, scope = read_json(scope_path, MAX_INPUT_BYTES, "scope JSON")
    map_bytes, inventory = read_json(map_path, MAX_INPUT_BYTES, "map JSON")
    _, review = read_json(review_path, MAX_REVIEW_BYTES, "semantic review JSON")
    reject_unsafe_review_text(review)

    scope_hash = sha256_bytes(scope_bytes)
    map_hash = sha256_bytes(map_bytes)
    validate_local_scan_receipt(receipt, target_root, scope, scope_hash, map_hash)
    controls = validate_scanner_inputs(scope, inventory, target_root)
    validate_review(review, controls, scope, scope_hash, map_hash)
    review_id = derive_review_id(scope_hash, map_hash)
    enriched = merge_inventory(inventory, review, scope_hash, map_hash, review_id)
    approval_manifest = make_approval_manifest(
        scope, controls, review, scope_hash, map_hash, review_id
    )

    detail = ".clean-my-ai-harness"
    files: dict[str, bytes] = {
        "YOUR-AI-SETUP.html": render_reader_report(
            scope, controls, review, map_hash, review_id
        ).encode("utf-8"),
        f"{detail}/00-scope-and-coverage.json": scope_bytes,
        f"{detail}/00-scope-and-coverage.md": render_scope_markdown(scope, review, scope_hash, map_hash, review_id).encode("utf-8"),
        f"{detail}/01-your-ai-setup-map.inventory.json": map_bytes,
        f"{detail}/01-your-ai-setup-map.json": json_bytes(enriched),
        f"{detail}/01-your-ai-setup-map.md": render_markdown(enriched).encode("utf-8"),
        f"{detail}/01-your-ai-setup-map.html": render_html(enriched).encode("utf-8"),
        f"{detail}/02-what-stays-and-what-changes.md": render_decisions_markdown(scope, controls, review, review_id).encode("utf-8"),
        f"{detail}/03-what-this-model-needs.md": render_model_markdown(scope, review).encode("utf-8"),
        f"{detail}/04-review-before-changing-anything.md": render_review_markdown(scope, controls, review, map_hash, review_id).encode("utf-8"),
        f"{detail}/04-review-before-changing-anything.json": json_bytes(approval_manifest),
    }
    for name, payload in files.items():
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PacketError(f"internal error: {name} is not UTF-8") from exc
        if private_paths(text):
            raise PacketError(f"refusing to write {name}: output contains a private absolute path")

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    if output_dir.exists() or output_dir.is_symlink():
        raise PacketError("packet output must not already exist")
    staged = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.stage-", dir=output_dir.parent))
    published = False
    try:
        for name, payload in files.items():
            atomic_write(staged / name, payload)
        if output_dir.exists() or output_dir.is_symlink():
            raise PacketError("packet output appeared during the build")
        os.rename(staged, output_dir)
        published = True
    finally:
        if not published and staged.exists():
            shutil.rmtree(staged)
    return {name: sha256_bytes(payload) for name, payload in files.items()}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-root", required=True, type=Path, metavar="TARGET")
    parser.add_argument("--scan-receipt", required=True, type=Path, metavar="LOCAL_SCAN_RECEIPT")
    parser.add_argument("scope_json", type=Path, metavar="00_SCOPE_JSON")
    parser.add_argument("map_json", type=Path, metavar="01_MAP_JSON")
    parser.add_argument("semantic_review_json", type=Path, metavar="SEMANTIC_REVIEW_JSON")
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        checksums = build_packet(
            args.target_root,
            args.scan_receipt,
            args.scope_json,
            args.map_json,
            args.semantic_review_json,
            args.output_dir,
        )
    except (OSError, PacketError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": "built", "files": checksums}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
