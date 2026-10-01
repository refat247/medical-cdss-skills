#!/usr/bin/env python3
"""Create a bounded, read-only inventory of a visible AI harness.

Audited files are untrusted data. This scanner never executes them, follows
their links, imports their code, or emits their contents. It reports only
bounded metadata and static signals. Runtime activation and behavioral value
require a separate trace or evaluation and are never inferred here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import stat
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "1.0"
EVIDENCE_STATES = (
    "VERIFIED",
    "USER_REPORTED",
    "INFERRED",
    "INACCESSIBLE",
    "NOT_APPLICABLE",
)
RUN_STAGES = (
    "Available",
    "Eligible",
    "Shown",
    "Consulted",
    "Acted through",
    "Checked",
    "Accepted",
)

DEFAULT_MAX_FILES = 5_000
DEFAULT_MAX_TRAVERSED_FILES = 100_000
DEFAULT_MAX_FILE_BYTES = 1_000_000
DEFAULT_MAX_TOTAL_BYTES = 25_000_000
DEFAULT_MAX_DEPTH = 16
MAX_RECORDED_SAMPLES = 30

EXCLUDED_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "cache",
    "coverage",
    "dist",
    "node_modules",
    "vendor",
    "venv",
}
SECRET_DIR_NAMES = {
    ".aws",
    ".gnupg",
    ".ssh",
    "credentials",
    "keychain",
    "secrets",
}
SECRET_EXACT_NAMES = {
    ".env",
    "cookies",
    "cookies.sqlite",
    "credentials.json",
    "id_dsa",
    "id_ed25519",
    "id_rsa",
    "login data",
    "secrets.json",
}
SECRET_SUFFIXES = {".key", ".p12", ".pfx", ".pem"}

KNOWN_CONTROL_NAMES = {
    ".cursorrules",
    ".mcp.json",
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "SKILL.md",
    "config.toml",
    "mcp.json",
    "openai.yaml",
    "settings.json",
    "settings.local.json",
}
CONTROL_PATH_HINTS = {
    ".agents",
    ".claude",
    ".codex",
    ".cursor",
    "agents",
    "checks",
    "guardrails",
    "hooks",
    "instructions",
    "memory",
    "prompts",
    "references",
    "rules",
    "skills",
    "validators",
}
CONTROL_NAME_HINTS = {
    "agent",
    "approval",
    "config",
    "guardrail",
    "hook",
    "instruction",
    "memory",
    "permission",
    "prompt",
    "rule",
    "schema",
    "setting",
    "skill",
    "tool",
    "validator",
}
TEXT_SUFFIXES = {
    ".json",
    ".md",
    ".mdx",
    ".prompt",
    ".rules",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
BINARY_DOCUMENT_SUFFIXES = {".docx", ".pdf", ".pptx", ".rtf", ".xlsx"}
EXECUTABLE_CONTROL_SUFFIXES = {".js", ".py", ".sh", ".ts"}

SIGNALS = {
    "authority_or_permission": re.compile(
        r"\b(approval|permission|must ask|read[- ]only|destructive|irreversible|"
        r"do not (?:send|publish|delete|deploy|buy))\b",
        re.I,
    ),
    "verification_or_acceptance": re.compile(
        r"\b(acceptance|check|evidence|proof|receipt|schema|test|validat(?:e|or|ion)|verify)\b",
        re.I,
    ),
    "routing_or_activation": re.compile(
        r"\b(activat(?:e|ion)|discover|invoke|load when|router|routing|trigger|use when)\b",
        re.I,
    ),
    "eager_loading": re.compile(
        r"\b(always load|load .* before|mandatory reference|must read|read .* before)\b",
        re.I,
    ),
    "external_action": re.compile(
        r"\b(buy|commit|delete|deploy|email|message|publish|purchase|send|upload)\b",
        re.I,
    ),
    "version_sensitive": re.compile(
        r"\b(Claude|ChatGPT|Codex|GPT[- ]?\d|Fable\s*\d|OpenAI|Anthropic|20\d{2}[-/]\d{2})\b",
        re.I,
    ),
}


class ScanConfigurationError(ValueError):
    """Raised when a requested scan would violate the public safety contract."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_user_label(value: str, label: str) -> str:
    value = value.strip()
    if not value:
        raise ScanConfigurationError(f"{label} must not be empty")
    if len(value) > 160 or any(ord(character) < 32 for character in value):
        raise ScanConfigurationError(f"{label} must be 160 printable characters or fewer")
    return value


