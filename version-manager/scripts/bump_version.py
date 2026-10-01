"""Universal Semantic Version Bumper & Synchronizer.

Discovers, inspects, updates, and verifies version declarations across:
- Agent Skills (SKILL.md frontmatter, provenance comments)
- Python packages (pyproject.toml, setup.cfg, setup.py, __init__.py)
- Node/TypeScript packages (package.json)
- Documentation (README.md "Installed (vX.Y.Z)", title headings)
- Changelogs (CHANGELOG.md Keep a Changelog releases)
- Test files (tests/test_*version*.py pinned assertions)
"""
import argparse
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple



DRY_RUN = False


def _write_file(path: str, content: str) -> None:
    """Single write choke point: honours dry-run, preserves newlines (no CRLF->LF churn), and replaces the file
    atomically so an interrupted write cannot leave a half-written declaration file."""
    if DRY_RUN:
        return
    tmp = f"{path}.tmp-bump"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    os.replace(tmp, path)


def parse_semver(v_str: str) -> Tuple[int, int, int, Optional[str]]:
    """Parses a SemVer string into (major, minor, patch, prerelease)."""
    m = re.match(r"^v?(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?$", v_str.strip())
    if not m:
        raise ValueError(f"Invalid SemVer string: '{v_str}' (expected MAJOR.MINOR.PATCH)")
    return int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4)


def bump_semver(current: str, part: str) -> str:
    """Computes next SemVer string given bump type ('major', 'minor', 'patch')."""
    major, minor, patch, _ = parse_semver(current)
    part_lower = part.lower()
    if part_lower == "major":
        return f"{major + 1}.0.0"
    elif part_lower == "minor":
        return f"{major}.{minor + 1}.0"
    elif part_lower == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        # Validate custom version string
        parse_semver(part)
        return part.lstrip("v")


def _today_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class VersionDeclaration:
    def __init__(self, file_path: str, file_type: str, current_version: str, line_num: int, line_content: str):
        self.file_path = file_path
        self.file_type = file_type
        self.current_version = current_version
        self.line_num = line_num
        self.line_content = line_content

    def __repr__(self):
        rel = os.path.basename(self.file_path)
        return f"[{self.file_type}] {rel}:{self.line_num} -> {self.current_version}"


