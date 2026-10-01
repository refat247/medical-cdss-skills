"""
CDSS Retrieval Packager & Production Suite Compiler
Autonomous packager, pruner, path patcher, and federated search orchestrator
for medical textbook Clinical Decision Support Systems (CDSS).

Supports:
  - Davidson's Principles and Practice of Medicine (25th Edition)
  - Harrison's Principles of Internal Medicine (22nd Edition)
  - Fuster & Hurst's The Heart (15th Edition)
  - Kumar and Clark's Clinical Medicine (11th Edition)
  - Generic medical textbook RAG packages
"""

__version__ = "1.5.1"

import os
import sys
import shutil
import argparse
import json
import glob
import re
import subprocess
import inspect
from pathlib import Path
from typing import List, Dict, Any, Optional

# Enable UTF-8 console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Files strictly PROTECTED from pruning (Trust anchors, checksums, provenance)
PROTECTED_FILENAMES = {
    "CORPUS_OUTPUT_PROTECTED.json",
    "CORPUS_TRUST_STATUS.md",
    "CORPUS_TRUST_STATUS.json",
    "CORPUS_TRUST_STATUS.txt",
}

# Patterns of files to PRUNE (Build-time QA / cold backups)
PRUNE_PATTERNS = [
    "QualityScorecard.*",
    "ClinicalFidelity.*",
    "ClinicalFidelityGate.*",
    "ClinicalFidelityFailures.*",
    "CompletenessChecklist.*",
    "*.zip",
    "*.bak",
    "*_backup_*.json",
    "*_CHECKPOINT.json",
    "*_AUDIT_REPORT.md",
    "*_REAUDIT_REPORT.md",
    "*_L1L2_CoverageGaps.md",
    "*_SourceLinesPrecision.*",
    "*_SpotCheck.md",
    "*_Stage6_Validation.md",
    "*_Remap_Log.md",
    "*_Corrections_Log.md",
    "*_SCATTERED.json",
    "*_SUSPECTED_GAP.json",
    "*_COMPLETE_DISEASES.json",
    "*_FIGURE_AUDIT.md",
    "*_TABLE_AUDIT.md",
    "*_PREREADY_REPORT.md",
    "*_REPAIRED_S2.md",
]

# Subset of PRUNE_PATTERNS that is the EVIDENCE the RAG pipeline's trust classifier (and therefore the
# index compiler) reads. Pruning these before indexing leaves chapters "LEGACY"/excluded; run prune AFTER
# indexing, or pass --keep-trust-evidence.
TRUST_EVIDENCE_PATTERNS = [
    "*_CHECKPOINT.json", "ClinicalFidelity.*", "ClinicalFidelityGate.*", "ClinicalFidelityFailures.*",
    "CompletenessChecklist.*", "*_L1L2_CoverageGaps.md", "*_SourceLinesPrecision.*", "*_Stage6_Validation.md",
    "*_SCATTERED.json", "*_SUSPECTED_GAP.json", "*_COMPLETE_DISEASES.json",
]


def _matches_any(file_name: str, patterns) -> bool:
    for pattern in patterns:
        regex = "^" + pattern.replace(".", r"\.").replace("*", ".*") + "$"
        if re.match(regex, file_name, re.IGNORECASE):
            return True
    return False


# Patterns of files strictly PROTECTED from pruning
PROTECT_EXTENSIONS = {
    ".jpeg", ".jpg", ".png", ".webp", ".gif", ".svg",
    ".db", ".sqlite", ".sqlite3",
    ".gbnf",
}


def compress_excerpt(text: str, max_chars: int = 150, hard_cap: int = 0) -> str:
    """Clause-safe excerpt compression for clinical text.

    Returns whole sentences only, so qualifiers such as "unless...", "except..." or "contraindicated if..."
    are never cut off mid-sentence. If the first sentence alone is longer than max_chars it is returned
    whole, up to hard_cap (default 4 x max_chars). Only a single sentence longer than hard_cap is cut,
    at a word boundary, with an explicit "[truncated - see full chunk]" marker. " [...]" marks omitted
    later sentences.
    """
    if not text:
        return ""
    _abbreviations = frozenset({
        "approx", "vs", "fig", "figs", "no", "nos", "cf", "ca", "resp", "dr", "st", "prof", "mr", "mrs", "ms",
        "e.g", "i.e", "i.v", "i.m", "s.c", "p.o", "p.r", "q.d", "b.i.d", "t.i.d", "q.i.d", "o.d", "b.d", "t.d.s", "q.d.s",
        "esp", "incl", "min", "max", "conc", "wt", "ht", "tab", "tabs", "caps", "sol", "inj", "vol", "ref", "refs",
    })

    def _is_abbreviation_period(txt: str, period_idx: int) -> bool:
        # True when the '.' closes an abbreviation ("i.v.", "approx.", "vs."), not a sentence: cutting there
        # used to drop the dose that follows ("Start heparin i.v. [...]").
        m = re.search(r"([A-Za-z](?:\.?[A-Za-z])*)$", txt[:period_idx])
        if not m:
            return False
        tok = m.group(1).lower()
        return tok in _abbreviations or bool(re.fullmatch(r"(?:[a-z]\.)+[a-z]", tok))

    text = " ".join(text.split())
    if len(text) <= max_chars:
        return text
    hard_cap = hard_cap or max_chars * 4
    ends = [m.end() for m in re.finditer(r"(?<=[A-Za-z\)%\]])[.!?](?=\s+[A-Z0-9(\[]|$)", text)
            if not _is_abbreviation_period(text, m.start())]
    fitting = [e for e in ends if e <= max_chars]
    if fitting:
        cut = fitting[-1]
    else:
        cut = ends[0] if ends else len(text)
        if cut > hard_cap:
            space = text.rfind(" ", 0, hard_cap)
            return text[:space if space > 0 else hard_cap].rstrip(" ,;:") + " [truncated - see full chunk]"
    return text[:cut].strip() + (" [...]" if cut < len(text) else "")


