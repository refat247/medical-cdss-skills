"""
CDSS Claim-Level Grounding Auditor (fail-closed).

A bridge note PASSES only if:
  1. The CDSS package directory exists and yields a non-empty chunk index.
  2. The note has a Layer 2 (Davidson Core Spine) section.
  3. Every claim line in the anchored sections cites a source:
       [Anchor: Book-Ch-ChunkID]   e.g. [Anchor: Davidson-16-L2-045]
       [chunk: ID]                 e.g. [chunk: L2-045]  (resolved in any book)
       Davidson Ch. 16 (Chunk L2-064) / [Anchor: Harrison Ch. 44, Fig. 44.4 / Chunk L2-024]  (free-text provenance)
       Box/Table/Figure N.N        (attributed to the nearest preceding book name; Davidson by default in Layer 2)
     Books organised by Parts/Sections (Harrison, Hurst) cannot map "Ch. N" to a file; such chunk citations
     resolve by id only and are reported as weak_citations.
  4. Every cited chunk / box / table / figure actually exists in the package.
  5. Layer 2 cites Davidson only (spec: zero non-Davidson content in Layer 2).
  6. No parametric red-flag formula appears in Layer 2.

Anchored sections: Layer 1, Layer 2, QB Awareness / Exam Trap, Layer 3, Layer 4, Layer 5 / Quick Revision.
Exempt sections: Coverage Declaration, Visual Assets, Layer 0, Clinical Evidence Notes (guidelines are outside the package).

Exit code 0 = PASS, 1 = FAIL.
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set

DEFAULT_PACKAGE_DIR = os.environ.get("CDSS_PACKAGE_DIR", r"D:\01_Medical_Study\CDSS_Retrieval_Package")

HALLUCINATION_RED_FLAGS = [
    r"Torricelli",
    r"v\s*=\s*\\?sqrt\{2",
    r"dimensionless\s+Reynolds",
    r"Poise\s+or\s+Pa",
    r"chaotic\s+turbulence.*2000",
]

BOOK_ALIASES = {
    "davidson": "davidson", "dav": "davidson",
    "harrison": "harrison", "har": "harrison",
    "hurst": "hurst", "fuster": "hurst",
    "kumar": "kumar", "kc": "kumar", "k&c": "kumar", "kumarclark": "kumar",
}

ANCHOR_RE = re.compile(r"\[Anchor:\s*([^\]]+?)\s*\]", re.IGNORECASE)
CHUNK_RE = re.compile(r"\[chunk:\s*([A-Za-z0-9_.\-]+)\s*\]", re.IGNORECASE)
REF_RE = re.compile(r"\b(Box|Table|Fig(?:ure)?)\.?\s+(\d{1,2}\.\d{1,3})\b", re.IGNORECASE)
CHUNK_ID_LINE_RE = re.compile(r"^\s*(?:full_)?chunk_id:\s*[\"']?([A-Za-z0-9_.\-]+)", re.MULTILINE)
CHAPTER_RE = re.compile(r"(?:Ch|Chapter|Part|Section)[ _-]?0*(\d{1,3})", re.IGNORECASE)
BOOK_ED_CH_RE = re.compile(r"^[A-Za-z]+_\d{1,2}_0*(\d{1,3})_")  # e.g. Davidson_25_18_Cardiovascular

EXEMPT_HEADINGS = ("COVERAGE DECLARATION", "VISUAL ASSET", "LAYER 0", "PHYSIOLOGY FOUNDATION",
                   "CLINICAL EVIDENCE", "EVIDENCE NOTES")
ANCHORED_HEADINGS = ("LAYER 1", "PRE-TRAINING", "LAYER 2", "DAVIDSON CORE", "QB AWARENESS", "EXAM TRAP",
                     "LAYER 3", "PHARMACOLOGY", "LAYER 4", "BEYOND DAVIDSON", "LAYER 5", "ACTIVE RECALL",
                     "QUICK REVISION")


def normalise_book(token: str) -> Optional[str]:
    t = re.sub(r"[^a-z&]", "", token.lower())
    if t in BOOK_ALIASES:
        return BOOK_ALIASES[t]
    for key, val in BOOK_ALIASES.items():
        if len(key) > 3 and key in t:
            return val
    return None


def book_from_path(p: Path, package_dir: Path) -> Optional[str]:
    try:
        rel = p.relative_to(package_dir)
    except ValueError:
        rel = p
    for part in rel.parts:
        b = normalise_book(part)
        if b:
            return b
    return None


class PackageIndex:
    """chunk ids per book (with chapter numbers), plus Box/Table/Figure numbers seen in each book's text."""

    def __init__(self, package_dir: Path):
        self.package_dir = package_dir
        self.chunks: Dict[str, Dict[str, Set[Optional[str]]]] = defaultdict(lambda: defaultdict(set))
        self.refs: Dict[str, Set[str]] = defaultdict(set)
        self.part_books: Set[str] = set()  # books whose files are organised by Part/Section, not chapter
        self.files_scanned = 0
        if package_dir.is_dir():
            self._build()

    def _build(self):
        for root, dirs, files in os.walk(self.package_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("__pycache__", "assets", "figures", "pages", "images")]
            for f in files:
                p = Path(root) / f
                book = book_from_path(p, self.package_dir)
                if book is None:
                    continue
                if f.endswith(("_RAG_Optimised.md", "_chunks.md")):
                    self._index_markdown(p, book)
                elif f.endswith((".db", ".sqlite", ".sqlite3")):
                    self._index_sqlite(p, book)

    def _index_markdown(self, p: Path, book: str):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return
        self.files_scanned += 1
        chapter = None
        for name in (p.name, p.parent.name, p.parent.parent.name):
            m = CHAPTER_RE.search(name) or BOOK_ED_CH_RE.search(name)
            if m and re.match(r"(?i)(part|section)", m.group(0)):
                self.part_books.add(book)
            if m:
                chapter = str(int(m.group(1)))
                break
        for cid in CHUNK_ID_LINE_RE.findall(text):
            self.chunks[book][cid].add(chapter)
        for kind, num in REF_RE.findall(text):
            self.refs[book].add(f"{kind[:3].lower()} {num}")

    def _index_sqlite(self, p: Path, book: str):
        try:
            con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        except sqlite3.Error:
            return
        try:
            self.files_scanned += 1
            tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            for t in tables:
                try:
                    cols = [r[1] for r in con.execute(f'PRAGMA table_info("{t}")')]
                except sqlite3.Error:
                    continue
                for c in cols:
                    if c.lower() in ("chunk_id", "full_chunk_id"):
                        for (v,) in con.execute(f'SELECT DISTINCT "{c}" FROM "{t}" WHERE "{c}" IS NOT NULL'):
                            self.chunks[book][str(v)].add(None)
        except sqlite3.Error:
            pass
        finally:
            con.close()

    @property
    def total_chunks(self) -> int:
        return sum(len(v) for v in self.chunks.values())

    def book_chapters(self, book: str) -> Set[str]:
        return {c for chs in self.chunks.get(book, {}).values() for c in chs if c}

    def resolve_anchor(self, book: Optional[str], chapter: Optional[str], chunk_id: str):
        """Returns (reason_or_None, weak_note_or_None). reason None = resolved."""
        books = [book] if book else list(self.chunks.keys())
        if book and book not in self.chunks:
            return f"book '{book}' has no indexed chunks in package", None
        for b in books:
            chapters = self.chunks[b].get(chunk_id)
            if not chapters:
                continue
            if chapters == {None}:
                return None, None
            if chapter is None:
                # A bare [chunk: L2-001] cannot be placed: local ids repeat in every chapter, so it must not
                # resolve just because SOME chapter of SOME book has that id.
                if len(chapters) > 1:
                    return (f"ambiguous: chunk '{chunk_id}' exists in {len(chapters)} chapters of {b}; "
                            f"cite it as [Anchor: {b.capitalize()}-<chapter>-{chunk_id}]"), None
                return None, None
            if chapter in chapters:
                return None, None
            if b in self.part_books and chapter not in self.book_chapters(b):
                # book is organised by Parts/Sections, so "Ch. 44" cannot be mapped to a file
                return None, f"{b} Ch. {chapter} / {chunk_id}: chapter not mappable to package files (chunk id exists in {len(chapters)} parts)"
            return f"chunk '{chunk_id}' exists in {b} chapter(s) {sorted(c for c in chapters if c)} but not in chapter {chapter}", None
        return f"chunk '{chunk_id}' not found" + (f" in {book}" if book else " in any book"), None