def relative_label(path: Path, root: Path) -> str:
    """Return a target-relative label without resolving or exposing the root."""
    try:
        relative = path.relative_to(root)
    except ValueError:
        return "[outside selected target]"
    rendered = relative.as_posix()
    return rendered or "."


def is_secret_name(name: str) -> bool:
    lowered = name.lower()
    return (
        lowered in SECRET_EXACT_NAMES
        or lowered.startswith(".env.")
        or lowered.startswith("credentials.")
        or lowered.startswith("secrets.")
        or Path(lowered).suffix in SECRET_SUFFIXES
    )


def is_candidate(relative_path: Path, *, include_documents: bool = False) -> bool:
    name = relative_path.name
    lowered_name = name.lower()
    lowered_parts = {part.lower() for part in relative_path.parts[:-1]}
    stem_tokens = set(re.findall(r"[a-z]+", Path(lowered_name).stem))
    hinted_path = bool(lowered_parts & CONTROL_PATH_HINTS)
    hinted_name = bool(stem_tokens & CONTROL_NAME_HINTS)
    if name in KNOWN_CONTROL_NAMES or lowered_name in {item.lower() for item in KNOWN_CONTROL_NAMES}:
        return True
    suffix = relative_path.suffix.lower()
    if include_documents and suffix in TEXT_SUFFIXES | BINARY_DOCUMENT_SUFFIXES | {".csv"}:
        return True
    if suffix in TEXT_SUFFIXES and (hinted_path or hinted_name):
        return True
    if suffix in EXECUTABLE_CONTROL_SUFFIXES and (
        bool(lowered_parts & {"checks", "guardrails", "hooks", "validators"}) or hinted_name
    ):
        return True
    return False


def infer_kind(relative_path: Path) -> str:
    name = relative_path.name.lower()
    parts = {part.lower() for part in relative_path.parts}
    stem = relative_path.stem.lower()
    if name == "skill.md" or "skills" in parts:
        return "skill-or-reference"
    if name in {"agents.md", "claude.md", "gemini.md"}:
        return "project-instructions"
    if "permission" in stem or "approval" in stem:
        return "authority-config"
    if "hook" in stem or "validator" in stem or "guardrail" in stem or parts & {"hooks", "validators", "guardrails"}:
        return "deterministic-control"
    if "memory" in stem or "memory" in parts:
        return "memory-or-standing-context"
    if "prompt" in stem or "prompts" in parts:
        return "prompt"
    if name.endswith((".json", ".toml", ".yaml", ".yml")):
        return "configuration"
    if relative_path.suffix.lower() in BINARY_DOCUMENT_SUFFIXES:
        return "supplied-document"
    return "instruction-or-reference"


def inferred_job(kind: str) -> str:
    return {
        "project-instructions": "Standing project rules and context",
        "memory-or-standing-context": "Saved context or preferences",
        "skill-or-reference": "Specialist procedure, route, or reference",
        "authority-config": "Permission or approval boundary",
        "deterministic-control": "Machine-checkable guardrail or finish check",
        "prompt": "Task or reusable prompt context",
        "configuration": "Product or runtime configuration",
        "supplied-document": "Supplied project or task context",
        "instruction-or-reference": "Instruction or supporting reference",
    }.get(kind, "Visible setup material")


def inferred_enforcement(kind: str) -> str:
    if kind in {"authority-config", "deterministic-control"}:
        return "HARD_CONTROL"
    if kind == "configuration":
        return "SYSTEM_CONFIGURATION"
    if kind == "supplied-document":
        return "CONTEXT_ONLY"
    return "WRITTEN_GUIDANCE"


def _read_candidate(path: Path, maximum_bytes: int) -> tuple[bytes, bool]:
    with path.open("rb") as handle:
        payload = handle.read(maximum_bytes + 1)
    return payload[:maximum_bytes], len(payload) > maximum_bytes


