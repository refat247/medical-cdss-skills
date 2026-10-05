#!/usr/bin/env python3
"""Verify offline-study-guide release metadata, inventory, hashes, and ZIP shape."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "PACKAGE_MANIFEST.json"

REQUIRED = [
    "SKILL.md",
    "README.md",
    "CHANGELOG.md",
    "VERSION",
    "MANUAL_ACTIVATION.md",
    "ACTIVATION_SMOKE_TEST.md",
    "VERSIONING_DECISION.md",
    "RELEASE_AUDIT.md",
    "TEST_REPORT.md",
    "PACKAGE_MANIFEST.json",
    "agents/openai.yaml",
    "references/input-contract.md",
    "references/reader-contract.md",
    "references/clinical-constraints.md",
    "scripts/build_guide.py",
    "scripts/check_guide.py",
    "scripts/run_regression.py",
    "scripts/verify_release.py",
    "evals/evals.json",
    "evals/triggers.json",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def find_one(pattern: str, text: str, label: str) -> str:
    m = re.search(pattern, text, re.MULTILINE)
    if not m:
        raise ValueError(f"missing {label}")
    return m.group(1)


def current_files() -> list[str]:
    out = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT).as_posix()
        if "__pycache__" in p.parts or p.suffix == ".pyc":
            continue
        out.append(rel)
    return sorted(out)


def verify_tree() -> tuple[str, dict]:
    errors: list[str] = []
    for rel in REQUIRED:
        p = ROOT / rel
        if not p.is_file():
            errors.append(f"missing required file: {rel}")
        elif p.stat().st_size == 0:
            errors.append(f"empty required file: {rel}")

    residue = [p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and ("__pycache__" in p.parts or p.suffix == ".pyc")]
    if residue:
        errors.append("compiled Python residue: " + ", ".join(sorted(residue)))

    skill = read("SKILL.md")
    version = find_one(r'^\s*version:\s*["\']?([^"\'\s]+)', skill, "SKILL.md metadata.version")
    status = find_one(r'^\s*status:\s*["\']?([^"\'\s]+)', skill, "SKILL.md metadata.status")
    lifecycle = find_one(r'^lifecycle:\s*([^\s]+)', skill, "SKILL.md lifecycle")
    visible = find_one(r'^Version\s+([0-9]+\.[0-9]+\.[0-9]+)\.', skill, "SKILL.md visible Version")

    mirrors = {
        "SKILL.md visible": visible,
        "VERSION": read("VERSION").strip(),
        "README.md": find_one(r'^\*\*Version:\*\*\s*([0-9]+\.[0-9]+\.[0-9]+)', read("README.md"), "README version"),
        "agents/openai.yaml": find_one(r'^\s*version:\s*["\']?([^"\'\s]+)', read("agents/openai.yaml"), "agent version"),
        "MANUAL_ACTIVATION.md": find_one(r'^# Manual activation — offline-study-guide v([0-9]+\.[0-9]+\.[0-9]+)', read("MANUAL_ACTIVATION.md"), "manual activation version"),
        "ACTIVATION_SMOKE_TEST.md": find_one(r'^# Activation smoke test — offline-study-guide v([0-9]+\.[0-9]+\.[0-9]+)', read("ACTIVATION_SMOKE_TEST.md"), "smoke-test version"),
    }
    for label, value in mirrors.items():
        if value != version:
            errors.append(f"version drift: {label}={value} canonical={version}")

    agent = read("agents/openai.yaml")
    agent_status = find_one(r'^\s*status:\s*["\']?([^"\'\s]+)', agent, "agent status")
    agent_lifecycle = find_one(r'^\s*lifecycle:\s*["\']?([^"\'\s]+)', agent, "agent lifecycle")
    if agent_status != status:
        errors.append(f"status drift: agent={agent_status} canonical={status}")
    if agent_lifecycle != lifecycle:
        errors.append(f"lifecycle drift: agent={agent_lifecycle} canonical={lifecycle}")
    if "$offline-study-guide" not in agent:
        errors.append("agents/openai.yaml default_prompt does not name $offline-study-guide")

    changelog = read("CHANGELOG.md")
    if not re.search(rf'^##\s+{re.escape(version)}\s+—\s+', changelog, re.MULTILINE):
        errors.append(f"CHANGELOG.md missing current release heading {version}")

    if not MANIFEST.is_file():
        errors.append("PACKAGE_MANIFEST.json missing")
        manifest = {}
    else:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if manifest.get("name") != "offline-study-guide":
            errors.append("manifest name mismatch")
        if manifest.get("version") != version:
            errors.append(f"manifest version drift: {manifest.get('version')} canonical={version}")
        if manifest.get("status") != status:
            errors.append("manifest status drift")
        if manifest.get("lifecycle") != lifecycle:
            errors.append("manifest lifecycle drift")
        files = manifest.get("files", {})
        actual = set(current_files()) - {"PACKAGE_MANIFEST.json"}
        listed = set(files)
        if actual != listed:
            missing = sorted(actual - listed)
            extra = sorted(listed - actual)
            if missing:
                errors.append("manifest missing files: " + ", ".join(missing))
            if extra:
                errors.append("manifest lists absent files: " + ", ".join(extra))
        for rel, rec in files.items():
            p = ROOT / rel
            if p.is_file():
                digest = sha256_file(p)
                if rec.get("sha256") != digest:
                    errors.append(f"manifest hash mismatch: {rel}")
                if rec.get("size") != p.stat().st_size:
                    errors.append(f"manifest size mismatch: {rel}")

    if errors:
        raise SystemExit("RELEASE VERIFY FAIL\n- " + "\n- ".join(errors))
    return version, manifest


def verify_archive(path: Path, version: str, manifest: dict) -> None:
    errors: list[str] = []
    if not path.is_file():
        raise SystemExit(f"archive not found: {path}")
    if f"v{version}" not in path.name:
        errors.append(f"archive filename does not contain v{version}: {path.name}")
    with zipfile.ZipFile(path) as zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
        if len(names) != len(set(names)):
            errors.append("duplicate archive file paths")
        if "SKILL.md" not in names:
            errors.append("SKILL.md is not at archive root")
        if any(n.startswith("offline-study-guide/") for n in names):
            errors.append("archive has an extra offline-study-guide/ wrapper root")
        if any("/__pycache__/" in f"/{n}" or n.endswith(".pyc") for n in names):
            errors.append("archive contains compiled Python residue")
        expected = set(current_files())
        if set(names) != expected:
            miss = sorted(expected - set(names))
            extra = sorted(set(names) - expected)
            if miss:
                errors.append("archive missing files: " + ", ".join(miss))
            if extra:
                errors.append("archive has unexpected files: " + ", ".join(extra))
        for rel, rec in manifest.get("files", {}).items():
            if rel in names:
                data = zf.read(rel)
                if sha256_bytes(data) != rec.get("sha256"):
                    errors.append(f"archive hash mismatch: {rel}")
                if len(data) != rec.get("size"):
                    errors.append(f"archive size mismatch: {rel}")
    if errors:
        raise SystemExit("ARCHIVE VERIFY FAIL\n- " + "\n- ".join(errors))
    print(f"ARCHIVE VERIFY PASS — root-correct v{version} package")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", type=Path)
    args = ap.parse_args()
    version, manifest = verify_tree()
    print(f"RELEASE VERIFY PASS — offline-study-guide v{version}")
    if args.archive:
        verify_archive(args.archive, version, manifest)


if __name__ == "__main__":
    main()