def parse_anchor(body: str):
    parts = body.split("-", 2)
    book = normalise_book(parts[0]) if parts else None
    if book and len(parts) == 3 and parts[1].strip().isdigit():
        return book, str(int(parts[1])), parts[2].strip()
    if book and len(parts) >= 2:
        return book, None, body.split("-", 1)[1].strip()
    return None, None, body.strip()


BOOK_RE = re.compile(r"\b(Davidson|Harrison|Hurst|Fuster|Kumar(?:\s*(?:&|and)\s*Clark)?|K&C)\b", re.IGNORECASE)
HYPHEN_ANCHOR_RE = re.compile(r"\[Anchor:\s*([A-Za-z&]+-\d+-[A-Za-z0-9_.\-]+)\s*\]", re.IGNORECASE)
SEG_CH_RE = re.compile(r"\bCh(?:apter)?\.?\s*(\d{1,3})\b", re.IGNORECASE)
SEG_CHUNK_RE = re.compile(r"\bChunks?\s*:?\s*([A-Za-z0-9_.\-]*\d[A-Za-z0-9_.\-]*)", re.IGNORECASE)


def extract_citations(line: str, default_book: Optional[str]) -> List[tuple]:
    """Returns citations as (kind, book, chapter, value, raw). kind is 'chunk' or 'ref'.

    Accepts [Anchor: Davidson-16-L2-045], [chunk: L2-045], free-text provenance such as
    "Davidson Ch. 16 (Chunk L2-064)" or "[Anchor: Harrison Ch. 44, Fig. 44.4 / Chunk L2-024]",
    and Box/Table/Figure numbers (attributed to the nearest preceding book name).
    """
    cites = []
    for body in HYPHEN_ANCHOR_RE.findall(line):
        book, chapter, cid = parse_anchor(body)
        cites.append(("chunk", book, chapter, cid, f"[Anchor: {body}]"))
    text = HYPHEN_ANCHOR_RE.sub(" ", line)
    for cid in CHUNK_RE.findall(text):
        cites.append(("chunk", default_book, None, cid, f"[chunk: {cid}]"))
    text = CHUNK_RE.sub(" ", text)
    marks = list(BOOK_RE.finditer(text))
    bounds = [(0, marks[0].start() if marks else len(text), default_book)]
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        bounds.append((m.start(), end, normalise_book(m.group(1))))
    for start, end, book in bounds:
        seg = text[start:end]
        ch = SEG_CH_RE.search(seg)
        chapter = str(int(ch.group(1))) if ch else None
        for cid in SEG_CHUNK_RE.findall(seg):
            cites.append(("chunk", book, chapter, cid.rstrip(".-"), seg.strip()[:60]))
        for kind, num in REF_RE.findall(seg):
            cites.append(("ref", book, None, f"{kind[:3].lower()} {num}", f"{kind} {num}"))
    return cites