def inspect_candidate(path: Path, relative_path: Path, maximum_bytes: int) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    try:
        file_stat = path.lstat()
        if not stat.S_ISREG(file_stat.st_mode):
            return None, errors
        if file_stat.st_size > maximum_bytes:
            return None, [{
                "path": relative_path.as_posix(),
                "code": "file-too-large",
                "message": f"Candidate exceeds the {maximum_bytes}-byte per-file limit.",
            }]
        payload, grew_past_limit = _read_candidate(path, maximum_bytes)
        if grew_past_limit:
            return None, [{
                "path": relative_path.as_posix(),
                "code": "file-grew-past-limit",
                "message": "Candidate changed during the scan and exceeded the per-file limit.",
            }]
    except OSError as exc:
        return None, [{
            "path": relative_path.as_posix(),
            "code": "read-error",
            "message": f"Could not read candidate ({exc.__class__.__name__}).",
        }]

    kind = infer_kind(relative_path)
    if relative_path.suffix.lower() in BINARY_DOCUMENT_SUFFIXES:
        path_text = relative_path.as_posix()
        control_id = "control-" + hashlib.sha256(path_text.encode("utf-8")).hexdigest()[:12]
        return {
            "id": control_id,
            "path": path_text,
            "kind": kind,
            "bytes": len(payload),
            "lines": None,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "content_inspection": "METADATA_ONLY",
            "job": {"value": inferred_job(kind), "evidence_state": "INFERRED"},
            "owner": {"value": "UNKNOWN", "evidence_state": "INACCESSIBLE"},
            "enforcement_type": {"value": inferred_enforcement(kind), "evidence_state": "INFERRED"},
            "evidence": [
                {
                    "state": "VERIFIED",
                    "claim": "This target-relative document was present and hashed within the declared scan bounds.",
                },
                {
                    "state": "INACCESSIBLE",
                    "claim": "The bounded scanner did not extract or interpret the document contents.",
                },
            ],
            "signals": {name: 0 for name in SIGNALS},
            "runtime": {
                "availability": "UNKNOWN",
                "activation": "UNKNOWN",
                "load_timing": "UNKNOWN",
                "consulted": "UNKNOWN",
            },
            "decision": {
                "status": "UNDECIDED",
                "reason": "Document presence does not establish runtime use or whether it should change.",
            },
        }, errors

    if b"\x00" in payload:
        return None, [{
            "path": relative_path.as_posix(),
            "code": "binary-content",
            "message": "Candidate appears to be binary; contents were not inspected.",
        }]

    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        text = payload.decode("utf-8", errors="replace")
        errors.append({
            "path": relative_path.as_posix(),
            "code": "invalid-utf8",
            "message": "Invalid UTF-8 bytes were replaced for signal counting.",
        })

    path_text = relative_path.as_posix()
    signal_counts = {name: len(pattern.findall(text)) for name, pattern in SIGNALS.items()}
    control_id = "control-" + hashlib.sha256(path_text.encode("utf-8")).hexdigest()[:12]
    record = {
        "id": control_id,
        "path": path_text,
        "kind": kind,
        "bytes": len(payload),
        "lines": len(text.splitlines()),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "content_inspection": "STATIC_TEXT_SIGNALS_ONLY",
        "job": {"value": inferred_job(kind), "evidence_state": "INFERRED"},
        "owner": {"value": "UNKNOWN", "evidence_state": "INACCESSIBLE"},
        "enforcement_type": {"value": inferred_enforcement(kind), "evidence_state": "INFERRED"},
        "evidence": [
            {
                "state": "VERIFIED",
                "claim": "This target-relative file was read within the declared scan bounds.",
            },
            {
                "state": "INFERRED",
                "claim": "Kind and signal counts were inferred from path metadata and static text matching; runtime use was not observed.",
            },
        ],
        "signals": signal_counts,
        "runtime": {
            "availability": "UNKNOWN",
            "activation": "UNKNOWN",
            "load_timing": "UNKNOWN",
            "consulted": "UNKNOWN",
        },
        "decision": {
            "status": "UNDECIDED",
            "reason": "A static inventory cannot establish whether this control should be kept, moved, combined, or retired.",
        },
    }
    return record, errors


def add_sample(samples: list[dict[str, str]], path: str, reason: str) -> None:
    if len(samples) < MAX_RECORDED_SAMPLES:
        samples.append({"path": path, "reason": reason})


