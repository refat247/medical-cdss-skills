"""
Publisher for an EXISTING Davidson Bridge Note V2.2 markdown file.

It does not write note content. The note must already exist in --output-dir
(written by you or an agent from a context packet built with
medical-cdss-unified-orchestrator --build-context-packet).

Steps:
  1. Figure super-resolution enhancement (if a figures/ folder exists)
  2. Fail-closed grounding gate (every claim line must cite a chunk that exists in the package)
  3. Anti-mojibake / LaTeX / ISMP cleanroom -> written to <output-dir>/cleanroom/ (source note untouched)
  4. Executive Word (.docx) publication with native card grids
"""

__version__ = "1.2.1"

import os
import sys
import re
import argparse
import subprocess
from pathlib import Path
from typing import Optional

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
SKILLS_ROOT = Path(os.environ.get("CDSS_SKILLS_ROOT", str(SKILL_DIR.parent)))
GUARD_SCRIPT = SKILLS_ROOT / "cdss-unicode-mojibake-guard" / "scripts" / "guard.py"
DEFAULT_PACKAGE_DIR = os.environ.get("CDSS_PACKAGE_DIR", r"D:\01_Medical_Study\CDSS_Retrieval_Package")

def run_pipeline(topic: str, output_dir: Path, package_dir: Path, note_id: Optional[str] = None) -> bool:
    """Runs all publishing steps; returns False (never raises) if any step fails."""
    try:
        return _run_pipeline(topic, output_dir, package_dir, note_id)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Publishing step failed (exit {e.returncode}): {' '.join(map(str, e.cmd[:2]))}", file=sys.stderr)
        return False


def _run_pipeline(topic: str, output_dir: Path, package_dir: Path, note_id: Optional[str] = None) -> bool:
    output_dir.mkdir(parents=True, exist_ok=True)
    header_id = f" [{note_id}]" if note_id else ""
    print(f"\n=======================================================")
    print(f" CDSS BRIDGE NOTE PUBLISHER: {topic.upper()}{header_id}")
    print(f" Target Directory: {output_dir}")
    print(f"=======================================================\n")

    # Step 1: Check existing figures and run enhance_figures
    figures_src = output_dir / "figures"
    figures_enh = output_dir / "figures_enhanced"
    if figures_src.exists():
        print("[STAGE 1/4] Running Lanczos-4 Figure Super-Sampling...")
        enhance_script = SCRIPTS_DIR / "enhance_figures.py"
        subprocess.run([sys.executable, str(enhance_script), "-f", str(figures_src), "-o", str(figures_enh)], check=True)
    else:
        print("[STAGE 1/4] No local 'figures' directory found to enhance. Skipping.")

    # Step 2: Check for candidate markdown note matching note_id or topic
    md_candidates = list(output_dir.glob("*.md"))
    if not md_candidates:
        print(f"[ERROR] No markdown note found in {output_dir} to audit/publish!", file=sys.stderr)
        return False

    note_md = None
    # 1. Try matching by note_id if provided (e.g., Note_16.1 or 16_1)
    if note_id:
        sanitized_id = note_id.replace(".", "_")
        pattern = re.compile(rf"(?:^|[^\d])(?:{re.escape(note_id)}|{re.escape(sanitized_id)})(?:[^\d]|$)")
        id_matches = [c for c in md_candidates if pattern.search(c.name)]
        if len(id_matches) == 1:
            note_md = id_matches[0]
        elif len(id_matches) > 1:
            print(f"[ERROR] Multiple markdown notes matched note_id='{note_id}': {[c.name for c in id_matches]}", file=sys.stderr)
            return False

    # 2. Try matching by topic if note_id was not provided or didn't resolve
    if not note_md and topic:
        clean_words = [w.lower() for w in re.split(r"[\s\-_]+", topic) if len(w) > 2]
        if clean_words:
            # First look for candidates containing ALL clean words
            exact_matches = [c for c in md_candidates if all(w in c.name.lower() for w in clean_words)]
            if len(exact_matches) == 1:
                note_md = exact_matches[0]
            elif len(exact_matches) > 1:
                print(f"[ERROR] Multiple markdown notes matched topic='{topic}': {[c.name for c in exact_matches]}", file=sys.stderr)
                return False

    # 3. Fail closed if neither note_id nor topic matched
    if not note_md:
        cand_names = [c.name for c in md_candidates]
        print(f"[ERROR] Could not resolve a matching markdown note for note_id='{note_id}' or topic='{topic}'. Available candidates: {cand_names}", file=sys.stderr)
        return False

    print(f"[STAGE 2/4] Verifying Claim Grounding on: {note_md.name}...")
    verify_script = SCRIPTS_DIR / "verify_grounding.py"
    res = subprocess.run([sys.executable, str(verify_script), "-n", str(note_md), "-p", str(package_dir)])
    if res.returncode != 0:
        print(f"[ERROR] Grounding check failed for {note_md.name} (exit code {res.returncode})! Zero-hallucination attribution gate breached.", file=sys.stderr)
        return False

    # Step 3: Anti-Mojibake & LaTeX Cleanroom Guard
    print(f"[STAGE 3/4] Running Cleanroom Anti-Mojibake & LaTeX Gate...")
    if not GUARD_SCRIPT.exists():
        print(f"[ERROR] Cleanroom guard not found at {GUARD_SCRIPT}; refusing to publish uncleaned text.", file=sys.stderr)
        return False
    clean_dir = output_dir / "cleanroom"
    clean_dir.mkdir(exist_ok=True)
    clean_md = clean_dir / note_md.name
    subprocess.run([sys.executable, str(GUARD_SCRIPT), "cleanroom-docx", "-f", str(note_md), "-o", str(clean_md)], check=True)

    # Step 4: Executive Word Document Publication
    print(f"[STAGE 4/4] Compiling Executive Word (.docx) with Native Card Grids...")
    publish_script = SCRIPTS_DIR / "publish_executive_docx.py"
    target_docx = output_dir / f"{note_md.stem}_Executive.docx"
    subprocess.run([sys.executable, str(publish_script), "-i", str(clean_md), "-o", str(target_docx),
                    "--base-dir", str(output_dir)], check=True)

    print(f"\n[PIPELINE-COMPLETE] Publication successful!")
    print(f"  - Source Markdown (unchanged): {note_md}")
    print(f"  - Clean Markdown: {clean_md}")
    print(f"  - Executive Word: {target_docx}\n")
    return True

def main():
    parser = argparse.ArgumentParser(description="Orchestrate Davidson Bridge Note V2.2 Synthesis")
    parser.add_argument("--topic", "-t", required=True, help="Clinical topic (e.g. 'Cardiac Murmurs')")
    parser.add_argument("--output-dir", "-o", required=True, help="Output destination folder")
    parser.add_argument("--package-dir", "-p", default=DEFAULT_PACKAGE_DIR, help="CDSS library path (env CDSS_PACKAGE_DIR)")
    parser.add_argument("--note-id", help="Optional note identifier (e.g. '16.1')")

    args = parser.parse_args()
    try:
        success = run_pipeline(args.topic, Path(args.output_dir), Path(args.package_dir), note_id=args.note_id)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Publishing step failed (exit {e.returncode}): {' '.join(map(str, e.cmd[:2]))}", file=sys.stderr)
        success = False
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()

