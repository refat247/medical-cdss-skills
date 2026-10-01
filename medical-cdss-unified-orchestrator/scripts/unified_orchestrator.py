"""
Unified Medical CDSS Orchestrator (v1.5.0)
Cross-Book Clinical Decision Support Navigator across:
  1. Davidson's Principles and Practice of Medicine (25th Edition)
  2. Harrison's Principles of Internal Medicine (22nd Edition)
  3. Fuster & Hurst's The Heart (15th Edition)
  4. Kumar and Clark's Clinical Medicine (11th Edition 2026)

Usage:
  python unified_orchestrator.py --query "Acute pulmonary embolism" --book all
  python unified_orchestrator.py --query "Takotsubo cardiomyopathy" --book hurst --compress
  python unified_orchestrator.py --vignette "65yo male with anterior STEMI, pulmonary edema, BP 85/55, Cr 2.6"
  python unified_orchestrator.py --validate-therapy "Sacubitril/valsartan" "heart failure"
  python unified_orchestrator.py --diff "Meningitis"
  python unified_orchestrator.py --outline "Diabetic ketoacidosis"
"""

__version__ = "1.5.0"

import os

import sys
import argparse
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SKILLS_ROOT = Path(os.environ.get("CDSS_SKILLS_ROOT", str(Path(__file__).resolve().parents[2])))
PACKAGE_DIR = Path(os.environ.get("CDSS_PACKAGE_DIR", r"D:\01_Medical_Study\CDSS_Retrieval_Package"))
FEDERATED_SEARCH_SCRIPT = PACKAGE_DIR / "cdss_federated_search.py"

if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))
try:
    from cdss_encoding_guard import sanitize_for_llm, safe_json_dumps, enforce_utf8_environment
    enforce_utf8_environment()
except ImportError:
    pass

# Local router locations (within package or source repos)
HARRISON_ROUTER_PKG = PACKAGE_DIR / "02_Harrison_22" / "Index" / "cdss_qa_router.py"
HURST_ROUTER_PKG = PACKAGE_DIR / "03_Hurst_The_Heart_15" / "Index" / "cdss_qa_router.py"
KUMAR_ROUTER_PKG = PACKAGE_DIR / "04_Kumar_and_Clark_11" / "Index" / "cdss_qa_router.py"

# Fallback source locations
# Fallback to UNPACKAGED build outputs (not trust-verified). Used only with a loud warning.
HARRISON_ROUTER_SRC = Path(os.environ.get("CDSS_HARRISON_BUILD_ROUTER", r"D:\01_Medical_Study\SPLIT Pdfs\harrison split\Index\rag_pipeline_output\cdss_qa_router.py"))
HURST_ROUTER_SRC = Path(os.environ.get("CDSS_HURST_BUILD_ROUTER", r"D:\01_Medical_Study\SPLIT Pdfs\Fuster & Hurst's The Heart_split\Index\rag_pipeline_output\cdss_qa_router.py"))


ACTIVE_BOOK = "all"          # set from --book; every mode honours it
ALLOW_PARTIAL = False        # --allow-partial: accept results from fewer books than were requested
SKIPPED: List[str] = []      # selected books that could not be queried in this run


def _selected(name: str) -> bool:
    return ACTIVE_BOOK in ("all", name)


def _note_skipped(name: str) -> None:
    if name not in SKIPPED:
        SKIPPED.append(name)


def _warn_build_fallback(book: str, path: Path) -> None:
    print(f"[WARN] {book}: packaged router missing; using UNPACKAGED build output (not trust-verified): {path}",
          file=sys.stderr)


def _finish(exit_codes: List[int], what: str) -> int:
    """No source reachable is a failure; so is a PARTIAL result (some selected book missing) unless --allow-partial.
    (Previously one answering book out of four exited 0 with only a printed note.)"""
    if not exit_codes:
        print(f"[ERROR] {what}: no textbook source was available (package: {PACKAGE_DIR})", file=sys.stderr)
        return 1
    code = max(exit_codes)
    if SKIPPED and code == 0 and not ALLOW_PARTIAL:
        print(f"[PARTIAL RESULT] {what}: these selected books were NOT queried: {', '.join(SKIPPED)}. "
              f"Exit 3 (use --allow-partial to accept).", file=sys.stderr)
        return 3
    if SKIPPED:
        print(f"[PARTIAL RESULT] not queried: {', '.join(SKIPPED)}", file=sys.stderr)
    return code


