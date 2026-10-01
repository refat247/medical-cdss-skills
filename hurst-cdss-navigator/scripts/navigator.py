"""Hurst CDSS Navigator execution wrapper.

Production-grade Clinical Decision Support System (CDSS) interface
grounded in Fuster & Hurst's The Heart (15th Edition).
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

_PACKAGE_DIR = Path(os.environ.get("CDSS_PACKAGE_DIR", r"D:\01_Medical_Study\CDSS_Retrieval_Package"))
ROUTER_PATH_PKG = _PACKAGE_DIR / "03_Hurst_The_Heart_15" / "Index" / "cdss_qa_router.py"
ROUTER_PATH_SPLIT = Path(r"D:\01_Medical_Study\SPLIT Pdfs\Fuster & Hurst's The Heart_split\Index\rag_pipeline_output\cdss_qa_router.py")
ROUTER_PATH_LEGACY = Path(r"D:\01_Medical_Study\Fcps\cardiology_book\Fuster & Hurst's The Heart_split\Index\rag_pipeline_output\cdss_qa_router.py")

def _resolve_router() -> str:
    for p in (ROUTER_PATH_PKG, ROUTER_PATH_SPLIT, ROUTER_PATH_LEGACY):
        if p.exists():
            if p != ROUTER_PATH_PKG:
                print(f"[WARN] Hurst: packaged router missing; using UNPACKAGED build router: {p}", file=sys.stderr)
            return str(p)
    return str(ROUTER_PATH_PKG)  # fallback for error messages

ROUTER_PATH = _resolve_router()


class HurstNavigator:
    """Interface to the underlying Hurst CDSS Router engine."""

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
        description="Hurst 15th Edition CDSS Navigator: Clinical Cardiology QA & Case Retrieval."
    )
    parser.add_argument("--query", "-q", help="Clinical query or symptom")
    parser.add_argument("--vignette", "-v", help="Clinical case vignette")
    parser.add_argument("--outline", help="Medical outline checklist")
    parser.add_argument("--diff", help="Differential diagnosis")
    parser.add_argument("--validate-therapy", nargs="+", help="Validate therapy safety")
    parser.add_argument("--comorbidities", help="Syndromic comorbidity lookup")
    parser.add_argument("--compress", action="store_true", help="Compress body spans")
    parser.add_argument("--interactive", action="store_true", help="Interactive physician shell")

    args = parser.parse_args()
    nav = HurstNavigator()

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
    elif args.comorbidities:
        print(nav.run_router_cli(["--comorbidities", args.comorbidities]))
    elif args.interactive:
        print(nav.run_router_cli(["--interactive"]))
    elif args.vignette:
        print(nav.vignette(args.vignette))
    elif args.query:
        print(nav.query(args.query, compress=args.compress))
    else:
        parser.print_help()


def run_navigator(args: Optional[List[str]] = None) -> int:
    """Convenience runner for CLI or programmatic execution."""
    if args is not None:
        sys.argv = [sys.argv[0]] + args
    main()
    return 0


if __name__ == "__main__":
    main()

