"""Harrison CDSS Navigator execution wrapper.

Production-grade Clinical Decision Support System (CDSS) interface
grounded in Harrison's Principles of Internal Medicine (22nd Edition).
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

_PACKAGE_DIR = Path(os.environ.get("CDSS_PACKAGE_DIR", r"D:\01_Medical_Study\CDSS_Retrieval_Package"))
ROUTER_PATH_PKG = _PACKAGE_DIR / "02_Harrison_22" / "Index" / "cdss_qa_router.py"
ROUTER_PATH_SPLIT = Path(r"D:\01_Medical_Study\SPLIT Pdfs\harrison split\Index\rag_pipeline_output\cdss_qa_router.py")

ROUTER_PATH = str(ROUTER_PATH_PKG if ROUTER_PATH_PKG.exists() else ROUTER_PATH_SPLIT)
if not ROUTER_PATH_PKG.exists() and ROUTER_PATH_SPLIT.exists():
    print(f"[WARN] Harrison: packaged router missing; using UNPACKAGED build router: {ROUTER_PATH_SPLIT}", file=sys.stderr)


class HarrisonNavigator:
    """Interface to Harrison 22nd Edition CDSS Router."""

    def __init__(self, router_path: str = ROUTER_PATH):
        self.router_path = Path(router_path)

    def is_available(self) -> bool:
        return self.router_path.exists()

    def run_router_cli(self, args: List[str]) -> str:
        if not self.router_path.exists():
            return f"[ERROR] Router not found at: {self.router_path}"
        cmd = [sys.executable, str(self.router_path)] + args
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        return res.stdout or res.stderr

    def query(self, text: str, compress: bool = False) -> str:
        args = ["--query", text]
        if compress:
            args.append("--compress")
        return self.run_router_cli(args)

    def vignette(self, clinical_story: str) -> str:
        return self.run_router_cli(["--vignette", clinical_story])

    def outline(self, condition: str) -> str:
        return self.run_router_cli(["--outline", condition])

    def diff(self, disease: str) -> str:
        return self.run_router_cli(["--diff", disease])

    def validate_therapy(self, drug: str, condition: str = "") -> str:
        args = ["--validate-therapy", drug]
        if condition:
            args.append(condition)
        return self.run_router_cli(args)


def main():
    parser = argparse.ArgumentParser(
        description="Harrison 22nd Edition CDSS Navigator: Clinical QA & Case Retrieval."
    )
    parser.add_argument("--query", "-q", help="Clinical query or symptom")
    parser.add_argument("--vignette", "-v", help="Clinical case vignette")
    parser.add_argument("--outline", help="Medical outline checklist")
    parser.add_argument("--diff", help="Differential diagnosis")
    parser.add_argument("--validate-therapy", nargs="+", help="Validate therapy safety")
    parser.add_argument("--compress", action="store_true", help="Compress body spans")

    args = parser.parse_args()
    nav = HarrisonNavigator()

    if not nav.is_available():
        print(f"[ERROR] Router not found at: {nav.router_path}", file=sys.stderr)
        sys.exit(1)

    if args.outline:
        print(nav.outline(args.outline))
    elif args.diff:
        print(nav.diff(args.diff))
    elif args.validate_therapy:
        drug = args.validate_therapy[0]
        cond = args.validate_therapy[1] if len(args.validate_therapy) > 1 else ""
        print(nav.validate_therapy(drug, cond))
    elif args.vignette:
        print(nav.vignette(args.vignette))
    elif args.query:
        print(nav.query(args.query, compress=args.compress))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