def discover_versions(root_dir: str) -> List[VersionDeclaration]:
    """Scans root_dir for all standard version declarations."""
    declarations = []
    root = os.path.abspath(root_dir)

    for dirpath, dirnames, filenames in os.walk(root):
        # Exclude git, cache, and virtual environment directories
        dirnames[:] = [d for d in dirnames if d not in {".git", ".pytest_cache", "__pycache__", "node_modules", "venv", ".venv"}]

        for fname in filenames:
            fpath = os.path.join(dirpath, fname)

            # 1. SKILL.md
            if fname == "SKILL.md":
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for idx, line in enumerate(f, start=1):
                        m = re.match(r"^version:\s*[\"']?([0-9][0-9A-Za-z.+\-]*)[\"']?\s*$", line.rstrip("\r\n"))
                        if m:
                            declarations.append(VersionDeclaration(fpath, "SKILL_FRONTMATTER", m.group(1), idx, line.strip()))
                        m_hdr = re.search(r"^#\s+.*\(v([0-9][0-9A-Za-z.+\-]*)\)", line.strip())
                        if m_hdr:
                            declarations.append(VersionDeclaration(fpath, "SKILL_HEADER", m_hdr.group(1), idx, line.strip()))

            # 2. package.json
            elif fname == "package.json":
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for idx, line in enumerate(f, start=1):
                        m = re.search(r'"version"\s*:\s*"([0-9][0-9A-Za-z.+\-]*)"', line)
                        if m:
                            declarations.append(VersionDeclaration(fpath, "PACKAGE_JSON", m.group(1), idx, line.strip()))
                            break

            # 3. pyproject.toml
            elif fname == "pyproject.toml":
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for idx, line in enumerate(f, start=1):
                        m = re.match(r'^version\s*=\s*["\']([0-9][0-9A-Za-z.+\-]*)["\']', line.strip())
                        if m:
                            declarations.append(VersionDeclaration(fpath, "PYPROJECT_TOML", m.group(1), idx, line.strip()))
                            break

            # 4. test files with pinned version assertions (must precede generic .py)
            elif fname.startswith("test_") and ("version" in fname or "consistency" in fname):
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for idx, line in enumerate(f, start=1):
                        m = re.search(r'assert\s+(?:__version__|PIPELINE_VERSION|VERSION|skill_v|changelog_v)\s*==\s*["\']([0-9][0-9A-Za-z.+\-]*)["\']', line)
                        if m:
                            declarations.append(VersionDeclaration(fpath, "TEST_ASSERTION", m.group(1), idx, line.strip()))

            # 5. Python scripts with __version__, PIPELINE_VERSION, or VERSION constants
            elif fname.endswith(".py"):
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for idx, line in enumerate(f, start=1):
                        m_init = re.match(r'^__version__\s*=\s*["\']([0-9][0-9A-Za-z.+\-]*)["\']', line.strip())
                        if m_init:
                            declarations.append(VersionDeclaration(fpath, "PYTHON_INIT", m_init.group(1), idx, line.strip()))
                        m_const = re.match(r'^(?:PIPELINE_VERSION|SKILL_VERSION|VERSION|APP_VERSION)\s*=\s*["\']([0-9][0-9A-Za-z.+\-]*)["\']', line.strip())
                        if m_const:
                            declarations.append(VersionDeclaration(fpath, "PYTHON_CONST", m_const.group(1), idx, line.strip()))

            # 6. README.md
            elif fname == "README.md":
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for idx, line in enumerate(f, start=1):
                        m_inst = re.search(r"Installed\s*\(v([0-9][0-9A-Za-z.+\-]*)\)", line)
                        if m_inst:
                            declarations.append(VersionDeclaration(fpath, "README_INSTALLED", m_inst.group(1), idx, line.strip()))
                        m_hdr = re.search(r"^#\s+.*\(v([0-9][0-9A-Za-z.+\-]*)\)", line)
                        if m_hdr:
                            declarations.append(VersionDeclaration(fpath, "README_HEADER", m_hdr.group(1), idx, line.strip()))

            # 7. CHANGELOG.md (latest release heading)
            elif fname == "CHANGELOG.md":
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for idx, line in enumerate(f, start=1):
                        m = re.match(r"^##\s*\[([0-9][0-9A-Za-z.+\-]*)\]", line.strip())
                        if m:
                            declarations.append(VersionDeclaration(fpath, "CHANGELOG_LATEST", m.group(1), idx, line.strip()))
                            break

    return declarations


def check_consistency(root_dir: str) -> Tuple[bool, Optional[str], Dict[str, List[VersionDeclaration]]]:
    """Verifies that all discovered version declarations in root_dir are mutually consistent."""
    decls = discover_versions(root_dir)
    if not decls:
        return True, None, {}

    versions = {}
    for d in decls:
        versions.setdefault(d.current_version, []).append(d)

    is_consistent = (len(versions) == 1)
    primary_version = next(iter(versions.keys())) if is_consistent else None
    return is_consistent, primary_version, versions


def apply_version_bump(
    root_dir: str,
    target_version: str,
    release_notes: Optional[str] = None,
    dry_run: bool = False,
) -> List[str]:
    """Updates all discovered version declarations to target_version (each file atomically).
    With dry_run=True nothing is written; the list of files that WOULD change is returned."""
    global DRY_RUN
    DRY_RUN = dry_run
    try:
        return _apply_version_bump(root_dir, target_version, release_notes)
    finally:
        DRY_RUN = False


