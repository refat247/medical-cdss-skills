#!/usr/bin/env python3
"""Validate a returned approval manifest against its generated original."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

sys.dont_write_bytecode = True

from build_review_packet import PacketError, read_json, validate_relative_source_path


MAX_APPROVAL_BYTES = 1_000_000
CHANGE_FIELDS = frozenset({
    "change_id",
    "control_id",
    "source_path",
    "source_sha256",
    "proposal_sha256",
    "proposed_change",
    "must_survive",
    "risk_if_wrong",
    "rollback",
    "decision",
})
TOP_FIELDS = frozenset({
    "schema_version",
    "review_id",
    "scan_id",
    "baseline",
    "permission_mode",
    "changes",
})


class ApprovalError(ValueError):
    """Raised when returned approval data is stale, incomplete, or edited."""


def exact_fields(value: object, fields: frozenset[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or frozenset(value) != fields:
        raise ApprovalError(f"{label} fields do not match the approval contract")
    return value


def validate_manifest_shape(value: dict[str, Any], *, original: bool) -> list[dict[str, Any]]:
    exact_fields(value, TOP_FIELDS, "manifest")
    if value["schema_version"] != "1.0":
        raise ApprovalError("approval schema version must be 1.0")
    if not isinstance(value["review_id"], str) or re.fullmatch(r"HARNESS-[A-F0-9]{10}-[A-F0-9]{10}", value["review_id"]) is None:
        raise ApprovalError("review ID is invalid")
    if not isinstance(value["scan_id"], str) or re.fullmatch(r"scan-[a-f0-9]{32}", value["scan_id"]) is None:
        raise ApprovalError("scan ID is invalid")
    baseline = exact_fields(value["baseline"], frozenset({"scope_sha256", "map_sha256"}), "baseline")
    if any(not isinstance(item, str) or re.fullmatch(r"[a-f0-9]{64}", item) is None for item in baseline.values()):
        raise ApprovalError("baseline hashes are invalid")
    if value["permission_mode"] != "READ_ONLY_UNTIL_INDIVIDUAL_APPROVAL":
        raise ApprovalError("permission mode changed")
    changes = value["changes"]
    if not isinstance(changes, list) or len(changes) > 500:
        raise ApprovalError("changes must be a bounded array")
    ids: list[str] = []
    for index, raw in enumerate(changes):
        item = exact_fields(raw, CHANGE_FIELDS, f"change {index}")
        change_id = item["change_id"]
        if not isinstance(change_id, str) or re.fullmatch(r"CHANGE-[A-F0-9]{32}", change_id) is None:
            raise ApprovalError(f"change {index} has an invalid ID")
        ids.append(change_id)
        if not isinstance(item["control_id"], str) or not item["control_id"]:
            raise ApprovalError(f"change {index} has an invalid control ID")
        try:
            validate_relative_source_path(item["source_path"], f"change {index} source path")
        except PacketError as exc:
            raise ApprovalError(str(exc)) from exc
        for field in ("source_sha256", "proposal_sha256"):
            if not isinstance(item[field], str) or re.fullmatch(r"[a-f0-9]{64}", item[field]) is None:
                raise ApprovalError(f"change {index} has an invalid {field}")
        allowed = {"PROPOSED"} if original else {"PROPOSED", "APPROVED", "REJECTED"}
        if item["decision"] not in allowed:
            raise ApprovalError(f"change {index} has an invalid decision transition")
    if len(ids) != len(set(ids)):
        raise ApprovalError("change IDs must be unique")
    return changes


def validate_returned_approval(
    original: dict[str, Any], returned: dict[str, Any]
) -> list[dict[str, str]]:
    original_changes = validate_manifest_shape(original, original=True)
    returned_changes = validate_manifest_shape(returned, original=False)
    for field in ("schema_version", "review_id", "scan_id", "baseline", "permission_mode"):
        if returned[field] != original[field]:
            raise ApprovalError(f"returned approval changed {field}")
    original_by_id = {item["change_id"]: item for item in original_changes}
    returned_by_id = {item["change_id"]: item for item in returned_changes}
    missing = sorted(set(original_by_id) - set(returned_by_id))
    unknown = sorted(set(returned_by_id) - set(original_by_id))
    if missing:
        raise ApprovalError(f"returned approval is missing change IDs: {', '.join(missing)}")
    if unknown:
        raise ApprovalError(f"returned approval contains unknown change IDs: {', '.join(unknown)}")
    decisions: list[dict[str, str]] = []
    for change_id, source in original_by_id.items():
        candidate = returned_by_id[change_id]
        for field in CHANGE_FIELDS - {"decision"}:
            if candidate[field] != source[field]:
                raise ApprovalError(f"returned approval edited {field} for {change_id}")
        if candidate["decision"] != "PROPOSED":
            decisions.append({"change_id": change_id, "decision": candidate["decision"]})
    if not decisions:
        raise ApprovalError("returned approval contains no APPROVED or REJECTED decision")
    return decisions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_json", type=Path, metavar="GENERATED_04_JSON")
    parser.add_argument("returned_json", type=Path, metavar="RETURNED_04_JSON")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        _, original = read_json(args.original_json, MAX_APPROVAL_BYTES, "generated approval JSON")
        _, returned = read_json(args.returned_json, MAX_APPROVAL_BYTES, "returned approval JSON")
        decisions = validate_returned_approval(original, returned)
    except (OSError, PacketError, ApprovalError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": "validated", "decisions": decisions}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