class CDSSPackager:
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.remaining_hardcoded: List[str] = []

    def log(self, message: str):
        if self.verbose:
            print(f"[CDSS-PACKAGER] {message}")

    def prune_directory(self, target_dir: Path, dry_run: bool = False, keep_trust_evidence: bool = False) -> int:
        """Prunes build-time QA scorecards and backup archives while strictly safeguarding images.
        dry_run lists what WOULD be removed; keep_trust_evidence preserves the files the trust classifier needs."""
        if not target_dir.exists():
            self.log(f"Directory not found: {target_dir}")
            return 0

        self.log(f"Scanning for build-time QA and backup files to prune in: {target_dir}")
        deleted_count = 0

        for root, dirs, files in os.walk(target_dir):
            for file_name in files:
                file_path = Path(root) / file_name
                file_ext = file_path.suffix.lower()

                # Strictly protect trust files, clinical figures, and databases
                if file_name in PROTECTED_FILENAMES or file_ext in PROTECT_EXTENSIONS:
                    continue

                should_prune = _matches_any(file_name, PRUNE_PATTERNS)
                if should_prune and keep_trust_evidence and _matches_any(file_name, TRUST_EVIDENCE_PATTERNS):
                    should_prune = False

                if should_prune:
                    if dry_run:
                        self.log(f"  [dry-run] would remove {file_path}")
                        deleted_count += 1
                        continue
                    try:
                        file_path.unlink()
                        deleted_count += 1
                    except Exception as e:
                        self.log(f"  Warning: could not delete {file_path.name}: {e}")

        verb = "Would remove" if dry_run else "Removed"
        self.log(f"Pruning complete. {verb} {deleted_count} non-retrieval files.")
        if not dry_run and not keep_trust_evidence:
            self.log("NOTE: trust evidence (checkpoints, fidelity gates, Stage 6 reports) is pruned too; index (compiler) BEFORE "
                     "pruning or use --keep-trust-evidence.")
        return deleted_count

    def patch_paths(self, target_dir: Path) -> int:
        """Ensures all python router/client files use dynamic relative path resolution."""
        patched_count = 0
        self.log(f"Auditing Python routers for hardcoded absolute paths in: {target_dir}")

        for py_file in target_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
            except Exception:
                continue

            modified = False

            # 1. Patch Davidson CDSS client database path
            if "cdss_retrieval_client.py" in py_file.name and 'DEFAULT_DB_PATH = Path(r"D:' in content:
                replacement_davidson = (
                    'DEFAULT_DB_PATH = Path(__file__).resolve().parent / "DAVIDSON_25_CDSS_ENGINE.db"\n'
                    'if not DEFAULT_DB_PATH.exists():\n'
                    '    DEFAULT_DB_PATH = Path(__import__("os").environ.get("DAVIDSON_CORPUS_DIR", r"D:\\davidson_25_true\\TRUE_MD_WITH_IMAGES(v2.23.0_made)")) / "cdss_global_index" / "DAVIDSON_25_CDSS_ENGINE.db"'
                )
                content = re.sub(
                    r'DEFAULT_DB_PATH\s*=\s*Path\(r"D:\\.*?"\)',
                    lambda m: replacement_davidson,
                    content
                )
                modified = True

            # 2. Patch Hurst router catalog & index paths
            if "cdss_qa_router.py" in py_file.name and 'INDEX_DIR = r"D:' in content:
                content = re.sub(
                    r'INDEX_DIR\s*=\s*r"D:\\.*?"',
                    lambda m: 'INDEX_DIR = os.path.dirname(os.path.abspath(__file__))',
                    content
                )
                modified = True

            # 3. Patch Harrison router paths if hardcoded
            if "cdss_qa_router.py" in py_file.name and 'BASE_DIR = r"D:' in content:
                content = re.sub(
                    r'BASE_DIR\s*=\s*r"D:\\.*?"',
                    lambda m: 'BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))',
                    content
                )
                modified = True

            if modified:
                py_file.write_text(content, encoding="utf-8")
                patched_count += 1
                self.log(f"  Patched paths to dynamic relative resolution: {py_file.name}")

        # Patching is regex-on-source and silently no-ops if a router template changes: re-scan and say what is left.
        self.remaining_hardcoded = []
        for py_file in target_dir.rglob("*.py"):
            try:
                for n, line in enumerate(py_file.read_text(encoding="utf-8").splitlines(), 1):
                    if re.search(r"""['"][A-Za-z]:\\\\""", line) or re.search(r"""r['"][A-Za-z]:\\""", line):
                        self.remaining_hardcoded.append(f"{py_file.name}:{n}")
            except Exception:
                continue
        if self.remaining_hardcoded:
            self.log(f"  WARNING: {len(self.remaining_hardcoded)} hard-coded drive path(s) remain after patching, e.g. {self.remaining_hardcoded[:5]}")
        self.log(f"Path audit complete. Patched {patched_count} scripts.")
        return patched_count

    def sync_encoding_guard(self, package_dir: Path) -> Path:
        """Writes the package's runtime cdss_encoding_guard.py from the cdss-unicode-mojibake-guard skill,
        plus the package API (audit_corpus_encoding) used by the federated search, FastAPI adapter and verify."""
        skills_root = Path(os.environ.get("CDSS_SKILLS_ROOT", str(Path(__file__).resolve().parents[2])))
        src = skills_root / "cdss-unicode-mojibake-guard" / "scripts" / "guard.py"
        text = src.read_text(encoding="utf-8")
        version = re.search(r'__version__\s*=\s*"([^"]+)"', text)
        header = ('"""cdss_encoding_guard.py - runtime output guard for CDSS_Retrieval_Package.\n'
                  f"Generated by cdss-retrieval-packager from cdss-unicode-mojibake-guard v{version.group(1) if version else '?'}.\n"
                  'Do not edit here; edit the skill and re-run `packager.py federate`.\n"""\n')
        compat = ('\n\n# --- Package API (kept for existing consumers) ---\n'
                  'def audit_corpus_encoding(package_dir):\n'
                  '    """Audits the package; same result shape as the previous package guard."""\n'
                  '    return audit_directory(Path(package_dir))\n')
        body = text.split('\nif __name__ == "__main__":')[0]
        out = package_dir / "cdss_encoding_guard.py"
        out.write_text(header + body + compat, encoding="utf-8")
        self.log(f"Synced runtime encoding guard -> {out}")
        return out

    def generate_federated_search(self, package_dir: Path) -> Path:
        """Generates or updates the root cdss_federated_search.py script."""
        federated_script = package_dir / "cdss_federated_search.py"
        self.log(f"Generating federated multi-book search CLI at: {federated_script}")

        code = r'''"""
Unified Federated CDSS Retrieval Engine
Aggregates sub-millisecond clinical chunk retrieval across:
  1. Davidson's Principles and Practice of Medicine (25th Edition)
  2. Harrison's Principles of Internal Medicine (22nd Edition)
  3. Fuster & Hurst's The Heart (15th Edition)

Usage:
  python cdss_federated_search.py --query "Acute pulmonary embolism" --book all
  python cdss_federated_search.py --query "Infective endocarditis" --book hurst --top_k 2
  python cdss_federated_search.py --query "Diabetic ketoacidosis" --json
"""

import os
import sys
import argparse
import json
import re
from pathlib import Path
from typing import List, Dict, Any

# Configure unicode output for Windows shells
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = Path(__file__).resolve().parent

# Output-layer normalisation (µg -> mcg, LaTeX de-delimiting, ISMP dose rewrites) from the package's
# cdss_encoding_guard.py, which the packager keeps in sync with the cdss-unicode-mojibake-guard skill.
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
try:
    from cdss_encoding_guard import sanitize_for_llm
except ImportError:
    def sanitize_for_llm(text, **kwargs):
        return text

__COMPRESS_EXCERPT_SOURCE__


def clean_excerpt(text: str, max_chars: int) -> str:
    """Normalise for output first (so LaTeX markup does not eat the length budget), then compress."""
    return compress_excerpt(sanitize_for_llm(text or ""), max_chars=max_chars)

def _load_router_module(unique_name: str, idx_dir: Path):
    """Load <idx_dir>/cdss_qa_router.py under a UNIQUE module name. The four books ship routers with the same
    file name; importing them all as `cdss_qa_router` and reload()-ing made a later book overwrite the
    globals of an earlier book's live router (a Harrison query returned Kumar chunk ids)."""
    import importlib.util
    path = idx_dir / "cdss_qa_router.py"
    spec = importlib.util.spec_from_file_location(unique_name, str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[unique_name] = mod
    sys.path.insert(0, str(idx_dir))
    try:
        spec.loader.exec_module(mod)
    finally:
        if str(idx_dir) in sys.path:
            sys.path.remove(str(idx_dir))
    return mod


class CDSSFederatedSearch:
    def __init__(self):
        self.dav_client = None
        self.har_router = None
        self.hurst_router = None
        self.kumar_router = None
        
    def _init_davidson(self):
        if self.dav_client is None:
            dav_idx = ROOT_DIR / "01_Davidson_25" / "Index" / "cdss_global_index"
            if dav_idx.exists():
                sys.path.insert(0, str(dav_idx))
                try:
                    from cdss_retrieval_client import DavidsonCDSSClient
                    self.dav_client = DavidsonCDSSClient()
                finally:
                    if str(dav_idx) in sys.path:
                        sys.path.remove(str(dav_idx))

    def _init_harrison(self):
        if self.har_router is None:
            har_idx = ROOT_DIR / "02_Harrison_22" / "Index"
            if har_idx.exists():
                h_mod = _load_router_module("cdss_qa_router_harrison", har_idx)
                self.har_router = h_mod.HarrisonCDSSRouter()

    def _init_hurst(self):
        if self.hurst_router is None:
            hurst_idx = ROOT_DIR / "03_Hurst_The_Heart_15" / "Index"
            if hurst_idx.exists():
                hu_mod = _load_router_module("cdss_qa_router_hurst", hurst_idx)
                self.hurst_router = hu_mod.CDSSRouter()

    def _init_kumar(self):
        if self.kumar_router is None:
            kc_idx = ROOT_DIR / "04_Kumar_and_Clark_11" / "Index"
            if kc_idx.exists():
                kc_mod = _load_router_module("cdss_qa_router_kumar", kc_idx)
                self.kumar_router = kc_mod.CDSSRouter()

    def search(self, query: str, book: str = "all", top_k: int = 3, compress: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        results: Dict[str, List[Dict[str, Any]]] = {}

        # 1. Davidson
        if book in ("all", "davidson"):
            try:
                self._init_davidson()
            except Exception as e:
                results["Davidson_25"] = [{"error": f"init failed: {e}"}]
                init_failed = True
            else:
                init_failed = False
            if self.dav_client:
                try:
                    dav_raw = self.dav_client.search_chunks_lexical(query, top_k=top_k)
                    max_excerpt = 150 if compress else 300
                    results["Davidson_25"] = [
                        {
                            "chunk_id": item.get("full_chunk_id", item.get("chunk_id")),
                            "chapter": item.get("chapter_title"),
                            "topic": item.get("topic"),
                            "type": item.get("semantic_type"),
                            "score": round(abs(item.get("rank_score", 0)), 2),
                            "excerpt": clean_excerpt(item.get("body_text", ""), max_excerpt)
                        }
                        for item in dav_raw
                    ]
                except Exception as e:
                    results["Davidson_25"] = [{"error": str(e)}]
            elif not init_failed:
                results["Davidson_25"] = []

        # 2. Harrison
        if book in ("all", "harrison"):
            try:
                self._init_harrison()
            except Exception as e:
                results["Harrison_22"] = [{"error": f"init failed: {e}"}]
                init_failed = True
            else:
                init_failed = False
            if self.har_router:
                try:
                    try:
                        har_raw = self.har_router.retrieve_chunks(query, top_k=top_k, compress=compress)
                    except TypeError:
                        har_raw = self.har_router.retrieve_chunks(query, top_k=top_k)
                    max_excerpt = 150 if compress else 300
                    results["Harrison_22"] = [
                        {
                            "chunk_id": item.get("chunk_id"),
                            "section": item.get("section"),
                            "topic": item.get("topic"),
                            "type": item.get("type"),
                            "score": item.get("score"),
                            "excerpt": clean_excerpt(item.get("excerpt", ""), max_excerpt)
                        }
                        for item in har_raw
                    ]
                except Exception as e:
                    results["Harrison_22"] = [{"error": str(e)}]
            elif not init_failed:
                results["Harrison_22"] = []

        # 3. Hurst
        if book in ("all", "hurst"):
            try:
                self._init_hurst()
            except Exception as e:
                results["Hurst_The_Heart_15"] = [{"error": f"init failed: {e}"}]
                init_failed = True
            else:
                init_failed = False
            if self.hurst_router:
                try:
                    try:
                        hurst_raw = self.hurst_router.retrieve_chunks(query, top_k=top_k, compress=compress)
                    except TypeError:
                        hurst_raw = self.hurst_router.retrieve_chunks(query, top_k=top_k)
                    max_excerpt = 150 if compress else 300
                    results["Hurst_The_Heart_15"] = [
                        {
                            "chunk_id": item.get("chunk_id"),
                            "section": item.get("section"),
                            "topic": item.get("topic"),
                            "type": item.get("semantic_type", item.get("type")),
                            "score": item.get("score"),
                            "excerpt": clean_excerpt(item.get("preview") or item.get("excerpt") or "", max_excerpt)
                        }
                        for item in hurst_raw
                    ]
                except Exception as e:
                    results["Hurst_The_Heart_15"] = [{"error": str(e)}]
            elif not init_failed:
                results["Hurst_The_Heart_15"] = []

        # 4. Kumar & Clark
        if book in ("all", "kumar", "kumar_clark"):
            try:
                self._init_kumar()
            except Exception as e:
                results["Kumar_and_Clark_11"] = [{"error": f"init failed: {e}"}]
                init_failed = True
            else:
                init_failed = False
            if self.kumar_router:
                try:
                    try:
                        kc_raw = self.kumar_router.retrieve_chunks(query, top_k=top_k, compress=compress)
                    except TypeError:
                        kc_raw = self.kumar_router.retrieve_chunks(query, top_k=top_k)
                    max_excerpt = 150 if compress else 300
                    results["Kumar_and_Clark_11"] = [
                        {
                            "chunk_id": item.get("chunk_id"),
                            "section": item.get("section"),
                            "topic": item.get("topic"),
                            "type": item.get("semantic_type"),
                            "score": item.get("score"),
                            "excerpt": clean_excerpt(item.get("preview") or "", max_excerpt)
                        }
                        for item in kc_raw
                    ]
                except Exception as e:
                    results["Kumar_and_Clark_11"] = [{"error": str(e)}]
            elif not init_failed:
                results["Kumar_and_Clark_11"] = []

        return results

    def close(self):
        if self.dav_client:
            self.dav_client.close()

def _positive_int(s):
    v = int(s)
    if v < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return v


def main():
    parser = argparse.ArgumentParser(description="Federated CDSS Clinical Chunk Retrieval Engine")
    parser.add_argument("--query", "-q", required=True, help="Clinical query / disease / drug / symptom")
    parser.add_argument("--book", "-b", choices=["all", "davidson", "harrison", "hurst", "kumar"], default="all", help="Target textbook")
    parser.add_argument("--top_k", "-k", type=_positive_int, default=3, help="Max chunks per textbook (>= 1)")
    parser.add_argument("--compress", action="store_true", help="Extractive span compression for high-precision token saving")
    parser.add_argument("--json", action="store_true", help="Output raw JSON for downstream LLM prompts")
    
    args = parser.parse_args()
    engine = CDSSFederatedSearch()
    
    try:
        results = engine.search(args.query, book=args.book, top_k=args.top_k, compress=args.compress)
        # A per-book {"error": ...} entry is a FAILURE of that book, not a retrieved chunk.
        errors = {b: [c["error"] for c in chunks if isinstance(c, dict) and "error" in c] for b, chunks in results.items()}
        errors = {b: e for b, e in errors.items() if e}
        if not results:
            print("[ERROR] no book index was found for --book " + str(args.book) + "; nothing was searched.", file=sys.stderr)
            if args.json:
                print("{}")
            return 1
        failed = bool(errors)

        if args.json:
            try:
                from cdss_encoding_guard import safe_json_dumps
                print(safe_json_dumps(results, indent=2))
            except ImportError:
                print(json.dumps(results, ensure_ascii=False, indent=2))
            return 1 if failed else 0

        print("\n" + "=" * 75)
        print(f"FEDERATED CDSS RETRIEVAL: \"{args.query}\"")
        print("=" * 75)
        for b, errs in errors.items():
            print(f"[ERROR] {b}: {'; '.join(errs)}", file=sys.stderr)
            print(f"\n[{b.upper()}] - RETRIEVAL FAILED: {'; '.join(errs)}")

        total_retrieved = sum(1 for chunks in results.values() for c in chunks if not (isinstance(c, dict) and "error" in c))
        if total_retrieved == 0:
            if not failed:
                print("No matching clinical evidence found.")
            return 1 if failed else 0

        for book_name, chunks in results.items():
            chunks = [c for c in chunks if not (isinstance(c, dict) and "error" in c)]
            if book_name in errors:
                continue
            print(f"\n[{book_name.upper()}] - {len(chunks)} Evidence Chunks Found:")
            print("-" * 75)
            if not chunks:
                print("  No chunks matched for this textbook.")
                continue
            for i, chunk in enumerate(chunks, 1):
                chunk_id = chunk.get("chunk_id")
                topic = chunk.get("topic", "General")
                score = chunk.get("score", "N/A")
                stype = chunk.get("type", "clinical_knowledge")
                excerpt = chunk.get("excerpt", "").replace("\n", " ")
                max_chars = 100 if args.compress else 180
                excerpt = compress_excerpt(excerpt, max_chars=max_chars)
                print(f"  ({i}) [{chunk_id}] | Topic: {topic} | Type: {stype} | Score: {score}")
                print(f"      Excerpt: {excerpt}\n")
        print("=" * 75 + "\n")
        return 1 if failed else 0

    finally:
        engine.close()

if __name__ == "__main__":
    sys.exit(main())
'''
        # Inject the single canonical compress_excerpt implementation (no duplicated copy to drift)
        code = code.replace("__COMPRESS_EXCERPT_SOURCE__", inspect.getsource(compress_excerpt))
        federated_script.write_text(code, encoding="utf-8")
        return federated_script

    BOOKS = [
        ("01_Davidson_25", "Davidson's Principles and Practice of Medicine (25th Ed.)", "Davidson"),
        ("02_Harrison_22", "Harrison's Principles of Internal Medicine (22nd Ed.)", "Harrison"),
        ("03_Hurst_The_Heart_15", "Fuster & Hurst's The Heart (15th Ed.)", "Hurst"),
        ("04_Kumar_and_Clark_11", "Kumar and Clark's Clinical Medicine (11th Ed.)", "Kumar_and_Clark"),
    ]

    def _book_table(self, package_dir: Path, verification: Optional[Dict[str, Any]]) -> str:
        """Builds the README table from what is actually on disk and the latest verification result."""
        rows = ["| Folder | Textbook | Status | RAG files | Images |", "| :--- | :--- | :--- | ---: | ---: |"]
        for folder, title, key in self.BOOKS:
            d = package_dir / folder
            if not d.exists():
                rows.append(f"| `{folder}/` | *{title}* | Not packaged | 0 | 0 |")
                continue
            rag = sum(1 for _ in d.rglob("*_RAG_Optimised.md"))
            imgs = sum(1 for p in d.rglob("*") if p.suffix.lower() in (".jpeg", ".jpg", ".png", ".webp"))
            v = (verification or {}).get(key, "not verified")
            status = "Router smoke test PASS" if str(v).startswith("PASS") else f"Router: {v}"
            rows.append(f"| `{folder}/` | *{title}* | {status} | {rag} | {imgs} |")
        figs = (verification or {}).get("Figures")
        if figs:
            rows.append("")
            rows.append(f"Figure link check: {figs}")
        return "\n".join(rows)

    def generate_readme(self, package_dir: Path, verification: Optional[Dict[str, Any]] = None) -> Path:
        """Generates the root README.md from actual package contents (no hardcoded counts or status)."""
        readme_file = package_dir / "README.md"
        self.log(f"Generating package README documentation at: {readme_file}")

        doc = '''# CDSS Multi-Textbook Clinical Retrieval Package

A unified, lightweight, high-performance retrieval package containing production clinical knowledge bases, RAG-optimized text, discrete semantic chunks, multimodal visual assets, GraphRAG co-occurrence networks, and sub-millisecond retrieval routers.

---

## 1. Directory Structure & Summary

__BOOK_TABLE__

---

## 2. Quickstart Retrieval

### A. Unified Federated Search (All Books)
```bash
# Query all books
python cdss_federated_search.py --query "Atrial fibrillation anticoagulation" --top_k 2

# Output structured JSON for downstream LLM prompts
python cdss_federated_search.py --query "Infective endocarditis Duke criteria" --json
```

### B. Individual Textbook Routers

#### Harrison's Principles of Internal Medicine (22nd Edition)
```bash
python 02_Harrison_22/Index/cdss_qa_router.py --query "Atrial fibrillation" --compress
```

#### Fuster & Hurst's The Heart (15th Edition)
```bash
python 03_Hurst_The_Heart_15/Index/cdss_qa_router.py --query "Infective endocarditis" --compress
```

#### Kumar and Clark's Clinical Medicine (11th Edition)
```bash
python 04_Kumar_and_Clark_11/Index/cdss_qa_router.py --query "Heart failure" --compress
```

#### Davidson's Principles and Practice of Medicine (25th Edition)
```python
from cdss_retrieval_client import DavidsonCDSSClient

client = DavidsonCDSSClient()
results = client.search_chunks_lexical("Infective endocarditis", top_k=3)
client.close()
```
'''
        doc = doc.replace("__BOOK_TABLE__", self._book_table(package_dir, verification))
        readme_file.write_text(doc, encoding="utf-8")
        return readme_file

    def verify_package(self, package_dir: Path) -> Dict[str, Any]:
        """Runs health verification and test queries on all packaged routers."""
        self.log(f"Running automated health verification on: {package_dir}")
        results = {"Davidson": "SKIPPED", "Harrison": "SKIPPED", "Hurst": "SKIPPED", "Kumar_and_Clark": "SKIPPED", "Federated": "SKIPPED"}

        # 1. Verify Davidson
        dav_idx = package_dir / "01_Davidson_25" / "Index" / "cdss_global_index"
        if dav_idx.exists():
            sys.path.insert(0, str(dav_idx))
            try:
                from cdss_retrieval_client import DavidsonCDSSClient
                client = DavidsonCDSSClient()
                res = client.search_chunks_lexical("heart failure", top_k=1)
                client.close()
                if res and len(res) > 0:
                    results["Davidson"] = "PASS"
                    self.log("  [PASS] Davidson 25 SQLite FTS5 BM25 search verified.")
                else:
                    results["Davidson"] = "FAIL (No results)"
            except Exception as e:
                results["Davidson"] = f"FAIL ({e})"
                self.log(f"  [FAIL] Davidson verification failed: {e}")
            finally:
                if str(dav_idx) in sys.path:
                    sys.path.remove(str(dav_idx))

        # 2. Verify Harrison
        har_idx = package_dir / "02_Harrison_22" / "Index"
        if har_idx.exists():
            sys.path.insert(0, str(har_idx))
            try:
                import cdss_qa_router as h_mod
                router = h_mod.HarrisonCDSSRouter()
                chunks = router.retrieve_chunks("heart failure", top_k=1)
                if chunks and len(chunks) > 0:
                    results["Harrison"] = "PASS"
                    self.log("  [PASS] Harrison 22 Early-Exit GraphRAG router verified.")
                else:
                    results["Harrison"] = "FAIL (No results)"
            except Exception as e:
                results["Harrison"] = f"FAIL ({e})"
                self.log(f"  [FAIL] Harrison verification failed: {e}")
            finally:
                if str(har_idx) in sys.path:
                    sys.path.remove(str(har_idx))

        # 3. Verify Hurst
        hurst_idx = package_dir / "03_Hurst_The_Heart_15" / "Index"
        if hurst_idx.exists():
            sys.path.insert(0, str(hurst_idx))
            try:
                import importlib
                import cdss_qa_router as hu_mod
                importlib.reload(hu_mod)
                router = hu_mod.CDSSRouter()
                chunks = router.retrieve_chunks("heart failure", top_k=1)
                if chunks and len(chunks) > 0:
                    results["Hurst"] = "PASS"
                    self.log("  [PASS] Hurst 15 GraphRAG & Inverted Index router verified.")
                else:
                    results["Hurst"] = "FAIL (No results)"
            except Exception as e:
                results["Hurst"] = f"FAIL ({e})"
                self.log(f"  [FAIL] Hurst verification failed: {e}")
            finally:
                if str(hurst_idx) in sys.path:
                    sys.path.remove(str(hurst_idx))

        # 4. Verify Kumar & Clark
        kc_idx = package_dir / "04_Kumar_and_Clark_11" / "Index"
        if kc_idx.exists():
            sys.path.insert(0, str(kc_idx))
            try:
                import importlib
                import cdss_qa_router as kc_mod
                importlib.reload(kc_mod)
                router = kc_mod.CDSSRouter()
                chunks = router.retrieve_chunks("heart failure", top_k=1)
                if chunks and len(chunks) > 0:
                    results["Kumar_and_Clark"] = "PASS"
                    self.log("  [PASS] Kumar & Clark 11 GraphRAG & BM25 router verified.")
                else:
                    results["Kumar_and_Clark"] = "FAIL (No results)"
            except Exception as e:
                results["Kumar_and_Clark"] = f"FAIL ({e})"
                self.log(f"  [FAIL] Kumar & Clark verification failed: {e}")
            finally:
                if str(kc_idx) in sys.path:
                    sys.path.remove(str(kc_idx))

        # 4b. Verify every image link in packaged chapter text resolves to a file
        results["Figures"] = self.verify_figure_links(package_dir)

        # 5. Verify Federated Search
        fed_script = package_dir / "cdss_federated_search.py"
        if fed_script.exists():
            results["Federated"] = "READY"
            self.log("  [PASS] Federated search CLI entrypoint verified.")

        # 6. Verify Unicode & Anti-Mojibake Integrity
        guard_script = package_dir / "cdss_encoding_guard.py"
        global_guard_script = Path(os.environ.get("CDSS_SKILLS_ROOT", str(Path(__file__).resolve().parents[2]))) / "cdss-unicode-mojibake-guard" / "scripts" / "guard.py"
        if guard_script.exists():
            sys.path.insert(0, str(package_dir))
            try:
                import cdss_encoding_guard
                audit_res = cdss_encoding_guard.audit_corpus_encoding(package_dir)
                if audit_res["status"] == "PASS":
                    results["Encoding_Guard"] = f"PASS ({audit_res['clean_files']}/{audit_res['total_scanned']} clean)"
                    self.log(f"  [PASS] Unicode & Anti-Mojibake integrity verified: {audit_res['clean_files']}/{audit_res['total_scanned']} files clean.")
                else:
                    results["Encoding_Guard"] = f"FAIL ({len(audit_res['violations'])} violations)"
                    self.log(f"  [FAIL] Mojibake/Encoding violations detected: {len(audit_res['violations'])}")
            except Exception as e:
                results["Encoding_Guard"] = f"FAIL ({e})"
            finally:
                if str(package_dir) in sys.path:
                    sys.path.remove(str(package_dir))
        elif global_guard_script.exists():
            try:
                cmd = [sys.executable, str(global_guard_script), "audit", "--target-dir", str(package_dir)]
                proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
                if proc.returncode == 0:
                    results["Encoding_Guard"] = "PASS (Global Guard)"
                    self.log("  [PASS] Unicode & Anti-Mojibake integrity verified via global guard.")
                else:
                    results["Encoding_Guard"] = f"FAIL (Exit code {proc.returncode})"
                    self.log(f"  [FAIL] Global guard detected encoding violations.")
            except Exception as e:
                results["Encoding_Guard"] = f"FAIL ({e})"

        return results

    IMG_LINK_RE = re.compile(r"!\[[^\]]*\]\(\s*<?([^)>\s]+)>?(?:\s+\"[^\"]*\")?\s*\)")
    BARE_ASSET_RE = re.compile(r"(?<![\w/(])((?:assets/)?figures/[\w.\-]+\.(?:jpe?g|png|webp|gif))", re.IGNORECASE)

    def verify_figure_links(self, package_dir: Path) -> str:
        """Checks that image references in *_RAG_Optimised.md / *_chunks.md resolve to existing files."""
        total, missing = 0, []
        for md in list(package_dir.rglob("*_RAG_Optimised.md")) + list(package_dir.rglob("*_chunks.md")):
            try:
                text = md.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            refs = set(self.IMG_LINK_RE.findall(text)) | set(self.BARE_ASSET_RE.findall(text))
            for ref in refs:
                if re.match(r"^[a-z]+://", ref):
                    continue
                total += 1
                if not (md.parent / ref).exists() and not (md.parent.parent / ref).exists():
                    missing.append(f"{md.name} -> {ref}")
        if missing:
            self.log(f"  [FAIL] {len(missing)} of {total} figure link(s) do not resolve, e.g. {missing[:5]}")
            return f"FAIL ({len(missing)} of {total} missing)"
        self.log(f"  [PASS] All {total} figure link(s) resolve.")
        return f"PASS ({total} links)"

    def auto(self, package_dir: Path) -> Dict[str, Any]:
        """Runs prune, patch-paths, federate, and verify end-to-end."""
        self.log(f"Executing end-to-end CDSS packaging optimization on: {package_dir}")
        self.prune_directory(package_dir)
        self.patch_paths(package_dir)
        self.sync_encoding_guard(package_dir)
        self.generate_federated_search(package_dir)
        verification = self.verify_package(package_dir)
        self.generate_readme(package_dir, verification)
        self.log("Package optimization complete.")
        return verification