def _apply_version_bump(root_dir: str, target_version: str, release_notes: Optional[str] = None) -> List[str]:
    decls = discover_versions(root_dir)
    if not decls:
        raise RuntimeError(f"No version declarations discovered in: {root_dir}")

    modified_files = set()
    root = os.path.abspath(root_dir)

    # 1. Update SKILL.md
    skill_path = os.path.join(root, "SKILL.md")
    if os.path.exists(skill_path):
        with open(skill_path, "r", encoding="utf-8", newline="") as f:
            content = f.read()
        new_content = re.sub(r"^(version:[ \t]*[\"']?)([0-9][0-9A-Za-z.+\-]*)", rf"\g<1>{target_version}", content, flags=re.MULTILINE)
        new_content = re.sub(r'^(#\s+.*\(v)([0-9][0-9A-Za-z.+\-]*)(\))', rf"\g<1>{target_version}\g<3>", new_content, flags=re.MULTILINE)
        new_content = re.sub(r'(skill_version:\s*["\'])([0-9][0-9A-Za-z.+\-]*)(["\'])', rf"\g<1>{target_version}\g<3>", new_content)
        if new_content != content:
            _write_file(skill_path, new_content)
            modified_files.add(skill_path)

    # 2. Update package.json
    pkg_path = os.path.join(root, "package.json")
    if os.path.exists(pkg_path):
        with open(pkg_path, "r", encoding="utf-8", newline="") as f:
            content = f.read()
        new_content = re.sub(r'("version"\s*:\s*")([0-9][0-9A-Za-z.+\-]*)(")', rf"\g<1>{target_version}\g<3>", content)
        if new_content != content:
            _write_file(pkg_path, new_content)
            modified_files.add(pkg_path)

    # 3. Update pyproject.toml
    pyproj_path = os.path.join(root, "pyproject.toml")
    if os.path.exists(pyproj_path):
        with open(pyproj_path, "r", encoding="utf-8", newline="") as f:
            content = f.read()
        new_content = re.sub(r'^(version\s*=\s*["\'])([0-9][0-9A-Za-z.+\-]*)(["\'])', rf"\g<1>{target_version}\g<3>", content, flags=re.MULTILINE)
        if new_content != content:
            _write_file(pyproj_path, new_content)
            modified_files.add(pyproj_path)

    # 4. Update __init__.py files
    for d in decls:
        if d.file_type == "PYTHON_INIT":
            with open(d.file_path, "r", encoding="utf-8", newline="") as f:
                content = f.read()
            new_content = re.sub(r'(__version__\s*=\s*["\'])([0-9][0-9A-Za-z.+\-]*)(["\'])', rf"\g<1>{target_version}\g<3>", content)
            new_content = re.sub(r'(\(v)([0-9][0-9A-Za-z.+\-]*)(\))', rf"\g<1>{target_version}\g<3>", new_content)
            if new_content != content:
                _write_file(d.file_path, new_content)
                modified_files.add(d.file_path)

    # 5. Update Python constant declarations (PIPELINE_VERSION, etc.)
    for d in decls:
        if d.file_type == "PYTHON_CONST":
            with open(d.file_path, "r", encoding="utf-8", newline="") as f:
                content = f.read()
            new_content = re.sub(r'^((?:PIPELINE_VERSION|SKILL_VERSION|VERSION|APP_VERSION)\s*=\s*["\'])([0-9][0-9A-Za-z.+\-]*)(["\'])', rf"\g<1>{target_version}\g<3>", content, flags=re.MULTILINE)
            if new_content != content:
                _write_file(d.file_path, new_content)
                modified_files.add(d.file_path)

    # 6. Update README.md
    readme_path = os.path.join(root, "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8", newline="") as f:
            content = f.read()
        new_content = re.sub(r"(Installed\s*\(v)([0-9][0-9A-Za-z.+\-]*)(\))", rf"\g<1>{target_version}\g<3>", content)
        new_content = re.sub(r"^([#]+\s+.*\(v)([0-9][0-9A-Za-z.+\-]*)(\))", rf"\g<1>{target_version}\g<3>", new_content, flags=re.MULTILINE)
        new_content = re.sub(r"(`v)([0-9][0-9A-Za-z.+\-]*)(`)", rf"\g<1>{target_version}\g<3>", new_content)
        if new_content != content:
            _write_file(readme_path, new_content)
            modified_files.add(readme_path)

    # 7. Update CHANGELOG.md
    changelog_path = os.path.join(root, "CHANGELOG.md")
    if os.path.exists(changelog_path):
        with open(changelog_path, "r", encoding="utf-8", newline="") as f:
            content = f.read()

        today = _today_iso()
        # Check if this release heading already exists
        if not re.search(rf"^##\s*\[{re.escape(target_version)}\]", content, re.MULTILINE):
            # Format release section
            body = release_notes.strip() if release_notes else (
                "### Added\n- Feature additions for this release.\n\n"
                "### Changed\n- Backward-compatible improvements.\n\n"
                "### Fixed\n- Bug fixes and optimizations."
            )
            new_entry = f"\n## [{target_version}] - {today}\n\n{body}\n"

            # Insert above the first existing release heading
            first_release = re.search(r"^##\s*\[[0-9][0-9A-Za-z.+\-]*\]", content, re.MULTILINE)
            if first_release:
                idx = first_release.start()
                new_content = content[:idx] + new_entry.lstrip("\n") + "\n" + content[idx:]
            else:
                new_content = content + "\n" + new_entry

            _write_file(changelog_path, new_content)
            modified_files.add(changelog_path)

    # 8. Update test assertions
    for d in decls:
        if d.file_type == "TEST_ASSERTION":
            with open(d.file_path, "r", encoding="utf-8", newline="") as f:
                content = f.read()
            new_content = re.sub(
                r'(assert\s+(?:__version__|PIPELINE_VERSION|VERSION|skill_v|changelog_v)\s*==\s*["\'])([0-9][0-9A-Za-z.+\-]*)(["\'])',
                rf"\g<1>{target_version}\g<3>",
                content
            )
            # Also update test function names like test_pipeline_version_is_2_23_0
            target_slug = target_version.replace(".", "_")
            new_content = re.sub(
                r'(def\s+test_[a-zA-Z0-9_]*_is_)(\d+_\d+_\d+)(\(\):)',
                rf"\g<1>{target_slug}\g<3>",
                new_content
            )
            if new_content != content:
                _write_file(d.file_path, new_content)
                modified_files.add(d.file_path)

    return sorted(list(modified_files))