def _davidson(query: str, exit_codes: List[int], label: str, as_json: bool = False) -> None:
    if not _selected("davidson"):
        return
    if FEDERATED_SEARCH_SCRIPT.exists():
        print(f"\n[DAVIDSON 25TH ED - {label}]")
        exit_codes.append(run_federated_query(query, book="davidson", top_k=3, as_json=as_json, compress=True))
    else:
        print("\n[DAVIDSON 25TH ED] Federated search script not available.")
        _note_skipped("davidson")


def get_harrison_router() -> Optional[Path]:
    if not _selected("harrison"):
        return None
    if HARRISON_ROUTER_PKG.exists():
        return HARRISON_ROUTER_PKG
    if HARRISON_ROUTER_SRC.exists():
        _warn_build_fallback("Harrison", HARRISON_ROUTER_SRC)
        return HARRISON_ROUTER_SRC
    _note_skipped("harrison")
    return None


def get_hurst_router() -> Optional[Path]:
    if not _selected("hurst"):
        return None
    if HURST_ROUTER_PKG.exists():
        return HURST_ROUTER_PKG
    if HURST_ROUTER_SRC.exists():
        _warn_build_fallback("Hurst", HURST_ROUTER_SRC)
        return HURST_ROUTER_SRC
    _note_skipped("hurst")
    return None


def get_kumar_router() -> Optional[Path]:
    if not _selected("kumar"):
        return None
    if KUMAR_ROUTER_PKG.exists():
        return KUMAR_ROUTER_PKG
    _note_skipped("kumar")      # no unpackaged fallback exists for Kumar & Clark
    return None


MAX_OUTPUT_WORDS = 1500  # Token economy ceiling across federated outputs


def enforce_token_budget(text: str) -> str:
    words = text.split()
    if len(words) > MAX_OUTPUT_WORDS:
        truncated = " ".join(words[:MAX_OUTPUT_WORDS])
        return truncated + f"\n\n... [TRUNCATED: Exceeded {MAX_OUTPUT_WORDS}-word budget guard. Query individual books with --book <name> for deeper detail.]"
    return text


def run_federated_query(query: str, book: str = "all", top_k: int = 3, as_json: bool = False, compress: bool = False) -> int:
    """Executes a cross-book query using cdss_federated_search.py."""
    if not FEDERATED_SEARCH_SCRIPT.exists():
        print(f"[ERROR] Federated search script not found at: {FEDERATED_SEARCH_SCRIPT}", file=sys.stderr)
        return 1

    cmd = [sys.executable, str(FEDERATED_SEARCH_SCRIPT), "--query", query, "--book", book, "--top_k", str(top_k)]
    if as_json:
        cmd.append("--json")
    if compress:
        cmd.append("--compress")

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if as_json:
        print(proc.stdout)
    else:
        print(enforce_token_budget(proc.stdout))
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)
    return proc.returncode