def main():
    parser = argparse.ArgumentParser(description="CDSS Retrieval Package Optimizer & Compiler")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # prune
    p_prune = subparsers.add_parser("prune", help="Prune build-time QA scorecards and cold backup zips")
    p_prune.add_argument("--package-dir", "-p", required=True, help="Target CDSS Retrieval Package directory")
    p_prune.add_argument("--dry-run", action="store_true", help="List what would be removed; delete nothing")
    p_prune.add_argument("--keep-trust-evidence", action="store_true",
                         help="Keep checkpoints / fidelity gates / Stage 6 reports (needed by the index compiler's trust check)")

    # patch-paths
    p_patch = subparsers.add_parser("patch-paths", help="Audit and patch hardcoded paths to dynamic relative paths")
    p_patch.add_argument("--package-dir", "-p", required=True, help="Target CDSS Retrieval Package directory")

    # federate
    p_fed = subparsers.add_parser("federate", help="Generate root cdss_federated_search.py and README.md")
    p_fed.add_argument("--package-dir", "-p", required=True, help="Target CDSS Retrieval Package directory")

    # verify
    p_ver = subparsers.add_parser("verify", help="Run automated retrieval smoke tests across all packaged routers")
    p_ver.add_argument("--package-dir", "-p", required=True, help="Target CDSS Retrieval Package directory")

    # auto
    p_auto = subparsers.add_parser("auto", help="Run prune, patch-paths, federate, and verify in one command")
    p_auto.add_argument("--package-dir", "-p", required=True, help="Target CDSS Retrieval Package directory")

    args = parser.parse_args()
    packager = CDSSPackager()

    target_dir = Path(args.package_dir).resolve()

    if args.command in ("prune", "patch-paths", "verify", "auto") and not target_dir.is_dir():
        print(f"[CDSS-PACKAGER] ERROR: package directory not found: {target_dir}", file=sys.stderr)
        sys.exit(2)
    if args.command == "prune":
        packager.prune_directory(target_dir, dry_run=args.dry_run, keep_trust_evidence=args.keep_trust_evidence)
    elif args.command == "patch-paths":
        packager.patch_paths(target_dir)
        if packager.remaining_hardcoded:
            sys.exit(1)
    elif args.command == "federate":
        packager.sync_encoding_guard(target_dir)
        packager.generate_federated_search(target_dir)
        packager.generate_readme(target_dir)
    elif args.command in ("verify", "auto"):
        results = packager.verify_package(target_dir) if args.command == "verify" else packager.auto(target_dir)
        print(f"\nVerification Results: {results}")
        failed = [k for k, v in results.items() if str(v).startswith("FAIL")]
        if failed:
            print(f"[CDSS-PACKAGER] FAILED checks: {failed}", file=sys.stderr)
            sys.exit(1)
        if not any(str(results.get(b, "")).startswith("PASS") for b in ("Davidson", "Harrison", "Hurst", "Kumar_and_Clark")):
            print("[CDSS-PACKAGER] No textbook router was verified (all SKIPPED): an empty or wrong package directory "
                  "is not a pass.", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