def split_sections(text: str) -> List[Dict]:
    sections, current = [], {"heading": "", "level": 0, "lines": []}
    for i, line in enumerate(text.splitlines(), start=1):
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            sections.append(current)
            current = {"heading": m.group(2).strip(), "level": len(m.group(1)), "lines": [], "lineno": i}
        else:
            current["lines"].append((i, line))
    sections.append(current)
    return sections


_LAYER_RE = {n: re.compile(rf"\bLAYER\s*{n}\b") for n in "012345"}


def section_kind(heading: str) -> str:
    """Classify a heading. A heading that names an anchored layer is ALWAYS anchored, even if it also contains an
    exempt phrase ("Layer 3 - Pharmacology: Clinical Evidence" used to be exempt because the exempt test ran first),
    and "Layer 10" is no longer mistaken for "Layer 1" (substring match)."""
    h = heading.upper()
    if _LAYER_RE["2"].search(h) or "DAVIDSON CORE" in h:
        return "layer2"
    if any(_LAYER_RE[n].search(h) for n in "1345") or any(
            k in h for k in ("PRE-TRAINING", "QB AWARENESS", "EXAM TRAP", "PHARMACOLOGY", "BEYOND DAVIDSON",
                             "ACTIVE RECALL", "QUICK REVISION")):
        return "anchored"
    if _LAYER_RE["0"].search(h) or any(k in h for k in EXEMPT_HEADINGS):
        return "exempt"
    return "inherit"