def walk_candidates(
    root: Path,
    *,
    max_files: int,
    max_traversed_files: int,
    max_depth: int,
    include_documents: bool = False,
) -> tuple[list[tuple[Path, Path]], Counter[str], list[dict[str, str]], list[dict[str, str]], bool]:
    candidates: list[tuple[Path, Path]] = []
    exclusion_counts: Counter[str] = Counter()
    exclusion_samples: list[dict[str, str]] = []
    traversal_errors: list[dict[str, str]] = []
    seen_files = 0
    seen_candidates = 0
    count_limit_hit = False

    def on_error(error: OSError) -> None:
        filename = Path(error.filename) if error.filename else root
        traversal_errors.append({
            "path": relative_label(filename, root),
            "code": "traversal-error",
            "message": f"Could not inspect directory ({error.__class__.__name__}).",
        })

    for current_text, dirnames, filenames in os.walk(root, topdown=True, followlinks=False, onerror=on_error):
        current = Path(current_text)
        relative_current = current.relative_to(root)
        depth = len(relative_current.parts)

        kept_directories: list[str] = []
        for dirname in sorted(dirnames):
            directory = current / dirname
            relative_directory = relative_current / dirname
            lowered = dirname.lower()
            if directory.is_symlink():
                exclusion_counts["symlink"] += 1
                add_sample(exclusion_samples, relative_directory.as_posix(), "symlink not traversed")
            elif lowered in SECRET_DIR_NAMES:
                exclusion_counts["secret-path"] += 1
            elif lowered in EXCLUDED_DIR_NAMES:
                exclusion_counts["excluded-directory"] += 1
                add_sample(exclusion_samples, relative_directory.as_posix(), "excluded directory")
            elif depth + 1 > max_depth:
                exclusion_counts["depth-limit"] += 1
                add_sample(exclusion_samples, relative_directory.as_posix(), "depth limit")
            else:
                kept_directories.append(dirname)
        dirnames[:] = kept_directories

        for filename in sorted(filenames):
            seen_files += 1
            if seen_files > max_traversed_files:
                count_limit_hit = True
                break
            path = current / filename
            relative_path = relative_current / filename
            if path.is_symlink():
                exclusion_counts["symlink"] += 1
                add_sample(exclusion_samples, relative_path.as_posix(), "symlink not followed")
                continue
            if is_secret_name(filename):
                exclusion_counts["secret-path"] += 1
                continue
            if is_candidate(relative_path, include_documents=include_documents):
                seen_candidates += 1
                if seen_candidates > max_files:
                    count_limit_hit = True
                    break
                candidates.append((path, relative_path))
        if count_limit_hit:
            break

    return candidates, exclusion_counts, exclusion_samples, traversal_errors, count_limit_hit


def coverage_records(surface: str, model: str) -> list[dict[str, Any]]:
    return [
        {
            "area": "visible local instruction and control files",
            "evidence_state": "VERIFIED",
            "detail": "Files matching the bounded scanner rules were inventoried without executing their contents.",
        },
        {
            "area": "selected surface and model labels",
            "evidence_state": "USER_REPORTED",
            "detail": f"The caller identified the surface as {surface!r} and the model as {model!r}; the scanner did not verify either runtime value.",
        },
        {
            "area": "control kind, apparent job, and static signals",
            "evidence_state": "INFERRED",
            "detail": "Path metadata and bounded text signals suggest intent; semantic review is required before a cleanup recommendation.",
        },
        {
            "area": "runtime activation and load order",
            "evidence_state": "INACCESSIBLE",
            "detail": "Actual availability, eligibility, loading, and consultation require a product trace or run receipt that the static scanner does not have.",
        },
        {
            "area": "hidden product instructions, routing, memory, and account settings",
            "evidence_state": "INACCESSIBLE",
            "detail": "The local scanner cannot inspect controls the product surface does not expose as files or supplied exports.",
        },
        {
            "area": "behavioral value and model performance",
            "evidence_state": "NOT_APPLICABLE",
            "detail": "This is a static inventory, not a behavioral evaluation or model comparison.",
        },
    ]


def make_blind_spots(
    *,
    exclusion_counts: Counter[str],
    file_errors: list[dict[str, str]],
    count_limit_hit: bool,
    total_byte_limit_hit: bool,
) -> list[dict[str, Any]]:
    blind_spots: list[dict[str, Any]] = [
        {
            "id": "hidden-product-controls",
            "evidence_state": "INACCESSIBLE",
            "detail": "Hidden system instructions, product routing, account memory, and unexported settings were not visible.",
        },
        {
            "id": "runtime-trace",
            "evidence_state": "INACCESSIBLE",
            "detail": "No trace showed which controls were eligible, shown, consulted, acted through, checked, or accepted for a real job.",
        },
        {
            "id": "behavioral-effect",
            "evidence_state": "NOT_APPLICABLE",
            "detail": "Static presence and text signals do not prove that a control helps or harms the work.",
        },
    ]
    if exclusion_counts:
        blind_spots.append({
            "id": "excluded-paths",
            "evidence_state": "INACCESSIBLE",
            "detail": "Some paths were deliberately excluded for privacy, safety, traversal, or relevance limits.",
            "counts": dict(sorted(exclusion_counts.items())),
        })
    if file_errors:
        blind_spots.append({
            "id": "file-errors",
            "evidence_state": "INACCESSIBLE",
            "detail": f"{len(file_errors)} candidate file event(s) could not be fully inspected; see 00-scope-and-coverage.json.",
        })
    if count_limit_hit:
        blind_spots.append({
            "id": "file-count-limit",
            "evidence_state": "INACCESSIBLE",
            "detail": "Traversal stopped at the configured file-count limit.",
        })
    if total_byte_limit_hit:
        blind_spots.append({
            "id": "total-byte-limit",
            "evidence_state": "INACCESSIBLE",
            "detail": "Candidate inspection stopped at the configured total-byte limit.",
        })
    return blind_spots