def run_case_vignette(vignette: str, as_json: bool = False) -> int:
    """Decomposes and analyzes a clinical case vignette across Davidson, Harrison, Hurst, and Kumar & Clark."""
    del SKIPPED[:]          # per-run state
    print("=" * 80)
    print(" UNIFIED CLINICAL CASE VIGNETTE ANALYSIS")
    print(f" Case: {vignette}")
    print("=" * 80)

    exit_codes = []

    # 1. Route to Davidson (Core Spine)
    if not _selected("davidson"):
        pass
    elif FEDERATED_SEARCH_SCRIPT.exists():
        print("\n[DAVIDSON 25TH ED - CORE MEDICINE EVALUATION]")
        code = run_federated_query(vignette, book="davidson", top_k=3, as_json=as_json, compress=True)
        exit_codes.append(code)
    else:
        print("\n[DAVIDSON 25TH ED] Federated search script not available.")
        _note_skipped("davidson")

    # 2. Route to Harrison (General Medicine)
    h_router = get_harrison_router()
    if h_router:
        print("\n[HARRISON 22ND ED - INTERNAL MEDICINE EVALUATION]")
        cmd = [sys.executable, str(h_router), "--vignette", vignette]
        if as_json:
            cmd.append("--json")
        res = subprocess.run(cmd)
        exit_codes.append(res.returncode)
    else:
        print("\n[HARRISON 22ND ED] Router not available.")

    # 3. Route to Hurst (Cardiology)
    hu_router = get_hurst_router()
    if hu_router:
        print("\n[HURST 15TH ED - CARDIOLOGY EVALUATION]")
        cmd = [sys.executable, str(hu_router), "--vignette", vignette]
        if as_json:
            cmd.append("--json")
        res = subprocess.run(cmd)
        exit_codes.append(res.returncode)
    else:
        print("\n[HURST 15TH ED] Router not available.")

    # 4. Route to Kumar & Clark (Clinical Medicine)
    kc_router = get_kumar_router()
    if kc_router:
        print("\n[KUMAR & CLARK 11TH ED - CLINICAL MEDICINE EVALUATION]")
        cmd = [sys.executable, str(kc_router), "--vignette", vignette]
        if as_json:
            cmd.append("--json")
        res = subprocess.run(cmd)
        exit_codes.append(res.returncode)
    else:
        print("\n[KUMAR & CLARK 11TH ED] Router not available.")

    return _finish(exit_codes, "query")


def run_therapy_validation(drug: str, condition: str) -> int:
    """Validates drug safety and indications across Davidson, Hurst, Harrison, and Kumar & Clark."""
    del SKIPPED[:]          # per-run state
    print("=" * 80)
    print(f" UNIFIED DRUG THERAPY SAFETY VERIFICATION: {drug} for '{condition}'")
    print("=" * 80)

    exit_codes = []

    # 1. Davidson 25th Edition
    if not _selected("davidson"):
        pass
    elif not FEDERATED_SEARCH_SCRIPT.exists():
        _note_skipped("davidson")
    else:
        print("\n[DAVIDSON 25TH ED - DRUG DOSING & SAFETY EVIDENCE]")
        code = run_federated_query(f"{drug} {condition}", book="davidson", top_k=2, compress=True)
        exit_codes.append(code)

    hu_router = get_hurst_router()
    if hu_router:
        print("\n[HURST'S THE HEART - CARDIAC DRUG SAFETY MATRIX]")
        res = subprocess.run([sys.executable, str(hu_router), "--validate-therapy", drug, condition])
        exit_codes.append(res.returncode)

    h_router = get_harrison_router()
    if h_router:
        print("\n[HARRISON'S INTERNAL MEDICINE - DRUG SAFETY MATRIX]")
        res = subprocess.run([sys.executable, str(h_router), "--validate-therapy", drug, condition])
        exit_codes.append(res.returncode)

    kc_router = get_kumar_router()
    if kc_router:
        print("\n[KUMAR & CLARK 11TH ED - CLINICAL MEDICINE DRUG SAFETY MATRIX]")
        args = [sys.executable, str(kc_router), "--validate-therapy", drug]
        if condition:
            args.append(condition)
        res = subprocess.run(args)
        exit_codes.append(res.returncode)

    return _finish(exit_codes, "query")


