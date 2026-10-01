#!/usr/bin/env python3
"""Repo-wide QA gate: catches crash-class defects that per-skill unit tests missed.

Checks
  1. every non-test .py file compiles
  2. pyflakes: no undefined names, no use-before-assignment, no redefinition of unused names
  3. every CLI script (argparse or __main__) answers `--help` with exit 0

Exit code 1 if any check fails. Run from anywhere:  python qa/check_all.py
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {"qa", ".git", "__pycache__", "tests", "fixtures", "node_modules", ".venv"}
# One-off, archived repair/release scripts that run work at import time; compile-checked only.
ONE_OFF = ("scripts/chapter_repairs/", "scripts/releases/")
FLAKE_FATAL = re.compile(r"undefined name|referenced before assignment|redefinition of unused|syntax", re.I)


def py_files() -> list[Path]:
    out = []
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        out += [Path(dp) / f for f in fns if f.endswith(".py") and not f.startswith("conftest")]
    return sorted(out)


def check_compile(files) -> list[str]:
    bad = []
    for f in files:
        try:
            compile(f.read_bytes(), str(f), "exec")  # syntax check only; writes no .pyc
        except SyntaxError as e:
            bad.append(f"{f.relative_to(ROOT)}:{e.lineno}: {e.msg}")
    return bad


def check_pyflakes(files) -> list[str]:
    res = subprocess.run([sys.executable, "-m", "pyflakes", *map(str, files)], capture_output=True, text=True)
    if res.returncode not in (0, 1):
        return [f"pyflakes unavailable: {res.stderr.strip()[:120]} (pip install pyflakes)"]
    return [l.replace(str(ROOT) + os.sep, "") for l in res.stdout.splitlines() if FLAKE_FATAL.search(l)]


def check_help(files) -> list[str]:
    bad = []
    pypath = os.pathsep.join(str(p) for p in ROOT.iterdir() if p.is_dir() and not p.name.startswith("."))
    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        if f.name.startswith("__") or any(o in rel for o in ONE_OFF):
            continue
        src = f.read_text(encoding="utf-8", errors="replace")
        if "argparse" not in src:  # scripts without argparse would execute real work on --help
            continue
        env = {**os.environ, "PYTHONPATH": pypath, "PYTHONIOENCODING": "utf-8"}
        try:
            r = subprocess.run([sys.executable, f.name, "--help"], cwd=f.parent, env=env, stdin=subprocess.DEVNULL,
                               capture_output=True, text=True, timeout=30)
        except subprocess.TimeoutExpired:
            bad.append(f"{rel}: --help timed out")
            continue
        if r.returncode != 0:
            bad.append(f"{rel}: --help exit {r.returncode}: {(r.stderr.strip().splitlines() or ['?'])[-1][:100]}")
    return bad


def main() -> int:
    files = py_files()
    failed = 0
    for name, fn in (("compile", check_compile), ("pyflakes (fatal classes)", check_pyflakes), ("--help smoke", check_help)):
        bad = fn(files)
        print(f"[{'FAIL' if bad else ' OK '}] {name}: {len(bad)} problem(s) across {len(files)} files")
        for b in bad:
            print("       ", b)
        failed += bool(bad)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