def scan_visible_harness(
    target: Path,
    *,
    surface: str,
    model: str,
    max_files: int = DEFAULT_MAX_FILES,
    max_traversed_files: int = DEFAULT_MAX_TRAVERSED_FILES,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES,
    max_depth: int = DEFAULT_MAX_DEPTH,
    include_documents: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if target.is_symlink():
        raise ScanConfigurationError("TARGET must not be a symlink")
    root = target.expanduser().resolve()
    if not root.is_dir():
        raise ScanConfigurationError("TARGET must be an existing directory")
    if min(max_files, max_traversed_files, max_file_bytes, max_total_bytes) < 1 or max_depth < 0:
        raise ScanConfigurationError("scan limits must be positive; max depth may be zero")

    surface = safe_user_label(surface, "surface")
    model = safe_user_label(model, "model")
    generated_at = utc_now()
    scan_id = "scan-" + secrets.token_hex(16)
    target_record = {
        "label": root.name,
        "absolute_path_emitted": False,
    }
    candidates, exclusion_counts, exclusion_samples, traversal_errors, count_limit_hit = walk_candidates(
        root,
        max_files=max_files,
        max_traversed_files=max_traversed_files,
        max_depth=max_depth,
        include_documents=include_documents,
    )

    controls: list[dict[str, Any]] = []
    file_errors = list(traversal_errors)
    inspected_bytes = 0
    total_byte_limit_hit = False
    for path, relative_path in candidates:
        try:
            candidate_size = path.lstat().st_size
        except OSError as exc:
            file_errors.append({
                "path": relative_path.as_posix(),
                "code": "stat-error",
                "message": f"Could not inspect candidate metadata ({exc.__class__.__name__}).",
            })
            continue
        if inspected_bytes + min(candidate_size, max_file_bytes) > max_total_bytes:
            total_byte_limit_hit = True
            break
        record, errors = inspect_candidate(path, relative_path, max_file_bytes)
        file_errors.extend(errors)
        if record is not None:
            controls.append(record)
            inspected_bytes += record["bytes"]

    controls.sort(key=lambda item: item["path"].casefold())
    coverage = coverage_records(surface, model)
    blind_spots = make_blind_spots(
        exclusion_counts=exclusion_counts,
        file_errors=file_errors,
        count_limit_hit=count_limit_hit,
        total_byte_limit_hit=total_byte_limit_hit,
    )
    run_map = {
        "trace_status": "NOT_EXPOSED",
        "trace_note": "No run trace was supplied. The setup map must not be treated as proof that a control shaped a job.",
        "funnel": [
            {
                "stage": stage,
                "status": "NOT_EXPOSED",
                "count": None,
                "detail": "Requires a runtime trace or acceptance record.",
            }
            for stage in RUN_STAGES
        ],
        "controls_observed": [],
    }

    scope = {
        "schema_version": SCHEMA_VERSION,
        "scan_id": scan_id,
        "generated_at": generated_at,
        "target": target_record,
        "reported_runtime": {
            "surface": {"value": surface, "evidence_state": "USER_REPORTED"},
            "model": {"value": model, "evidence_state": "USER_REPORTED"},
        },
        "limits": {
            "max_files": max_files,
            "max_traversed_files": max_traversed_files,
            "max_file_bytes": max_file_bytes,
            "max_total_bytes": max_total_bytes,
            "max_depth": max_depth,
            "include_documents": include_documents,
        },
        "safety": {
            "audited_text_treatment": "UNTRUSTED_DATA",
            "target_writes": False,
            "network_access": False,
            "symlink_traversal": False,
            "content_excerpts_emitted": False,
            "secret_paths_recorded": False,
        },
        "evidence_states_supported": list(EVIDENCE_STATES),
        "coverage": coverage,
        "counts": {
            "visible_controls": len(controls),
            "inspected_bytes": inspected_bytes,
            "file_errors": len(file_errors),
            "excluded": sum(exclusion_counts.values()),
        },
        "exclusion_counts": dict(sorted(exclusion_counts.items())),
        "exclusion_samples": exclusion_samples,
        "file_errors": file_errors,
        "blind_spots": blind_spots,
    }
    normalized_map = {
        "schema_version": SCHEMA_VERSION,
        "scan_id": scan_id,
        "generated_at": generated_at,
        "title": "Visible AI harness map",
        "target": target_record,
        "reported_runtime": scope["reported_runtime"],
        "safety": scope["safety"],
        "coverage": coverage,
        "counts": scope["counts"],
        "setup_map": {
            "status": "STATIC_VISIBLE_INVENTORY",
            "summary": {
                "visible_controls": len(controls),
                "inspected_bytes": inspected_bytes,
                "undecided_controls": len(controls),
            },
            "controls": controls,
        },
        "run_map": run_map,
        "decisions": [],
        "decision_note": "The scanner makes no keep, move, combine, or retire decision from static text alone.",
        "blind_spots": blind_spots,
    }
    return scope, normalized_map


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1_048_576), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_local_scan_receipt(
    target: Path,
    scope_path: Path,
    map_path: Path,
    scope: dict[str, Any],
) -> dict[str, Any]:
    """Create a local-only target binding; never copy this into reader output."""
    return {
        "schema_version": SCHEMA_VERSION,
        "scan_id": scope["scan_id"],
        "generated_at": scope["generated_at"],
        "target_root": str(target.resolve()),
        "scope_sha256": sha256_file(scope_path),
        "map_sha256": sha256_file(map_path),
        "safety": scope["safety"],
    }