def run_diff(comparator: str) -> int:
    """Checks differential diagnosis look-alikes across Harrison, Hurst, and Kumar & Clark."""
    del SKIPPED[:]          # per-run state
    print(f"=== DIFFERENTIAL COMPARATORS FOR: {comparator} ===")
    exit_codes = []
    _davidson(f"{comparator} differential diagnosis", exit_codes, "DIFFERENTIAL EVIDENCE")

    h_router = get_harrison_router()
    if h_router:
        print("\n[Harrison 22nd Edition Comparators]:")
        res = subprocess.run([sys.executable, str(h_router), "--diff", comparator])
        exit_codes.append(res.returncode)

    hu_router = get_hurst_router()
    if hu_router:
        print("\n[Hurst 15th Edition Comparators]:")
        res = subprocess.run([sys.executable, str(hu_router), "--diff", comparator])
        exit_codes.append(res.returncode)

    kc_router = get_kumar_router()
    if kc_router:
        print("\n[Kumar & Clark 11th Edition Comparators]:")
        res = subprocess.run([sys.executable, str(kc_router), "--diff", comparator])
        exit_codes.append(res.returncode)

    return _finish(exit_codes, "query")


def run_outline(concept: str) -> int:
    """Retrieves structured prompt-ready clinical checklists across Harrison, Hurst, and Kumar & Clark."""
    del SKIPPED[:]          # per-run state
    print(f"=== PROMPT-READY CLINICAL OUTLINE: {concept} ===")
    exit_codes = []
    _davidson(concept, exit_codes, "CORE SPINE")

    h_router = get_harrison_router()
    if h_router:
        print("\n[Harrison 22nd Edition Concept Tree]:")
        res = subprocess.run([sys.executable, str(h_router), "--outline", concept])
        exit_codes.append(res.returncode)

    hu_router = get_hurst_router()
    if hu_router:
        print("\n[Hurst 15th Edition Concept Tree]:")
        res = subprocess.run([sys.executable, str(hu_router), "--outline", concept])
        exit_codes.append(res.returncode)

    kc_router = get_kumar_router()
    if kc_router:
        print("\n[Kumar & Clark 11th Edition Concept Tree]:")
        res = subprocess.run([sys.executable, str(kc_router), "--outline", concept])
        exit_codes.append(res.returncode)

    return _finish(exit_codes, "query")