def is_claim_line(line: str) -> bool:
    s = line.strip()
    if not s or s.startswith(("<!--", "```", "|---", "| ---", ":--")) or re.fullmatch(r"[|\-:\s]+", s):
        return False
    if re.match(r"^([-*+]|\d+[.)])\s+\S", s):
        return True
    if s.startswith("|"):
        cells = [c.strip() for c in s.strip("|").split("|")]
        # Any row with content is a claim (single-token cells such as `| Warfarin | 10mg |` used to be skipped).
        # Header rows are excluded later (header_rows) and all-caps label rows here.
        return any(re.search(r"\w", c) for c in cells) and not all(c.isupper() for c in cells if c)
    return len(re.sub(r"[>*_`]", "", s).split()) >= 6


def verify_note_grounding(note_path: Path, package_dir: Path, index: Optional[PackageIndex] = None) -> Dict:
    text = note_path.read_text(encoding="utf-8")
    report = {
        "note": note_path.name, "status": "PASS", "failures": [], "warnings": [],
        "claim_lines_checked": 0, "uncited_lines": [], "unresolved_citations": [],
        "red_flag_violations": [], "citations_resolved": 0, "package_chunks_indexed": 0,
    }

    def fail(msg):
        report["failures"].append(msg)

    if not package_dir.is_dir():
        fail(f"package directory not found: {package_dir}")
        report["status"] = "FAIL"
        return report
    index = index or PackageIndex(package_dir)
    report["package_chunks_indexed"] = index.total_chunks
    if index.total_chunks == 0:
        fail(f"no chunk ids could be indexed from package: {package_dir}")

    sections = split_sections(text)
    kinds: List[str] = []
    stack: List = []  # (level, kind, explicit) of enclosing headings
    for s in sections:
        if not s["heading"]:
            kinds.append("exempt")
            continue
        while stack and stack[-1][0] >= s["level"]:
            stack.pop()
        k = section_kind(s["heading"])
        explicit = k != "inherit"
        if k == "inherit":
            k = stack[-1][1] if stack else "exempt"
            inherited_explicit = bool(stack) and stack[-1][2]
            if k == "exempt" and not inherited_explicit and s["level"] >= 2 and any(is_claim_line(l) for _, l in s["lines"]):
                # Fail closed: a section the gate cannot classify but that contains claims is NOT silently skipped.
                report.setdefault("unclassified_sections", []).append(f"line {s.get('lineno')}: '{s['heading']}'")
                fail(f"unclassified section '{s['heading']}' (line {s.get('lineno')}) contains claim lines: name it as a "
                     f"Layer 1-5 / QB section, or as an exempt section (Coverage Declaration, Visual Assets, Layer 0, Clinical Evidence Notes)")
        stack.append((s["level"], k, explicit or (stack[-1][2] if stack else False)))
        kinds.append(k)

    if not any(k == "layer2" for k in kinds):
        fail("note has no Layer 2 / Davidson Core section")

    report["weak_citations"] = []
    for s, kind in zip(sections, kinds):
        if kind == "exempt":
            continue
        lines = s["lines"]
        header_rows = {lines[i][0] for i in range(len(lines) - 1)
                       if lines[i][1].strip().startswith("|") and re.fullmatch(r"\s*\|?[\s:|\-]+\|?\s*", lines[i + 1][1] or "x")}
        for lineno, line in lines:
            if kind == "layer2":
                for pat in HALLUCINATION_RED_FLAGS:
                    m = re.search(pat, line, re.IGNORECASE)
                    if m:
                        report["red_flag_violations"].append(f"line {lineno}: parametric formula '{m.group(0)}' in Layer 2")
            if lineno in header_rows or not is_claim_line(line):
                continue
            report["claim_lines_checked"] += 1
            default_book = "davidson" if kind == "layer2" else None
            cites = extract_citations(line, default_book)
            if not cites:
                report["uncited_lines"].append(f"line {lineno}: {line.strip()[:120]}")
                continue
            for ckind, book, chapter, value, raw in cites:
                if kind == "layer2" and book not in (None, "davidson"):
                    report["unresolved_citations"].append(f"line {lineno}: non-Davidson citation in Layer 2: {raw}")
                    continue
                if ckind == "chunk":
                    reason, weak = index.resolve_anchor(book, chapter, value)
                else:
                    pool = [book] if book else list(index.refs.keys())
                    found = any(value in index.refs.get(b, set()) for b in pool)
                    reason, weak = (None, None) if found else (f"{raw} not found in {book or 'any book'} package text", None)
                if reason:
                    report["unresolved_citations"].append(f"line {lineno}: {raw} -> {reason}")
                else:
                    report["citations_resolved"] += 1
                    if weak:
                        report["weak_citations"].append(f"line {lineno}: {weak}")

    if report["claim_lines_checked"] == 0:
        fail("no claim lines found in anchored sections")
    if report["uncited_lines"]:
        fail(f"{len(report['uncited_lines'])} claim line(s) have no citation")
    if report["unresolved_citations"]:
        fail(f"{len(report['unresolved_citations'])} citation(s) do not resolve to the package")
    if report["red_flag_violations"]:
        fail(f"{len(report['red_flag_violations'])} parametric red flag(s) in Layer 2")
    report["status"] = "FAIL" if report["failures"] else "PASS"
    return report