def verify_versions(root_dir: str) -> Tuple[bool, Optional[str], List[VersionDeclaration]]:
    """Verifies that all discovered version declarations in root_dir are mutually consistent.
    
    Returns:
        (is_consistent, canonical_version, list_of_mismatched_declarations)
    """
    is_consistent, primary_v, groups = check_consistency(root_dir)
    if is_consistent:
        return True, primary_v, []
    
    # Identify minority/drifted declarations
    # Find the version with the highest count (mode) as candidate canonical
    sorted_groups = sorted(groups.items(), key=lambda x: len(x[1]), reverse=True)
    canonical = sorted_groups[0][0] if sorted_groups else None
    mismatches = []
    for ver, items in sorted_groups[1:]:
        mismatches.extend(items)
    return False, canonical, mismatches


def bump_all(
    root_dir: str,
    bump_type: str,
    message: Optional[str] = None,
    category: Optional[str] = None,
    notes: Optional[str] = None,
) -> Tuple[bool, str]:
    """Computes target version, updates all files, and appends a changelog entry.
    
    Args:
        root_dir: Target directory path
        bump_type: 'major', 'minor', 'patch', or explicit version string
        message: Summary message for the changelog
        category: Changelog category (e.g. 'Added', 'Changed', 'Fixed')
        
    Returns:
        (success, target_version)
    """
    is_consistent, current_v, groups = check_consistency(root_dir)
    if not current_v:
        # If drift exists, select highest version as baseline
        versions = sorted(list(groups.keys()), key=lambda s: parse_semver(s)[:3], reverse=True)
        current_v = versions[0]

    target_v = bump_semver(current_v, bump_type)

    release_notes = None
    if notes:
        release_notes = notes.strip() + "\n"      # full release notes are used verbatim (was wrapped as ONE bullet)
    elif message:
        cat = category.strip().capitalize() if category else ("Added" if bump_type == "minor" else "Changed")
        release_notes = f"### {cat}\n- {message.strip()}\n"

    apply_version_bump(root_dir, target_v, release_notes=release_notes)
    
    verified, new_v, _ = check_consistency(root_dir)
    if verified and new_v == target_v:
        return True, target_v
    return False, target_v