def validate_output_location(target: Path, output_dir: Path) -> tuple[Path, Path]:
    if target.is_symlink():
        raise ScanConfigurationError("TARGET must not be a symlink")
    if output_dir.exists() and output_dir.is_symlink():
        raise ScanConfigurationError("--output-dir must not be a symlink")
    root = target.expanduser().resolve()
    output = output_dir.expanduser().resolve(strict=False)
    if output == root or root in output.parents:
        raise ScanConfigurationError("--output-dir must be outside TARGET so the scan remains read-only")
    return root, output


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path, metavar="TARGET")
    parser.add_argument("--surface", required=True, help="Caller-reported product surface.")
    parser.add_argument("--model", required=True, help="Caller-reported model or router.")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--max-files", type=positive_int, default=DEFAULT_MAX_FILES)
    parser.add_argument("--max-traversed-files", type=positive_int, default=DEFAULT_MAX_TRAVERSED_FILES)
    parser.add_argument("--max-file-bytes", type=positive_int, default=DEFAULT_MAX_FILE_BYTES)
    parser.add_argument("--max-total-bytes", type=positive_int, default=DEFAULT_MAX_TOTAL_BYTES)
    parser.add_argument("--max-depth", type=nonnegative_int, default=DEFAULT_MAX_DEPTH)
    parser.add_argument(
        "--include-documents",
        action="store_true",
        help="Also inventory ordinary text files and common uploaded document formats; binary document contents remain uninspected.",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        target, output_dir = validate_output_location(args.target, args.output_dir)
        scope, normalized_map = scan_visible_harness(
            target,
            surface=args.surface,
            model=args.model,
            max_files=args.max_files,
            max_traversed_files=args.max_traversed_files,
            max_file_bytes=args.max_file_bytes,
            max_total_bytes=args.max_total_bytes,
            max_depth=args.max_depth,
            include_documents=args.include_documents,
        )
        scope_path = output_dir / "00-scope-and-coverage.json"
        map_path = output_dir / "01-your-ai-setup-map.json"
        receipt_path = output_dir / ".scan-receipt.json"
        atomic_write_json(scope_path, scope)
        atomic_write_json(map_path, normalized_map)
        atomic_write_json(
            receipt_path,
            build_local_scan_receipt(target, scope_path, map_path, scope),
        )
    except (OSError, ScanConfigurationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps({
        "scope_and_coverage": str(scope_path),
        "normalized_harness_map": str(map_path),
        "local_scan_receipt": str(receipt_path),
        "visible_controls": normalized_map["setup_map"]["summary"]["visible_controls"],
        "run_trace": normalized_map["run_map"]["trace_status"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
