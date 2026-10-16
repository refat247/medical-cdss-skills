"""Portable Semantic Version Bumper & Synchronizer.

Designed for OpenAI/ChatGPT Agent Skills and conventional Python/Node projects.
Discovers, inspects, updates, and verifies current version declarations across:
- SKILL.md YAML frontmatter (top-level version or metadata.version)
- agents/openai.yaml top-level version
- Python packages (pyproject.toml, setup.cfg, setup.py, __init__.py)
- Node/TypeScript packages (package.json)
- Documentation (README.md current version/title patterns)
- CHANGELOG.md latest Keep-a-Changelog release heading
- Version-pinned tests and selected Python constants

The updater stages all changed file contents first and uses rollback on write failure.
This is rollback-protected multi-file synchronization, not a filesystem transaction.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

SEMVER_PATTERN = r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
SEMVER_FULL_RE = re.compile(rf"^v?({SEMVER_PATTERN})$")
EXCLUDED_DIRS = {".git", ".pytest_cache", "__pycache__", "node_modules", "venv", ".venv", ".mypy_cache", ".ruff_cache"}


def normalize_semver(value: str) -> str:
    m = SEMVER_FULL_RE.match(value.strip())
    if not m:
        raise ValueError(f"Invalid SemVer string: '{value}' (expected SemVer 2.0.0)")
    return m.group(1)


def parse_semver(v_str: str) -> Tuple[int, int, int, Optional[str]]:
    """Backward-compatible parser returning (major, minor, patch, prerelease/build suffix)."""
    normalized = normalize_semver(v_str)
    core_and_pre, plus, build = normalized.partition("+")
    core, dash, pre = core_and_pre.partition("-")
    major, minor, patch = (int(x) for x in core.split("."))
    suffix = pre or None
    if build:
        suffix = f"{suffix}+{build}" if suffix else f"+{build}"
    return major, minor, patch, suffix


def _semver_sort_key(value: str) -> Tuple[int, int, int, int, Tuple[Tuple[int, Any], ...]]:
    """SemVer precedence key. Build metadata is ignored for precedence."""
    normalized = normalize_semver(value)
    core_pre = normalized.split("+", 1)[0]
    core, sep, pre = core_pre.partition("-")
    major, minor, patch = (int(x) for x in core.split("."))
    if not sep:
        return (major, minor, patch, 1, ())
    parts: List[Tuple[int, Any]] = []
    for token in pre.split("."):
        if token.isdigit():
            parts.append((0, int(token)))
        else:
            parts.append((1, token))
    return (major, minor, patch, 0, tuple(parts))


def bump_semver(current: str, part: str) -> str:
    current_norm = normalize_semver(current)
    major, minor, patch = (int(x) for x in current_norm.split("+", 1)[0].split("-", 1)[0].split("."))
    part_lower = part.lower()
    if part_lower == "major":
        return f"{major + 1}.0.0"
    if part_lower == "minor":
        return f"{major}.{minor + 1}.0"
    if part_lower == "patch":
        return f"{major}.{minor}.{patch + 1}"
    return normalize_semver(part)


def _today_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


@dataclass(frozen=True)
class VersionDeclaration:
    file_path: str
    file_type: str
    current_version: str
    line_num: int
    line_content: str

    def __repr__(self) -> str:
        return f"[{self.file_type}] {self.file_path}:{self.line_num} -> {self.current_version}"


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore", newline="") as f:
        return f.read()


def _line_num(text: str, start: int) -> int:
    return text.count("\n", 0, start) + 1


def _append_match(decls: List[VersionDeclaration], path: str, kind: str, text: str, match: re.Match[str], group: int = 1) -> None:
    version = normalize_semver(match.group(group))
    line_no = _line_num(text, match.start(group))
    line = text.splitlines()[line_no - 1].strip() if text.splitlines() else ""
    decls.append(VersionDeclaration(path, kind, version, line_no, line))


def _frontmatter(text: str) -> Optional[Tuple[int, int, str]]:
    """Return (body_start, body_end, body) for leading YAML frontmatter."""
    if not text.startswith("---"):
        return None
    m = re.match(r"^---\s*\r?\n([\s\S]*?)\r?\n---(?:\s*\r?\n|$)", text)
    if not m:
        return None
    return m.start(1), m.end(1), m.group(1)


def _discover_skill_frontmatter(path: str, text: str, decls: List[VersionDeclaration]) -> None:
    fm = _frontmatter(text)
    if not fm:
        return
    offset, _, body = fm

    # Top-level version: (no indentation)
    top = re.search(rf"(?m)^version:\s*[\"']?({SEMVER_PATTERN})[\"']?\s*$", body)
    if top:
        shifted = re.search(re.escape(top.group(0)), text[offset:])
        abs_start = offset + (shifted.start() if shifted else top.start())
        fake = re.compile(rf"({SEMVER_PATTERN})").search(text, abs_start)
        if fake:
            _append_match(decls, path, "SKILL_FRONTMATTER", text, fake)
        return

    # metadata.version nested below a top-level metadata key.
    meta = re.search(r"(?m)^metadata:\s*(?:#.*)?$", body)
    if meta:
        tail = body[meta.end():]
        nested = re.search(rf"(?m)^\s{{2,}}version:\s*[\"']?({SEMVER_PATTERN})[\"']?\s*$", tail)
        if nested:
            value_rel = meta.end() + nested.start(1)
            value_abs = offset + value_rel
            fake = re.compile(rf"({SEMVER_PATTERN})").search(text, value_abs)
            if fake and fake.start() == value_abs:
                _append_match(decls, path, "SKILL_METADATA_VERSION", text, fake)


def discover_versions(root_dir: str) -> List[VersionDeclaration]:
    """Scan a package/project for canonical current version declarations."""
    declarations: List[VersionDeclaration] = []
    root = os.path.abspath(root_dir)

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        rel_dir = os.path.relpath(dirpath, root)

        for fname in filenames:
            path = os.path.join(dirpath, fname)
            rel = os.path.relpath(path, root).replace(os.sep, "/")
            text = None

            if fname == "SKILL.md" and dirpath == root:
                text = _read(path)
                _discover_skill_frontmatter(path, text, declarations)
                for m in re.finditer(rf"(?m)^#\s+.*?\(v({SEMVER_PATTERN})\)\s*$", text):
                    _append_match(declarations, path, "SKILL_HEADER", text, m)

            elif rel == "agents/openai.yaml":
                text = _read(path)
                m = re.search(rf"(?m)^version:\s*[\"']?({SEMVER_PATTERN})[\"']?\s*$", text)
                if m:
                    _append_match(declarations, path, "OPENAI_YAML", text, m)

            elif fname == "package.json" and dirpath == root:
                text = _read(path)
                m = re.search(rf'"version"\s*:\s*"({SEMVER_PATTERN})"', text)
                if m:
                    _append_match(declarations, path, "PACKAGE_JSON", text, m)

            elif fname == "pyproject.toml" and dirpath == root:
                text = _read(path)
                m = re.search(rf'(?m)^version\s*=\s*["\']({SEMVER_PATTERN})["\']\s*$', text)
                if m:
                    _append_match(declarations, path, "PYPROJECT_TOML", text, m)

            elif fname in {"setup.cfg", "setup.py"} and dirpath == root:
                text = _read(path)
                if fname == "setup.cfg":
                    m = re.search(rf'(?m)^version\s*=\s*({SEMVER_PATTERN})\s*$', text)
                else:
                    m = re.search(rf'version\s*=\s*["\']({SEMVER_PATTERN})["\']', text)
                if m:
                    _append_match(declarations, path, "PYTHON_SETUP", text, m)

            elif fname == "__init__.py":
                text = _read(path)
                for m in re.finditer(rf'(?m)^__version__\s*=\s*["\']({SEMVER_PATTERN})["\']\s*$', text):
                    _append_match(declarations, path, "PYTHON_INIT", text, m)

            elif fname.endswith(".py") and not fname.startswith("test_"):
                text = _read(path)
                for m in re.finditer(rf'(?m)^(?:PIPELINE_VERSION|SKILL_VERSION|VERSION|APP_VERSION)\s*=\s*["\']({SEMVER_PATTERN})["\']\s*$', text):
                    _append_match(declarations, path, "PYTHON_CONST", text, m)

            elif fname == "README.md" and dirpath == root:
                text = _read(path)
                patterns = [
                    ("README_INSTALLED", rf"Installed\s*\(v({SEMVER_PATTERN})\)"),
                    ("README_HEADER", rf"(?m)^#\s+.*?\(v({SEMVER_PATTERN})\)\s*$"),
                    ("README_VERSION", rf"(?mi)^\*\*Version:\*\*\s*`?\**({SEMVER_PATTERN})\**`?\s*$"),
                    ("README_VERSION", rf"(?mi)^Version:\s*`?\**({SEMVER_PATTERN})\**`?\s*$"),
                    ("README_WORKING_VERSION", rf"(?mi)^\*\*Working version:\*\*\s*`?\**({SEMVER_PATTERN})\**`?\s*$"),
                ]
                seen_spans = set()
                for kind, pattern in patterns:
                    for m in re.finditer(pattern, text):
                        span = m.span(1)
                        if span not in seen_spans:
                            _append_match(declarations, path, kind, text, m)
                            seen_spans.add(span)

            elif fname == "CHANGELOG.md" and dirpath == root:
                text = _read(path)
                m = re.search(rf"(?m)^##\s*\[?({SEMVER_PATTERN})\]?\s*(?:-|—|$)", text)
                if m:
                    _append_match(declarations, path, "CHANGELOG_LATEST", text, m)

            elif fname.startswith("test_") and ("version" in fname or "consistency" in fname):
                text = _read(path)
                for m in re.finditer(
                    rf'(?m)^\s*assert\s+(?:__version__|PIPELINE_VERSION|VERSION|skill_v|changelog_v)\s*==\s*["\']({SEMVER_PATTERN})["\']',
                    text,
                ):
                    _append_match(declarations, path, "TEST_ASSERTION", text, m)

    # Stable deterministic order and exact-declaration de-duplication.
    unique: Dict[Tuple[str, str, int, str], VersionDeclaration] = {}
    for d in declarations:
        unique[(d.file_path, d.file_type, d.line_num, d.current_version)] = d
    return sorted(unique.values(), key=lambda d: (d.file_path, d.line_num, d.file_type))


def check_consistency(root_dir: str) -> Tuple[bool, Optional[str], Dict[str, List[VersionDeclaration]]]:
    """Return False when there are zero declarations or when declarations drift."""
    decls = discover_versions(root_dir)
    if not decls:
        return False, None, {}
    groups: Dict[str, List[VersionDeclaration]] = {}
    for d in decls:
        groups.setdefault(d.current_version, []).append(d)
    if len(groups) == 1:
        return True, next(iter(groups)), groups
    return False, None, groups


def _replace_skill_frontmatter(text: str, target: str) -> str:
    fm = _frontmatter(text)
    if not fm:
        return text
    start, end, body = fm
    if re.search(r"(?m)^version:", body):
        body2 = re.sub(rf"(?m)^(version:\s*[\"']?)({SEMVER_PATTERN})([\"']?\s*)$", rf"\g<1>{target}\g<3>", body, count=1)
    elif re.search(r"(?m)^metadata:\s*(?:#.*)?$", body):
        meta = re.search(r"(?m)^metadata:\s*(?:#.*)?$", body)
        assert meta is not None
        head, tail = body[: meta.end()], body[meta.end():]
        tail2 = re.sub(
            rf"(?m)^(\s{{2,}}version:\s*[\"']?)({SEMVER_PATTERN})([\"']?\s*)$",
            rf"\g<1>{target}\g<3>", tail, count=1,
        )
        body2 = head + tail2
    else:
        body2 = body
    result = text[:start] + body2 + text[end:]
    return re.sub(rf"(?m)^(#\s+.*?\(v)({SEMVER_PATTERN})(\)\s*)$", rf"\g<1>{target}\g<3>", result)


def _replace_current_versions(rel: str, text: str, target: str) -> str:
    if rel == "SKILL.md":
        text = _replace_skill_frontmatter(text, target)
        text = re.sub(rf'(skill_version:\s*["\'])({SEMVER_PATTERN})(["\'])', rf"\g<1>{target}\g<3>", text)
        return text
    if rel == "agents/openai.yaml":
        return re.sub(rf"(?m)^(version:\s*[\"']?)({SEMVER_PATTERN})([\"']?\s*)$", rf"\g<1>{target}\g<3>", text, count=1)
    if rel == "package.json":
        return re.sub(rf'("version"\s*:\s*")({SEMVER_PATTERN})(")', rf"\g<1>{target}\g<3>", text, count=1)
    if rel == "pyproject.toml":
        return re.sub(rf'(?m)^(version\s*=\s*["\'])({SEMVER_PATTERN})(["\']\s*)$', rf"\g<1>{target}\g<3>", text, count=1)
    if rel == "setup.cfg":
        return re.sub(rf"(?m)^(version\s*=\s*)({SEMVER_PATTERN})(\s*)$", rf"\g<1>{target}\g<3>", text, count=1)
    if rel == "setup.py":
        return re.sub(rf'(version\s*=\s*["\'])({SEMVER_PATTERN})(["\'])', rf"\g<1>{target}\g<3>", text, count=1)
    if rel == "README.md":
        replacements = [
            (rf"(Installed\s*\(v)({SEMVER_PATTERN})(\))", rf"\g<1>{target}\g<3>"),
            (rf"(?m)^(#\s+.*?\(v)({SEMVER_PATTERN})(\)\s*)$", rf"\g<1>{target}\g<3>"),
            (rf"(?mi)^(\*\*Version:\*\*\s*`?\**?)({SEMVER_PATTERN})(\**`?\s*)$", rf"\g<1>{target}\g<3>"),
            (rf"(?mi)^(Version:\s*`?\**?)({SEMVER_PATTERN})(\**`?\s*)$", rf"\g<1>{target}\g<3>"),
            (rf"(?mi)^(\*\*Working version:\*\*\s*`?\**?)({SEMVER_PATTERN})(\**`?\s*)$", rf"\g<1>{target}\g<3>"),
        ]
        for pattern, repl in replacements:
            text = re.sub(pattern, repl, text)
        return text
    return text


def _replace_dynamic_decls(path: str, text: str, types: Iterable[str], target: str) -> str:
    kinds = set(types)
    if "PYTHON_INIT" in kinds:
        text = re.sub(rf'(?m)^(__version__\s*=\s*["\'])({SEMVER_PATTERN})(["\']\s*)$', rf"\g<1>{target}\g<3>", text)
    if "PYTHON_CONST" in kinds:
        text = re.sub(rf'(?m)^((?:PIPELINE_VERSION|SKILL_VERSION|VERSION|APP_VERSION)\s*=\s*["\'])({SEMVER_PATTERN})(["\']\s*)$', rf"\g<1>{target}\g<3>", text)
    if "TEST_ASSERTION" in kinds:
        text = re.sub(
            rf'(?m)^(\s*assert\s+(?:__version__|PIPELINE_VERSION|VERSION|skill_v|changelog_v)\s*==\s*["\'])({SEMVER_PATTERN})(["\'])',
            rf"\g<1>{target}\g<3>", text,
        )
    return text


def _with_changelog_release(content: str, target: str, release_notes: Optional[str]) -> str:
    if re.search(rf"(?m)^##\s*\[?{re.escape(target)}\]?\s*(?:-|—|$)", content):
        return content
    newline = "\r\n" if "\r\n" in content else "\n"
    body = release_notes.strip() if release_notes else "### Changed\n- Version synchronization update."
    body = body.replace("\r\n", "\n").replace("\r", "\n").replace("\n", newline)
    entry = f"## [{target}] - {_today_iso()}{newline}{newline}{body}{newline}{newline}"
    first = re.search(rf"(?m)^##\s*\[?{SEMVER_PATTERN}\]?\s*(?:-|—|$)", content)
    if first:
        return content[: first.start()] + entry + content[first.start():]
    return content.rstrip() + "\n\n" + entry


def plan_version_bump(root_dir: str, target_version: str, release_notes: Optional[str] = None) -> Dict[str, Tuple[str, str]]:
    """Return path -> (original, updated) without writing."""
    target = normalize_semver(target_version)
    decls = discover_versions(root_dir)
    if not decls:
        raise RuntimeError(f"No version declarations discovered in: {root_dir}")
    root = os.path.abspath(root_dir)
    by_path: Dict[str, List[VersionDeclaration]] = {}
    for d in decls:
        by_path.setdefault(d.file_path, []).append(d)

    candidates = set(by_path)
    changelog = os.path.join(root, "CHANGELOG.md")
    if os.path.exists(changelog):
        candidates.add(changelog)

    changes: Dict[str, Tuple[str, str]] = {}
    for path in sorted(candidates):
        original = _read(path)
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        updated = _replace_current_versions(rel, original, target)
        updated = _replace_dynamic_decls(path, updated, (d.file_type for d in by_path.get(path, [])), target)
        if rel == "CHANGELOG.md":
            updated = _with_changelog_release(updated, target, release_notes)
        if updated != original:
            changes[path] = (original, updated)
    return changes


def _commit_with_rollback(changes: Dict[str, Tuple[str, str]]) -> List[str]:
    """Write staged contents with rollback on ordinary write/replace failures."""
    staged: Dict[str, str] = {}
    replaced: List[str] = []
    try:
        for path, (_, updated) in changes.items():
            fd, tmp = tempfile.mkstemp(prefix=".version-manager-", dir=os.path.dirname(path), text=True)
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
                f.write(updated)
                f.flush()
                os.fsync(f.fileno())
            staged[path] = tmp
        for path in sorted(staged):
            os.replace(staged[path], path)
            replaced.append(path)
        return replaced
    except Exception:
        for path in reversed(replaced):
            original = changes[path][0]
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(original)
        raise
    finally:
        for tmp in staged.values():
            if os.path.exists(tmp):
                os.unlink(tmp)


def apply_version_bump(root_dir: str, target_version: str, release_notes: Optional[str] = None, dry_run: bool = False) -> List[str]:
    changes = plan_version_bump(root_dir, target_version, release_notes)
    if dry_run:
        return sorted(changes)
    return sorted(_commit_with_rollback(changes))


def verify_versions(root_dir: str) -> Tuple[bool, Optional[str], List[VersionDeclaration]]:
    is_consistent, primary, groups = check_consistency(root_dir)
    if not groups:
        return False, None, []
    if is_consistent:
        return True, primary, []
    sorted_groups = sorted(groups.items(), key=lambda item: (-len(item[1]), _semver_sort_key(item[0])), reverse=False)
    canonical = max(groups, key=lambda v: (len(groups[v]), _semver_sort_key(v)))
    mismatches = [d for ver, items in groups.items() if ver != canonical for d in items]
    return False, canonical, mismatches


def bump_all(root_dir: str, bump_type: str, message: Optional[str] = None, category: Optional[str] = None, dry_run: bool = False) -> Tuple[bool, str]:
    is_consistent, current, groups = check_consistency(root_dir)
    if not groups:
        raise RuntimeError(f"No version declarations discovered in: {root_dir}")
    action = bump_type.lower()
    if current is None and action in {"major", "minor", "patch"}:
        raise RuntimeError(
            "Version drift makes a relative bump baseline ambiguous. "
            "Repair drift first or provide an explicit target SemVer."
        )
    target = normalize_semver(bump_type) if action not in {"major", "minor", "patch"} else bump_semver(current, action)
    release_notes = None
    if message:
        cat = (category or ("Added" if bump_type.lower() == "minor" else "Changed")).strip().capitalize()
        release_notes = f"### {cat}\n- {message.strip()}"
    apply_version_bump(root_dir, target, release_notes, dry_run=dry_run)
    if dry_run:
        return True, target
    verified, new_v, _ = verify_versions(root_dir)
    return verified and new_v == target, target


def discover_skill_suite(parent_dir: str, name_filter: Optional[str] = None) -> List[Tuple[str, str]]:
    suite: List[Tuple[str, str]] = []
    parent = os.path.abspath(parent_dir)
    if not os.path.exists(parent):
        return suite
    for entry in sorted(os.listdir(parent)):
        path = os.path.join(parent, entry)
        if not os.path.isdir(path) or entry in EXCLUDED_DIRS:
            continue
        if name_filter and name_filter.lower() not in entry.lower():
            continue
        if os.path.exists(os.path.join(path, "SKILL.md")) or os.path.exists(os.path.join(path, "pyproject.toml")):
            suite.append((entry, path))
    if not suite and not name_filter:
        for root, dirs, files in os.walk(parent):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            rel = os.path.relpath(root, parent)
            depth = 0 if rel == "." else rel.count(os.sep) + 1
            if depth > 3:
                dirs[:] = []
                continue
            if "SKILL.md" in files and root != parent:
                suite.append((os.path.basename(root), root))
    return suite


def audit_suite(parent_dir: str, verify: bool = False, inspect: bool = False, name_filter: Optional[str] = None) -> Tuple[bool, List[Dict[str, Any]]]:
    suite = discover_skill_suite(parent_dir, name_filter=name_filter)
    if not suite:
        print(f"[SUITE] No skill packages found in: {parent_dir}", file=sys.stderr)
        return False, []
    results: List[Dict[str, Any]] = []
    all_ok = True
    for name, path in suite:
        decls = discover_versions(path)
        consistent, canonical, groups = check_consistency(path)
        if not consistent:
            all_ok = False
        results.append({
            "name": name,
            "path": path,
            "declarations": len(decls),
            "version": canonical or ("UNRESOLVED" if not groups else "DRIFT"),
            "is_consistent": consistent,
            "drift_groups": groups if not consistent else {},
            "has_tests": os.path.isdir(os.path.join(path, "tests")),
        })
    print("\n" + "=" * 88)
    print(f" SKILL SUITE VERIFICATION REPORT: {parent_dir}")
    print("=" * 88)
    print(f"{'Skill Package':<38} | {'Version':<16} | {'Decls':<6} | Status")
    print("-" * 88)
    for r in results:
        status = "[OK] Consistent" if r["is_consistent"] else ("[FAIL] No declarations" if r["declarations"] == 0 else "[FAIL] Drift")
        print(f"{r['name']:<38} | {r['version']:<16} | {r['declarations']:<6} | {status}")
    print("-" * 88)
    passed = sum(1 for r in results if r["is_consistent"])
    print(f" Suite Health: {passed}/{len(results)} package(s) verified.\n")
    return all_ok, results


def main() -> None:
    parser = argparse.ArgumentParser(description="Portable Semantic Version Bumper & Synchronizer")
    parser.add_argument("target", nargs="?", default=None, help="Target repository or skill directory")
    parser.add_argument("--dir", "-d", default=None, help="Alternative target directory")
    parser.add_argument("--suite", "-s", help="Audit all skills in a parent directory")
    parser.add_argument("--filter", "-f", help="Substring filter for suite skill names")
    parser.add_argument("--inspect", action="store_true", help="Read-only declaration inventory and drift report")
    parser.add_argument("--verify", action="store_true", help="Exit 0 only when >=1 declarations exist and all agree")
    parser.add_argument("--bump", help="major, minor, patch, or explicit SemVer")
    parser.add_argument("--set-version", help="Explicit SemVer target")
    parser.add_argument("--message", "-m", help="Single changelog bullet")
    parser.add_argument("--notes", help="Full markdown release-note body")
    parser.add_argument("--category", default=None, help="Changelog category")
    parser.add_argument("--dry-run", action="store_true", help="Plan bump without writing files")
    args = parser.parse_args()

    if args.suite and (args.bump or args.set_version):
        print("Error: --suite is audit-only; run the bump on one skill directory at a time.", file=sys.stderr)
        raise SystemExit(2)

    if args.suite:
        suite = os.path.abspath(args.suite)
        if not os.path.exists(suite):
            print(f"Error: Suite directory not found: {suite}", file=sys.stderr)
            raise SystemExit(1)
        ok, _ = audit_suite(suite, verify=args.verify, inspect=args.inspect, name_filter=args.filter)
        raise SystemExit(0 if ok else 1)

    target = os.path.abspath(args.target or args.dir or ".")
    if not os.path.exists(target):
        print(f"Error: Target directory not found: {target}", file=sys.stderr)
        raise SystemExit(1)

    if args.inspect:
        decls = discover_versions(target)
        print(f"\nDiscovered {len(decls)} version declaration(s) in: {target}")
        print("-" * 72)
        for d in decls:
            print(f"  {d}")
        consistent, version, groups = check_consistency(target)
        print("-" * 72)
        if consistent:
            print(f"Status: OK (Consistent version: {version})\n")
            raise SystemExit(0)
        if not groups:
            print("Status: UNRESOLVED (no version declarations discovered)\n", file=sys.stderr)
        else:
            print(f"Status: DRIFT DETECTED across {len(groups)} version(s):", file=sys.stderr)
            for ver, items in groups.items():
                print(f"  - v{ver}: {len(items)} declaration(s)", file=sys.stderr)
        raise SystemExit(1)

    if args.verify:
        consistent, version, groups = check_consistency(target)
        if consistent:
            print(f"[OK] All discovered version declarations in {os.path.basename(target)} agree on v{version}")
            raise SystemExit(0)
        if not groups:
            print(f"[FAIL] No version declarations discovered in {target}", file=sys.stderr)
        else:
            print(f"[FAIL] Version drift detected in {target}:", file=sys.stderr)
            for ver, items in groups.items():
                print(f"  - v{ver}:", file=sys.stderr)
                for item in items:
                    print(f"      {item}", file=sys.stderr)
        raise SystemExit(1)

    action = args.bump or args.set_version
    if action:
        notes = args.notes
        message = None if notes else args.message
        try:
            if notes:
                consistent, current, groups = check_consistency(target)
                if not groups:
                    raise RuntimeError(f"No version declarations discovered in: {target}")
                action_lower = action.lower()
                if current is None and action_lower in {"major", "minor", "patch"}:
                    raise RuntimeError(
                        "Version drift makes a relative bump baseline ambiguous. "
                        "Repair drift first or provide an explicit target SemVer."
                    )
                target_v = normalize_semver(action) if action_lower not in {"major", "minor", "patch"} else bump_semver(current, action_lower)
                changed = apply_version_bump(target, target_v, notes, dry_run=args.dry_run)
                success = True if args.dry_run else verify_versions(target)[0]
            else:
                success, target_v = bump_all(target, action, message=message, category=args.category, dry_run=args.dry_run)
                changed = plan_version_bump(target, target_v).keys() if args.dry_run else []
        except (RuntimeError, ValueError) as exc:
            print(f"[FAIL] {exc}", file=sys.stderr)
            raise SystemExit(1)
        if args.dry_run:
            print(f"[DRY RUN] Planned version target: v{target_v}")
            for path in changed:
                print(f"  - {path}")
            raise SystemExit(0)
        if success:
            print(f"[SUCCESS] Version synchronization to v{target_v} completed and verified.")
            raise SystemExit(0)
        print(f"[ERROR] Post-bump verification failed for v{target_v}.", file=sys.stderr)
        raise SystemExit(1)

    parser.print_help()


if __name__ == "__main__":
    main()