def discover_skill_suite(parent_dir: str, name_filter: Optional[str] = None) -> List[Tuple[str, str]]:
    """Scans parent_dir for all skill or package subdirectories.
    
    Args:
        parent_dir: Parent directory containing multiple skills
        name_filter: Optional substring filter for skill directory names
        
    Returns:
        List of (skill_name, absolute_skill_path)
    """
    suite = []
    parent = os.path.abspath(parent_dir)
    if not os.path.exists(parent):
        return []

    # First check immediate child directories
    for entry in sorted(os.listdir(parent)):
        entry_path = os.path.join(parent, entry)
        if not os.path.isdir(entry_path):
            continue
        if entry in {".git", ".pytest_cache", "__pycache__", "node_modules", "venv", ".venv", "tmp"}:
            continue
        if name_filter and name_filter.lower() not in entry.lower():
            continue
        if os.path.exists(os.path.join(entry_path, "SKILL.md")) or os.path.exists(os.path.join(entry_path, "pyproject.toml")):
            suite.append((entry, entry_path))

    # If none found at depth 1 and no filter was given, search up to depth 3
    if not suite and not name_filter:
        for root, dirs, files in os.walk(parent):
            dirs[:] = [d for d in dirs if d not in {".git", ".pytest_cache", "__pycache__", "node_modules", "venv", ".venv"}]
            rel_depth = os.path.relpath(root, parent).count(os.sep)
            if rel_depth > 3:
                continue
            if "SKILL.md" in files:
                skill_name = os.path.basename(root)
                suite.append((skill_name, root))

    return suite


def audit_suite(
    parent_dir: str,
    verify: bool = False,
    inspect: bool = False,
    name_filter: Optional[str] = None
) -> Tuple[bool, List[Dict[str, Any]]]:
    """Audits version consistency across all skills in a suite.
    
    Returns:
        (all_passed, results_list)
    """
    suite = discover_skill_suite(parent_dir, name_filter=name_filter)
    if not suite:
        filter_msg = f" matching '{name_filter}'" if name_filter else ""
        print(f"[SUITE] No skill packages found in: {parent_dir}{filter_msg}")
        return True, []

    results = []
    all_consistent = True

    for name, skill_path in suite:
        decls = discover_versions(skill_path)
        is_consistent, canonical, groups = check_consistency(skill_path)
        
        has_tests = os.path.exists(os.path.join(skill_path, "tests"))
        if not is_consistent:
            all_consistent = False

        results.append({
            "name": name,
            "path": skill_path,
            "declarations": len(decls),
            "version": canonical or "DRIFT",
            "is_consistent": is_consistent,
            "drift_groups": groups if not is_consistent else {},
            "has_tests": has_tests,
        })

    print("\n" + "=" * 80)
    print(f" SKILL SUITE VERIFICATION REPORT: {parent_dir}")
    print("=" * 80)
    print(f"{'Skill Package':<36} | {'Version':<10} | {'Decls':<6} | {'Status'}")
    print("-" * 80)

    for r in results:
        status_str = "[OK] Consistent" if r["is_consistent"] else f"[FAIL] Drift ({len(r['drift_groups'])} versions)"
        v_str = f"v{r['version']}" if r['version'] != "DRIFT" else "DRIFT"
        print(f"{r['name']:<36} | {v_str:<10} | {r['declarations']:<6} | {status_str}")

    print("-" * 80)
    passed_cnt = sum(1 for r in results if r["is_consistent"])
    total_cnt = len(results)

    if all_consistent:
        print(f" Suite Health: {passed_cnt}/{total_cnt} skills 100% verified with 0 drift.\n")
    else:
        print(f" [ALERT] Drift detected in {total_cnt - passed_cnt} skill(s)!\n", file=sys.stderr)
        for r in results:
            if not r["is_consistent"]:
                print(f"  * {r['name']}:", file=sys.stderr)
                for ver, items in r["drift_groups"].items():
                    print(f"      - v{ver}: {len(items)} file(s)", file=sys.stderr)
        print()

    return all_consistent, results


