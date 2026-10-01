"""v2.6.3 — repository-wide scan: every executable script (root-level *.py
with an `if __name__ == "__main__":` block under `scripts/` -- i.e. something a human or an
automation could invoke directly, as opposed to a library module only ever
imported) that is CAPABLE of writing/mutating a file must carry an
explicit, greppable safety declaration. This is the requirement 8
"repository-wide test that identifies executable scripts capable of
mutation but lacking an explicit safety declaration" -- a structural check
against a FUTURE script being added to this repo without the same
guardrail discipline this release established, not a one-time audit of
the scripts that already exist.

"Capable of mutation" is a deliberately broad, conservative heuristic
(write-mode `open()`, `.write(`, `json.dump(`) -- false positives (a script
flagged that's actually harmless) are cheap to review case by case; false
negatives (a genuinely mutating script slipping through unflagged) are the
failure mode this test exists to prevent, so the heuristic errs toward
over-flagging rather than under-flagging.

"Explicit safety declaration" is any of: the literal v2.6.3 marker string
this release's guarded scripts all carry, an import of
`stages.mutation_guard` (the shared guardrail module), or an explicit
`--apply`/dry-run-by-default CLI contract (CP-07's pre-existing pattern in
checkpoint_migrate_v2_6_0.py, kept as a recognized alternative rather than
forced to re-word itself to match the newer marker).
"""
import ast
import glob
import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_ROOT = os.path.join(REPO_ROOT, "scripts")
SCRIPTS_ROOT = os.path.join(REPO_ROOT, "scripts")

MUTATION_PATTERNS = [
    re.compile(r"""open\([^)]*['"]w[b+]?['"]"""),  # open(..., 'w'), 'wb', 'w+', etc.
    re.compile(r"\.write\("),
    re.compile(r"json\.dump\("),
    re.compile(r"os\.replace\("),
    re.compile(r"shutil\.copyfile\("),
    re.compile(r"guarded_write_file\("),          # delegated write via stages.mutation_guard
    re.compile(r"migrate_checkpoint_schema\("),    # delegated checkpoint mutation
    re.compile(r"migrate_checkpoint_file\("),
    re.compile(r"write_protection_marker\("),
    re.compile(r"save_checkpoint\("),
    re.compile(r"mark_stage_complete\("),
]

SAFETY_DECLARATION_MARKERS = [
    "v2.6.3 SAFETY GUARDRAIL",
    "stages.mutation_guard",
    "from pipeline.stages import mutation_guard",
    "dry_run=True",  # explicit dry-run-default contract (e.g. checkpoint_migrate_v2_6_0.py's CLI)
    "Default is dry-run",
]

# Files intentionally out of scope for this scan:
# - test files and fixtures (pytest's own write patterns, not production runners)
# - anything under a backup/pycache directory
# - checkpoint_utils.py and pipeline/stages/*.py: LIBRARY modules with no __main__ guard,
#   never directly executed as a standalone script -- covered by their own
#   dedicated safety-mechanism tests (test_checkpoint_access_modes.py,
#   test_mutation_guard.py, test_adjudication_manifest.py) rather than this
#   generic scan, which targets DIRECT RUNNERS specifically (requirement 2's
#   own framing: "every root-level runner and chapter-specific script").
EXCLUDED_DIR_MARKERS = ("__pycache__", "_v2_6_2_backup", "_v2_6_3_backup",
                         "_phase0_phase1_backup", "_source_lines_fix_backup",
                         os.path.join("tests", ""))


def _has_main_guard(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            test = node.test
            if (isinstance(test, ast.Compare)
                    and isinstance(test.left, ast.Name) and test.left.id == "__name__"
                    and any(isinstance(c, ast.Constant) and c.value == "__main__"
                            for c in test.comparators)):
                return True
    return False


def _executable_root_scripts():
    scripts = []
    for path in sorted(glob.glob(os.path.join(SCRIPTS_ROOT, "**", "*.py"), recursive=True)):
        if any(marker in path for marker in EXCLUDED_DIR_MARKERS):
            continue
        with open(path, encoding="utf-8") as f:
            source = f.read()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        if _has_main_guard(tree):
            scripts.append((path, source))
    return scripts


def _is_mutation_capable(source):
    return any(p.search(source) for p in MUTATION_PATTERNS)


def _has_safety_declaration(source):
    return any(marker in source for marker in SAFETY_DECLARATION_MARKERS)


def test_at_least_one_executable_script_exists():
    """Sanity check that the scan is actually finding files -- an empty
    result would make every other assertion in this file vacuously true."""
    assert len(_executable_root_scripts()) >= 5


def test_every_mutation_capable_executable_script_has_a_safety_declaration():
    undeclared = []
    for path, source in _executable_root_scripts():
        if _is_mutation_capable(source) and not _has_safety_declaration(source):
            undeclared.append(os.path.basename(path))
    assert not undeclared, (
        f"The following executable script(s) can write/mutate files but have no "
        f"recognized safety declaration ({SAFETY_DECLARATION_MARKERS}): {undeclared}. "
        f"Add an explicit v2.6.3 SAFETY GUARDRAIL docstring block, route writes through "
        f"stages.mutation_guard, or adopt an explicit dry-run-by-default CLI contract."
    )


def test_known_guarded_scripts_are_all_flagged_as_mutation_capable():
    """Confirms the heuristic isn't accidentally blind to the exact scripts
    this release added guardrails to -- a scanner that never flags anything
    would trivially 'pass' the test above without proving anything."""
    known_mutating = {
        "run_stage_4_5d.py", "apply_ch05_adjudication.py",
        "regenerate_rag_optimised_ch05.py", "apply_source_lines_corrections_ch05.py",
        "rerun_stage6_ch05.py", "run_source_lines_precision.py",
        "migrate_ch05_schema_v2.py", "checkpoint_migrate_v2_6_0.py",
    }
    flagged = {os.path.basename(p) for p, src in _executable_root_scripts()
               if _is_mutation_capable(src)}
    missing = known_mutating - flagged
    assert not missing, f"expected these known-mutating scripts to be detected by the " \
                         f"heuristic, but they weren't: {missing}"


def test_known_guarded_scripts_all_declare_safety():
    known_mutating = {
        "run_stage_4_5d.py", "apply_ch05_adjudication.py",
        "regenerate_rag_optimised_ch05.py", "apply_source_lines_corrections_ch05.py",
        "rerun_stage6_ch05.py", "run_source_lines_precision.py",
        "migrate_ch05_schema_v2.py", "checkpoint_migrate_v2_6_0.py",
    }
    for path, source in _executable_root_scripts():
        if os.path.basename(path) in known_mutating:
            assert _has_safety_declaration(source), f"{os.path.basename(path)} missing safety declaration"