def run_build_context_packet(topic: str, output_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Builds a structured 4-book context packet for downstream bridge note synthesis:
    Partitions into core_spine (Davidson), beyond_davidson (Harrison, Hurst, Kumar & Clark),
    exam_traps, and clinical guidelines.
    """
    packet = {
        "topic": topic,
        "source_hierarchy": {
            "core_spine": "Davidson 25th Edition",
            "beyond_davidson": ["Harrison 22nd Edition", "Fuster & Hurst The Heart 15th Edition", "Kumar and Clark 11th Edition 2026"],
            "evidence": "not retrieved by this tool (guideline recommendations are not queried)"
        },
        "core_spine_chunks": [],
        "beyond_davidson_chunks": [],
        "exam_traps": [],
        "guideline_recommendations": [],
        "not_populated": ["exam_traps", "guideline_recommendations"],   # always empty: nothing here retrieves them
    }
    def fail(msg: str):
        print(f"[CONTEXT-PACKET] ERROR: {msg}. No packet written.", file=sys.stderr)
        return None

    if not FEDERATED_SEARCH_SCRIPT.exists():
        return fail(f"federated search script not found at {FEDERATED_SEARCH_SCRIPT}")
    cmd = [sys.executable, str(FEDERATED_SEARCH_SCRIPT), "--query", topic, "--book", "all", "--top_k", "4", "--json"]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        return fail(f"federated search exited {proc.returncode}: {proc.stderr.strip()[-300:]}")
    try:
        results = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        return fail(f"federated search returned invalid JSON ({e})")

    raw_chunks: List[Dict[str, Any]] = []
    if isinstance(results, dict):
        for bname, bchunks in results.items():
            items = bchunks if isinstance(bchunks, list) else [bchunks]
            for chk in items:
                if isinstance(chk, dict):
                    chk.setdefault("book", bname)
                    raw_chunks.append(chk)
    elif isinstance(results, list):
        raw_chunks = [r for r in results if isinstance(r, dict)]

    packet["warnings"] = []
    for res in raw_chunks:
        if "error" in res:
            packet["warnings"].append(f"{res.get('book')}: retrieval error: {res['error']}")
            continue
        if "davidson" in str(res.get("book", "")).lower():
            packet["core_spine_chunks"].append(res)
        else:
            packet["beyond_davidson_chunks"].append(res)
    for w in packet["warnings"]:
        print(f"[CONTEXT-PACKET] WARNING: {w}", file=sys.stderr)
    packet["complete"] = not packet["warnings"]
    if not packet["core_spine_chunks"] and not packet["beyond_davidson_chunks"]:
        return fail(f"no chunks retrieved for topic '{topic}'")
    if not packet["core_spine_chunks"]:
        print("[CONTEXT-PACKET] WARNING: no Davidson core-spine chunks retrieved; Layer 2 cannot be grounded.", file=sys.stderr)

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(packet, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[CONTEXT-PACKET] Saved context packet to: {out_p}")
    else:
        print(json.dumps(packet, indent=2, ensure_ascii=False))

    return packet


def main():
    parser = argparse.ArgumentParser(
        description="Unified CDSS Navigator: Federated clinical retrieval across Davidson, Harrison, Hurst, and Kumar & Clark."
    )
    parser.add_argument("--query", help="Clinical query for federated cross-book retrieval")
    parser.add_argument("--book", choices=["all", "davidson", "harrison", "hurst", "kumar"], default="all", help="Target book")
    parser.add_argument("--top_k", type=int, default=3, help="Number of chunks per book")
    parser.add_argument("--vignette", help="Decompose and analyze a full clinical case vignette")
    parser.add_argument("--validate-therapy", nargs=2, metavar=("DRUG", "CONDITION"), help="Check drug indications and safety")
    parser.add_argument("--diff", help="Lookup differential diagnosis comparators")
    parser.add_argument("--outline", help="Lookup prompt-ready medical concept checklist")
    parser.add_argument("--compress", action="store_true", help="Extractive span compression")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--build-context-packet", metavar="TOPIC", help="Build grounded 4-book context packet for bridge note synthesis")
    parser.add_argument("--output", "-o", help="Output file path for context packet")
    parser.add_argument("--allow-partial", action="store_true",
                        help="Exit 0 even if some selected books could not be queried")

    args = parser.parse_args()
    global ACTIVE_BOOK, ALLOW_PARTIAL
    ACTIVE_BOOK, ALLOW_PARTIAL = args.book, args.allow_partial
    del SKIPPED[:]

    modes = [m for m, v in (("--build-context-packet", args.build_context_packet), ("--query", args.query),
                            ("--vignette", args.vignette), ("--validate-therapy", args.validate_therapy),
                            ("--diff", args.diff), ("--outline", args.outline)) if v]
    if len(modes) > 1:
        print(f"[ERROR] choose exactly one mode, got {modes}", file=sys.stderr)
        sys.exit(2)
    if args.output and not args.build_context_packet:
        print("[ERROR] --output is only used with --build-context-packet", file=sys.stderr)
        sys.exit(2)
    if args.json and modes and modes[0] != "--query":
        print(f"[ERROR] --json is only supported with --query (the {modes[0]} output is multi-section text/JSON "
              f"from separate books and would not be one parseable document)", file=sys.stderr)
        sys.exit(2)

    if args.build_context_packet:
        pkt = run_build_context_packet(args.build_context_packet, output_path=args.output)
        if not pkt:
            sys.exit(1)
        sys.exit(0 if (pkt.get("complete") or ALLOW_PARTIAL) else 3)
    elif args.query:
        code = run_federated_query(args.query, book=args.book, top_k=args.top_k, as_json=args.json, compress=args.compress)
        sys.exit(code)
    elif args.vignette:
        code = run_case_vignette(args.vignette, as_json=args.json)
        sys.exit(code)
    elif args.validate_therapy:
        code = run_therapy_validation(args.validate_therapy[0], args.validate_therapy[1])
        sys.exit(code)
    elif args.diff:
        code = run_diff(args.diff)
        sys.exit(code)
    elif args.outline:
        code = run_outline(args.outline)
        sys.exit(code)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
