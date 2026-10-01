"""Kumar & Clark 11th Edition CDSS Navigator execution wrapper.

Production-grade Clinical Decision Support System (CDSS) interface
grounded in Kumar and Clark's Clinical Medicine (11th Edition 2026).
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Primary production router path
_PACKAGE_DIR = Path(os.environ.get("CDSS_PACKAGE_DIR", r"D:\01_Medical_Study\CDSS_Retrieval_Package"))
ROUTER_PATH = str(_PACKAGE_DIR / "04_Kumar_and_Clark_11" / "Index" / "cdss_qa_router.py")
INDEX_DIR = Path(ROUTER_PATH).parent


class KumarNavigator:
    """Interface to the Kumar & Clark 11th Edition CDSS Router and Index Assets."""

    def __init__(self, router_path: str = ROUTER_PATH):
        self.router_path = Path(router_path)
        self.index_dir = self.router_path.parent

    def is_available(self) -> bool:
        return self.router_path.exists()

    MAX_OUTPUT_WORDS = 1200  # Strict budget ceiling per Antigravity token economy protocol

    def _enforce_token_budget(self, text: str) -> str:
        words = text.split()
        if len(words) > self.MAX_OUTPUT_WORDS:
            truncated = " ".join(words[:self.MAX_OUTPUT_WORDS])
            return truncated + f"\n\n... [TRUNCATED: Exceeded {self.MAX_OUTPUT_WORDS}-word budget guard. Use --compress for precision excerpts.]"
        return text

    def run_router_cli(self, args: List[str]) -> str:
        """Executes the underlying cdss_qa_router.py CLI."""
        if not self.router_path.exists():
            return f"[ERROR] Router not found at: {self.router_path}"
        cmd = [sys.executable, str(self.router_path)] + args
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        output = res.stdout or res.stderr
        return self._enforce_token_budget(output)

    def query(self, text: str, top_k: int = 3, compress: bool = False, json_output: bool = False) -> str:
        """Run a clinical symptom or diagnostic query."""
        args = ["--query", text, "--top_k", str(top_k)]
        if compress:
            args.append("--compress")
        if json_output:
            args.append("--json")
        return self.run_router_cli(args)

    def vignette(self, clinical_story: str, top_k: int = 3, compress: bool = False) -> str:
        """Decompose and retrieve evidence for a complex clinical case vignette."""
        args = ["--vignette", clinical_story, "--top_k", str(top_k)]
        if compress:
            args.append("--compress")
        return self.run_router_cli(args)

    def outline(self, condition: str) -> str:
        """Retrieve structured prompt-ready medical checklist / concept subtree."""
        subtrees_path = self.index_dir / "kumar_clark_concept_subtrees.json"
        if not subtrees_path.exists():
            return f"[ERROR] Subtrees asset not found at {subtrees_path}"

        with open(subtrees_path, "r", encoding="utf-8") as f:
            subtrees: Dict[str, Any] = json.load(f)

        target = condition.strip().lower()
        matches = []
        for k, v in subtrees.items():
            if target in k.lower():
                matches.append((k, v))

        if not matches:
            return f"[OUTLINE] No direct subtree matches found for '{condition}'. Try broader term."

        lines = [f"===========================================================================",
                 f"KUMAR & CLARK 11TH ED CONCEPT OUTLINE: \"{condition}\"",
                 f"==========================================================================="]
        for key, entry in matches[:5]:
            lines.append(f"\n[CONCEPT] {entry.get('parent_concept', key)}")
            lines.append(f"  Subfacets ({entry.get('subfacets_count', len(entry.get('subfacets', [])))}):")
            for sub in entry.get("subfacets", []):
                lines.append(f"    - {sub}")
        lines.append("===========================================================================")
        return "\n".join(lines)

    def diff(self, condition: str) -> str:
        """Retrieve differential diagnosis comparators and 'vs.' entries."""
        diff_path = self.index_dir / "kumar_clark_differential_comparators.json"
        if not diff_path.exists():
            return f"[ERROR] Differential comparators asset not found at {diff_path}"

        with open(diff_path, "r", encoding="utf-8") as f:
            differentials: List[Dict[str, Any]] = json.load(f)

        target = condition.strip().lower()
        matches = [d for d in differentials if target in d.get("parent_concept", "").lower() or target in d.get("differential_entry", "").lower()]

        if not matches:
            # Fallback to concept subtrees for diagnostic/differentiation entries
            return self.outline(condition)

        lines = [f"===========================================================================",
                 f"KUMAR & CLARK 11TH ED DIFFERENTIAL COMPARATORS: \"{condition}\"",
                 f"==========================================================================="]
        for d in matches:
            lines.append(f"- Concept: {d.get('parent_concept')}")
            lines.append(f"  Entry: {d.get('differential_entry')}")
            lines.append(f"  Relationship: {d.get('relationship')}\n")
        lines.append("===========================================================================")
        return "\n".join(lines)

    def validate_therapy(self, drug: str, condition: str = "") -> str:
        """Validate drug indication and clinical safety guardrails."""
        matrix_path = self.index_dir / "kumar_clark_drug_disease_safety_matrix.json"
        if not matrix_path.exists():
            return f"[ERROR] Drug safety matrix not found at {matrix_path}"

        with open(matrix_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        matrix = data.get("matrix", {})
        drug_norm = drug.strip().lower()

        if drug_norm in matrix:
            entry = matrix[drug_norm]
            return (
                f"===========================================================================\n"
                f"KUMAR & CLARK 11TH ED DRUG SAFETY GUARDRAIL: {drug.upper()}\n"
                f"===========================================================================\n"
                f"  Indication: {entry.get('general_indication')}\n"
                f"  Safety Precautions: {entry.get('safety_precautions')}\n"
                f"==========================================================================="
            )

        # Partial match
        for d_key, entry in matrix.items():
            if drug_norm in d_key or d_key in drug_norm:
                return (
                    f"===========================================================================\n"
                    f"KUMAR & CLARK 11TH ED DRUG SAFETY GUARDRAIL: {d_key.upper()}\n"
                    f"===========================================================================\n"
                    f"  Indication: {entry.get('general_indication')}\n"
                    f"  Safety Precautions: {entry.get('safety_precautions')}\n"
                    f"==========================================================================="
                )

        return f"[THERAPY GUARDRAIL] Drug '{drug}' not explicitly indexed in current guardrail matrix. Refer to clinical chapters."


def main():
    parser = argparse.ArgumentParser(
        description="Kumar & Clark 11th Edition CDSS Navigator: Single-Book Clinical QA & Case Retrieval."
    )
    parser.add_argument("--query", "-q", help="Clinical query, symptom, or disease workup")
    parser.add_argument("--vignette", "-v", help="Clinical case vignette for multi-sentence decomposition")
    parser.add_argument("--top_k", "-k", type=int, default=3, help="Max results to return (default: 3)")
    parser.add_argument("--compress", action="store_true", help="Compress evidence chunks to 120-word precision micro-windows")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    parser.add_argument("--outline", help="Extract prompt-ready medical checklist / concept subtree outline")
    parser.add_argument("--diff", help="Lookup differential diagnosis comparators")
    parser.add_argument("--validate-therapy", nargs="+", help="Validate drug therapy (e.g. --validate-therapy Sacubitril)")

    args = parser.parse_args()
    nav = KumarNavigator()

    if not nav.is_available():
        print(f"[ERROR] Router not found at: {nav.router_path}", file=sys.stderr)
        sys.exit(1)

    if args.outline:
        print(nav.outline(args.outline))
        return

    if args.diff:
        print(nav.diff(args.diff))
        return

    if args.validate_therapy:
        drug = args.validate_therapy[0]
        cond = args.validate_therapy[1] if len(args.validate_therapy) > 1 else ""
        print(nav.validate_therapy(drug, cond))
        return

    query = args.query or args.vignette
    if not query:
        parser.print_help()
        return

    if args.vignette:
        print(nav.vignette(args.vignette, top_k=args.top_k, compress=args.compress))
    else:
        print(nav.query(args.query, top_k=args.top_k, compress=args.compress, json_output=args.json))


if __name__ == "__main__":
    main()
