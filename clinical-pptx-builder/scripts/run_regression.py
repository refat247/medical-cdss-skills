#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures"
PRE = ROOT / "scripts" / "pptx_preflight.py"
LINT = ROOT / "scripts" / "clinical_lint.py"
cases = [
    ("good.pptx", False, False),
    ("overflow.pptx", True, False),
    ("contrast.pptx", True, False),
    ("clinical_bad.pptx", False, True),
    ("missing_font.pptx", True, False),
    ("dense_citations.pptx", False, False),
]
failed = []
for name, preflight_error, lint_error in cases:
    path = FIX / name
    p = subprocess.run(["python3", str(PRE), str(path), "--min-pt", "18", "--expect-aspect", "16:9", "--fail-on", "error"], text=True, capture_output=True)
    l = subprocess.run(["python3", str(LINT), str(path), "--jurisdiction", "none"], text=True, capture_output=True)
    got_p = "SUMMARY: ERROR=0" not in p.stdout
    got_l = "SUMMARY: ERROR=0" not in l.stdout
    print(f"{name}: preflight_error={got_p} clinical_error={got_l}")
    if got_p != preflight_error or got_l != lint_error:
        failed.append(name)
if failed:
    raise SystemExit("Regression mismatch: " + ", ".join(failed))
print("Regression suite passed")