def main():
    parser = argparse.ArgumentParser(description="Fail-closed claim-level grounding audit for bridge notes")
    parser.add_argument("--note", "-n", required=True, help="Path to Markdown note file")
    parser.add_argument("--package-dir", "-p", default=DEFAULT_PACKAGE_DIR, help="Path to CDSS package (env CDSS_PACKAGE_DIR)")
    parser.add_argument("--report", "-r", help="Optional path to write the JSON report")
    args = parser.parse_args()

    res = verify_note_grounding(Path(args.note), Path(args.package_dir))
    print(f"[GROUNDING-AUDIT] {res['note']}: {res['status']}")
    print(f"[GROUNDING-AUDIT] Package chunks indexed: {res['package_chunks_indexed']} | claim lines: "
          f"{res['claim_lines_checked']} | citations resolved: {res['citations_resolved']} "
          f"(weak, chapter not mappable: {len(res.get('weak_citations', []))})")
    for f in res["failures"]:
        print(f"  FAIL: {f}")
    for w in res.get("warnings", [])[:15]:
        print(f"  WARN: {w}")
    for key in ("uncited_lines", "unresolved_citations", "red_flag_violations", "weak_citations"):
        for item in res[key][:15]:
            print(f"    - {item}")
        if len(res[key]) > 15:
            print(f"    ... {len(res[key]) - 15} more")
    if args.report:
        Path(args.report).write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    sys.exit(0 if res["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