def main():
    parser = argparse.ArgumentParser(description="Universal Semantic Version Bumper & Synchronizer")
    parser.add_argument("target", nargs="?", default=None, help="Target repository or skill directory")
    parser.add_argument("--dir", "-d", default=None, help="Alternative flag for target directory")
    parser.add_argument("--suite", "-s", help="Audit or operate on all skills in a parent workspace directory")
    parser.add_argument("--filter", "-f", help="Optional substring filter for skill names in suite mode")
    parser.add_argument("--inspect", action="store_true", help="Inspect and display all version declarations without modifying")
    parser.add_argument("--verify", action="store_true", help="Verify 100%% mutual consistency across all version declarations")
    parser.add_argument("--bump", help="Bump type (major, minor, patch) or explicit version string (e.g. 1.3.0)")
    parser.add_argument("--set-version", help="Explicit target version string (e.g. 2.25.0)")
    parser.add_argument("--message", "-m", help="Summary message for changelog")
    parser.add_argument("--notes", help="Full markdown release notes content for CHANGELOG.md")
    parser.add_argument("--dry-run", action="store_true", help="Show which files a bump WOULD change; write nothing")
    parser.add_argument("--category", default="Changed", help="Changelog category (Added, Changed, Fixed, etc.)")

    args = parser.parse_args()

    if args.suite and (args.bump or args.set_version):
        print("Error: --suite is audit-only; run the bump on one skill directory at a time.", file=sys.stderr)
        sys.exit(2)

    # Suite mode branch
    if args.suite:
        suite_dir = os.path.abspath(args.suite)
        if not os.path.exists(suite_dir):
            print(f"Error: Suite directory not found: {suite_dir}", file=sys.stderr)
            sys.exit(1)
        all_ok, _ = audit_suite(suite_dir, verify=args.verify, inspect=args.inspect, name_filter=args.filter)
        sys.exit(0 if all_ok else 1)

    target_path = args.target or args.dir or "."
    target_dir = os.path.abspath(target_path)

    if not os.path.exists(target_dir):
        print(f"Error: Target directory not found: {target_dir}", file=sys.stderr)
        sys.exit(1)

    if args.inspect:
        decls = discover_versions(target_dir)
        print(f"\nDiscovered {len(decls)} version declaration(s) in: {target_dir}")
        print("-" * 60)
        for d in decls:
            print(f"  {d}")
        is_consistent, v, groups = check_consistency(target_dir)
        print("-" * 60)
        if is_consistent:
            print(f"Status: OK (Consistent version: {v})\n")
        else:
            print(f"Status: DRIFT DETECTED across {len(groups)} distinct version(s):")
            for ver, items in groups.items():
                print(f"  - v{ver}: {len(items)} file(s)")
            print()
        sys.exit(0 if is_consistent else 1)

    if args.verify:
        is_consistent, v, groups = check_consistency(target_dir)
        if is_consistent:
            print(f"[OK] All version declarations in {os.path.basename(target_dir)} agree on v{v}")
            sys.exit(0)
        else:
            print(f"[FAIL] Version drift detected in {target_dir}:", file=sys.stderr)
            for ver, items in groups.items():
                print(f"  - v{ver}:", file=sys.stderr)
                for it in items:
                    print(f"      {it}", file=sys.stderr)
            sys.exit(1)

    bump_action = args.bump or args.set_version
    if bump_action:
        if args.dry_run:
            cur = check_consistency(target_dir)[1] or "0.0.0"
            tv = bump_semver(cur, bump_action)
            files = apply_version_bump(target_dir, tv, dry_run=True)
            print(f"[DRY-RUN] v{cur} -> v{tv}: would modify {len(files)} file(s):")
            for f in files:
                print(f"  {f}")
            sys.exit(0)
        success, target_v = bump_all(
            root_dir=target_dir,
            bump_type=bump_action,
            message=args.message,
            category=args.category,
            notes=args.notes,
        )
        if success:
            print(f"\n[SUCCESS] Version bump to v{target_v} complete and 100% consistent!")
            sys.exit(0)
        else:
            print(f"\n[ERROR] Post-bump consistency check failed for v{target_v}!", file=sys.stderr)
            sys.exit(1)

    # Default if no action arguments
    parser.print_help()


if __name__ == "__main__":
    main()

