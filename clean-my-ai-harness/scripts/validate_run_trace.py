#!/usr/bin/env python3
"""Validate a Clean My AI Harness run-trace JSON file without dependencies."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


STAGES = {"Available", "Eligible", "Shown", "Consulted", "Acted through", "Checked", "Accepted"}
STATUSES = {"VERIFIED", "INFERRED", "INACCESSIBLE", "NOT_EXPOSED", "UNKNOWN"}
TRACE_STATUSES = {"COMPLETE", "PARTIAL", "NOT_EXPOSED"}


def validate(payload: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["top level must be an object"]
    if payload.get("trace_status") not in TRACE_STATUSES:
        errors.append("trace_status must be COMPLETE, PARTIAL, or NOT_EXPOSED")
    if not isinstance(payload.get("trace_note"), str) or not payload["trace_note"].strip():
        errors.append("trace_note must be a non-empty string")
    funnel = payload.get("funnel")
    if not isinstance(funnel, list):
        return errors + ["funnel must be a list"]
    seen: set[str] = set()
    for index, item in enumerate(funnel):
        prefix = f"funnel[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        stage = item.get("stage")
        if stage not in STAGES:
            errors.append(f"{prefix}.stage is invalid")
        elif stage in seen:
            errors.append(f"{prefix}.stage is duplicated")
        else:
            seen.add(stage)
        if item.get("status") not in STATUSES:
            errors.append(f"{prefix}.status is invalid")
        count = item.get("count")
        if count is not None and (not isinstance(count, int) or isinstance(count, bool) or count < 0):
            errors.append(f"{prefix}.count must be null or a non-negative integer")
        if not isinstance(item.get("detail"), str) or not item["detail"].strip():
            errors.append(f"{prefix}.detail must be a non-empty string")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace_json", type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.trace_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: could not read valid JSON ({exc.__class__.__name__})", file=sys.stderr)
        return 2
    errors = validate(payload)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2
    print(json.dumps({"valid": True, "trace_status": payload["trace_status"], "stages": len(payload["funnel"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
