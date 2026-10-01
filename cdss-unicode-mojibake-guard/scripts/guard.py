"""
CDSS Unicode, Anti-Mojibake, ISMP Clinical Safety & LaTeX De-Delimiter Engine
Autonomous pre-flight auditor, in-place sanitizer, and runtime encoding guard.
"""

__version__ = "1.6.1"

import os
import re
import sys
import json
import argparse
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Enable UTF-8 console output on Windows
def enforce_utf8_environment():
    """Forces Windows stdout/stderr to strict UTF-8 with replacement."""
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    if hasattr(sys.stderr, 'reconfigure'):
        try:
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass

enforce_utf8_environment()

# Common double-encoded Windows-1252 / UTF-8 artifact table
MOJIBAKE_MAP: Dict[str, str] = {
    "â‰¥": ">=",
    "â‰¤": "<=",
    "Â±": "+/-",
    "Âµg": "mcg",
    "Âµ": "µ",
    "â€™": "'",
    "â€˜": "'",
    "â€œ": '"',
    "â€\x9d": '"',
    "â€”": " - ",
    "â€“": " - ",
    "Â°C": " deg C",
    "â†’": "->",
    "Ã—": "x",
    "Ã©": "e",
    "Ã¨": "e",
    # added in the second sweep (previously neither repaired nor flagged; a sign flip like "âˆ’5" passed the gate)
    "âˆ’": "-", "â‰ˆ": "~", "Î±": "alpha", "Î²": "beta", "Î³": "gamma", "Î”": "Delta", "Î¼": "mc",
    "Â½": "1/2", "Â²": "2", "Â³": "3", "Â·": ".", "â€¢": "-", "â€¦": "...",
    "Ã¶": "o", "Ã¼": "u", "Ã¤": "a", "Ã±": "n", "Ã§": "c",
}

# Regex for detecting encoding corruptions, invisible artifacts, and raw LaTeX OCR tags
# BLOCKING: genuine corruption only. Source text is kept verbatim, so printed symbols (µg, ≥) and the
# pipeline's LaTeX are NOT corruption; they are normalised only in generated output (sanitize_for_llm).
CORRUPTION_PATTERNS = [
    r"â‰[¥¤ˆ]", r"Â[±µ°½²³·]", r"â[€™€˜]", r"â€[“”—–¢¦]", r"Ã[—©¶¼¤±§]", r"âˆ’", r"Î[±²³”¼]", r"\ufffd", r"\u200b", r"\ufeff", r"\u00ad",
    # Legacy corruption written by guard/preready versions <= 1.3.0 / 1.7.0 (NFKC and \mu bugs), or OCR.
    # Files containing these must be regenerated from source, not patched.
    r"mcg\s*(?:mol|g)\b", r"\b10(?:9|12)/L\b", "\u2044",
]
CORRUPTION_REGEX = re.compile("|".join(CORRUPTION_PATTERNS))

# Non-blocking notes: raw microgram symbols and LaTeX comparison markup are legitimate in verbatim source;
# they are converted in output (µg -> mcg, \geq -> >=) by sanitize_for_llm / cleanroom_docx_filter.
OUTPUT_NORMALISATION_PATTERNS = [
    r"\b[µμ]g\b", r"(?<=[0-9\s])ug\b", r"\\(?:geq|leq)\b", r"\\text\{--",
]

# ISMP dose-writing advisories. Reported by audit, but NEVER rewritten in source text:
# textbook/source markdown stays verbatim (lab values such as "Hb 13.0 g/dL" are not doses).
# Rewrites are applied only to generated output (cleanroom_docx_filter / sanitize_for_llm(rewrite_doses=True)).
DOSE_UNITS = r"(?:mg|mcg|g|mL|units)"
NOT_LAB_DENOM = r"(?!\s*/\s*(?:d?L|mL|mmol|\d+\s*h)\b)"
ISMP_ADVISORY_PATTERNS = [
    r"\b\d+\.0+\s*" + DOSE_UNITS + r"\b" + NOT_LAB_DENOM,
    r"(?:^|[\s(])\.\d+\s*(?:mg|mcg|g|mL|units|mmol)\b",
    r"(?<![\w.])(?:Q\.D\.|QD|Q\.O\.D\.|QOD)(?!\w)",
    r"\b\d+\s*(?:IU\b|I\.U\.(?!\w))",
    r"\b\d+\s*U\b(?!\s*\/\s*[a-zA-Z])(?![.\-][A-Za-z])",
]
ISMP_ADVISORY_REGEX = re.compile("|".join(ISMP_ADVISORY_PATTERNS + OUTPUT_NORMALISATION_PATTERNS))

# Source repair restores the ORIGINAL character (not the ISMP output form), e.g. "Âµg" -> "µg".
SOURCE_MOJIBAKE_MAP: Dict[str, str] = {
    "â‰¥": "≥", "â‰¤": "≤", "Â±": "±", "Âµ": "µ", "Â°": "°",
    "â€™": "\u2019", "â€˜": "\u2018", "â€œ": "\u201c", "â€\x9d": "\u201d",
    "â€”": "\u2014", "â€“": "\u2013", "â†’": "→", "Ã—": "×", "Ã©": "é", "Ã¨": "è",
    "âˆ’": "\u2212", "â‰ˆ": "≈", "Î±": "α", "Î²": "β", "Î³": "γ", "Î”": "Δ", "Î¼": "μ",
    "Â½": "½", "Â²": "²", "Â³": "³", "Â·": "·", "â€¢": "•", "â€¦": "…",
    "Ã¶": "ö", "Ã¼": "ü", "Ã¤": "ä", "Ã±": "ñ", "Ã§": "ç",
}


def repair_source_text(text: str) -> str:
    """Source-safe repair: fixes encoding damage only and keeps the printed text verbatim.

    Restores double-encoded characters to their originals, applies NFC, expands typographic ligatures and
    strips invisible characters (BOM, zero-width space, soft hyphen, direction marks). It does NOT convert
    µg, ≥, ± or LaTeX, and does NOT apply ISMP rewrites; those belong to generated output only.
    """
    if not text:
        return ""
    for bad, good in SOURCE_MOJIBAKE_MAP.items():
        text = text.replace(bad, good)
    text = unicodedata.normalize("NFC", text)
    for lig, rep in LIGATURE_MAP.items():
        text = text.replace(lig, rep)
    for ch in ("\u200b", "\ufeff", "\u00ad", "\u200e", "\u200f"):
        text = text.replace(ch, "")
    return text

# Explicit typographic ligature mapping for NFC-safe normalisation
LIGATURE_MAP: Dict[str, str] = {
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb03": "ffi",
    "\ufb04": "ffl",
    "\ufb05": "ft",
    "\ufb06": "st",
}

def repair_mojibake(text: str) -> str:
    """Repairs known double-encoded Windows-1252 / UTF-8 corruption."""
    if not text:
        return ""
    for bad, good in MOJIBAKE_MAP.items():
        if bad in text:
            text = text.replace(bad, good)
    return text

def clean_clinical_latex(text: str) -> str:
    """
    Removes OCR and LLM-generated LaTeX math delimiters and converts them
    to standard clinical ASCII/Unicode representations.
    """
    if not text:
        return ""

    # 0. Powers of ten in math mode: 10$^{9}$ -> 10⁹ (must run before citation rule)
    _sup0 = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
    text = re.sub(r"(?<![\d.])(10)\s*\$\^\{?\s*(-?\d{1,3})\s*\}?\$",
                  lambda m: m.group(1) + m.group(2).translate(_sup0), text)
    text = re.sub(r"\$\^\{\\circ\}\$|\\\(\s*\^\{\\circ\}\s*\\\)|\^\{\\circ\}", "°", text)
    text = re.sub(r"\$\^\\circ\$", "°", text)
    # 1. Superscript references: \( ^{18} \) or $^{18}$ -> [18]
    text = re.sub(r"\\\(\s*\^\{([0-9,\-\s]+)\}\s*\\\)", r"[\1]", text)
    text = re.sub(r"\$\^\{([0-9,\-\s]+)\}\$", r"[\1]", text)
    text = re.sub(r"\$\^([0-9]+)\$", r"[\1]", text)
    # Other superscripts are ion charges / isotopes, NOT citation numbers: Ca$^{2+}$ -> Ca2+, $^{99m}$Tc -> 99mTc
    text = re.sub(r"\$\^\{([^}]+)\}\$", r"\1", text)

    # 1b. Powers of ten / numeric exponents: 10^{9} or 10^9 -> 10⁹ (never collapse to "109")
    _sup = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
    text = re.sub(r"(\d)\s*\^\s*\{\s*(-?\d{1,3})\s*\}", lambda m: m.group(1) + m.group(2).translate(_sup), text)
    text = re.sub(r"(\d)\^(-?\d{1,3})(?!\d)", lambda m: m.group(1) + m.group(2).translate(_sup), text)

    # 2. TeX hyphens / dashes: \text{--} or \text{---}
    text = re.sub(r"\\text\{---\}", " - ", text)
    text = re.sub(r"\\text\{--\}", "-", text)

    # 3. Clinical heart sounds & valve components: $S_1$, $S_2$, $S_3$, $S_4$, $A_2$, $P_2$, $V_1$-$V_6$
    text = re.sub(r"\\?[\(\$]\s*S_([1-4])\s*\\?[\)\$]", r"S\1", text)
    text = re.sub(r"\\?[\(\$]\s*A_2\s*\\?[\)\$]", "A2", text)
    text = re.sub(r"\\?[\(\$]\s*P_2\s*\\?[\)\$]", "P2", text)
    text = re.sub(r"\\?[\(\$]\s*V_([1-6])\s*\\?[\)\$]", r"V\1", text)

    # 4. A2-OS / OS / intervals
    text = re.sub(r"\\?[\(\$]\s*A_2\s*(?:-|\\text\{--\}|\s*-\s*)\s*OS\s*\\?[\)\$]", "A2-OS", text)

    # 5. Greek letters, physics symbols, and math symbols
    # Note: Approximation tildes (~5%) are strictly preserved and not stripped.
    text = re.sub(r"\\mathrm\{([^}]+)\}", r"\1", text)
    text = re.sub(r"\\text\{([^}]+)\}", r"\1", text)
    text = re.sub(r"\\(?:ge|geq)(?=[^a-zA-Z]|$)", ">=", text)
    text = re.sub(r"\\(?:le|leq)(?=[^a-zA-Z]|$)", "<=", text)
    text = re.sub(r"\\pm(?=[^a-zA-Z]|$)", "+/-", text)
    text = re.sub(r"\\times(?=[^a-zA-Z]|$)", "x", text)
    text = re.sub(r"\\cdot(?=[^a-zA-Z]|$)", " * ", text)
    text = re.sub(r"\\approx(?=[^a-zA-Z]|$)", "~", text)
    text = re.sub(r"\\Delta\s*P\b", "Delta P", text)
    text = re.sub(r"\\Delta(?=[^a-zA-Z]|$)", "Delta", text)
    text = re.sub(r"\\rho(?=[^a-zA-Z]|$)", "rho", text)
    text = re.sub(r"\\circ(?=[^a-zA-Z]|$)", "°", text)
    text = re.sub(r"\\beta(?=[^a-zA-Z]|$)", "beta", text)
    text = re.sub(r"\\alpha(?=[^a-zA-Z]|$)", "alpha", text)
    text = re.sub(r"\\rightarrow(?=[^a-zA-Z]|$)", "->", text)

    # Convert LaTeX microgram: \mu g, \mu\text{g}, \mu\mathrm{g}, \(\mu\)g, $\mu$g -> mcg
    # Only map to mcg when \mu is explicitly coupled with g (mass unit)
    text = re.sub(r"\\?[\(\$]\s*\\mu\s*(?:\\(?:text|mathrm)\{g\}|g)\s*\\?[\)\$]", "mcg", text)
    text = re.sub(r"\\?[\(\$]\s*\\mu\s*\\?[\)\$]\s*(?:\\(?:text|mathrm)\{g\}|g)\b", "mcg", text)
    text = re.sub(r"\\mu\s*(?:\\(?:text|mathrm)\{g\}|g)\b", "mcg", text)
    # Lone \mu represents the Greek prefix micro (µ, e.g. \( \mu \)mol/L -> µmol/L)
    text = re.sub(r"\\?[\(\$]\s*\\mu\s*\\?[\)\$]", "µ", text)
    text = re.sub(r"\\mu(?=[^a-zA-Z]|$)", "µ", text)

    text = re.sub(r"\\?[\(\$]\s*\\beta\s*([0-9]*)\s*\\?[\)\$]", r"beta\1", text)
    text = re.sub(r"\\?[\(\$]\s*\\alpha\s*([0-9]*)\s*\\?[\)\$]", r"alpha\1", text)
    text = re.sub(r"\\%", "%", text)
    text = re.sub(r"\b([A-Za-z]{1,4})_\{([0-9A-Za-z]+)\}", r"\1\2", text)
    text = re.sub(r"V_\{?max\}?", "Vmax", text)
    text = re.sub(r"\\?[\(\$]\s*dp/dt\s*\\?[\)\$]", "dp/dt", text)

    # 6. De-delimit \( ... \) or $ ... $ wrapping comparisons, numbers, or units
    def strip_delimiters(m):
        raw_inner = m.group(1)
        nxt = m.string[m.end():m.end() + 1]
        # "$5 for A vs $10": the closing "$" is really the opening of the next currency amount
        # (preceded by whitespace and followed by a digit) -> not a math span.
        if raw_inner != raw_inner.rstrip() and nxt.isdigit():
            return m.group(0)
        inner = raw_inner.strip()
        # If inner text contains prose conjunctions or currency phrases (e.g. "$5 to $10"),
        # these are standalone currency amounts or prose, NOT LaTeX math delimiters!
        if re.search(r"\b(?:to|and|or|per|with|between|from)\b", inner, re.IGNORECASE):
            return m.group(0)
        # If inner contains complex TeX commands, keep delimiters
        if not re.search(r"\\(frac|sqrt|sum|int|partial|mathbf|begin|end)", inner):
            return inner
        return m.group(0)

    text = re.sub(r"\\\((.*?)\\\)", strip_delimiters, text)
    text = re.sub(r"\$([^$\n]+?)\$", strip_delimiters, text)

    # 7. Clean up leftover basic subscripts: only numeric subscripts (e.g. S_1 -> S1)
    # or explicit braces (V_{max} -> Vmax) to avoid corrupting snake_case words like drug_dosing
    text = re.sub(r"\b([A-Za-z]{1,4})_\{([0-9A-Za-z]+)\}\b", r"\1\2", text)
    # (not file names: page_042.png / fig_3.png keep their underscore)
    text = re.sub(r"\b([A-Za-z]{1,4})_([0-9]+)\b(?!\.[A-Za-z0-9]{2,4}\b)", r"\1\2", text)

    # 8. Proper spacing around comparisons
    text = re.sub(r"(>=|<=|>|<)([0-9])", r"\1 \2", text)

    return text

def apply_ismp_dose_rewrites(text: str) -> str:
    """ISMP dose-expression rewrites for GENERATED OUTPUT only (never source text).

    Trailing-zero removal is limited to dose units and skips lab concentrations
    (e.g. "Hb 13.0 g/dL", "K 4.0 mmol/L" are left untouched).
    """
    text = re.sub(r"\b(\d+)\.0+\s*(mg|mcg|g|mL|units)\b" + NOT_LAB_DENOM, r"\1 \2", text)
    text = re.sub(r"(^|[\s(])\.(\d+)\s*(mg|mcg|g|mL|units|mmol)\b", r"\g<1>0.\2 \3", text)
    text = re.sub(r"(?<![\w.])(?:Q\.D\.|QD)(?!\w)", "once daily", text)
    text = re.sub(r"(?<![\w.])(?:Q\.O\.D\.|QOD)(?!\w)", "every other day", text)
    text = re.sub(r"(\d+)\s*(?:IU\b|I\.U\.(?!\w))", r"\1 units", text)
    # "U" is a dose unit only; "5 U.S. adults", "2 U-wave" are not doses
    text = re.sub(r"(\d+)\s*U\b(?!\s*\/\s*[a-zA-Z])(?![.\-][A-Za-z])", r"\1 units", text)
    return text

def sanitize_for_llm(text: str, enforce_ismp: bool = True, clean_latex: bool = True,
                     rewrite_doses: bool = True) -> str:
    """
    Sanitizes retrieved clinical text into token-safe, zero-mojibake format
    guaranteed compatible with all LLM tokenizers (Gemini, Claude, GPT, LLaMA).
    Uses NFC canonical normalization to prevent corruption of superscripts and fractions.
    """
    if not text:
        return ""

    # 1. Repair double-encoded CP1252 artifacts
    text = repair_mojibake(text)

    # 2. Unicode NFC normalization (avoids destroying superscripts like 10⁹ -> 109 or fractions ½)
    text = unicodedata.normalize("NFC", text)

    # 3. Replace common typographic ligatures safely
    for lig, rep in LIGATURE_MAP.items():
        if lig in text:
            text = text.replace(lig, rep)

    # 4. Strip invisible and token-breaking characters
    text = text.replace("\u200b", "")  # Zero-width space
    text = text.replace("\ufeff", "")  # BOM
    text = text.replace("\u00ad", "")  # Soft hyphen
    text = text.replace("\u200e", "")  # LTR mark
    text = text.replace("\u200f", "")  # RTL mark
    text = text.replace("\u00a0", " ")  # Non-breaking space to regular space

    # 5. Clinical LaTeX De-Delimiter
    if clean_latex:
        text = clean_clinical_latex(text)

    # 6. ISMP / FDA Clinical Safety Canonicalization
    if enforce_ismp:
        text = re.sub(r"([0-9\.\s])[µμ]g\b", r"\1mcg", text)
        text = re.sub(r"\b[µμ]g\b", "mcg", text)
        text = re.sub(r"([0-9\.\s])ug\b", r"\1mcg", text)
        text = re.sub(r"\bug\b", "mcg", text)

        # ISMP dose rewrites (trailing/leading zeros, QD, IU, U) only for generated output
        if rewrite_doses:
            text = apply_ismp_dose_rewrites(text)

        text = text.replace("≥", ">=")
        text = text.replace("≤", "<=")
        text = text.replace("±", "+/-")
        text = text.replace("°C", " deg C")
        text = text.replace("—", " - ")
        text = text.replace("–", " - ")
        text = text.replace("’", "'").replace("‘", "'")
        text = text.replace("“", '"').replace("”", '"')

    return text

def cleanroom_docx_filter(text: str) -> str:
    """
    Sanitizes markdown specifically before document publishing into Word (.docx).
    Converts remaining math delimiters, normalizes hyphens, and ensures zero broken escapes.
    """
    if not text:
        return ""
    text = sanitize_for_llm(text, enforce_ismp=True, clean_latex=True)
    # Convert remaining display math $$ ... $$ to plain text formula
    text = re.sub(r"\$\$\s*([^\$]+?)\s*\$\$", r"\1", text)
    # Convert remaining inline math $ ... $ to plain text
    text = re.sub(r"\$([^\$\n]+?)\$", r"\1", text)
    # Clean double hyphens to en-dash / spaced hyphen
    text = re.sub(r"(?<!-)--(?!-)", " - ", text)
    return text

def safe_json_dumps(obj: Any, indent: Optional[int] = 2) -> str:
    """Serializes data to JSON with ensure_ascii=False so LLMs receive pure Unicode."""
    return json.dumps(obj, ensure_ascii=False, indent=indent)

EXCLUDE_DIRS = {"rag_pipeline_output", ".git", "__pycache__", ".pytest_cache", "node_modules"}
# Image/page folders hold no text the guard checks; skipping them keeps whole-package audits fast.
NON_TEXT_DIRS = {"assets", "figures", "pages", "images", "__pycache__"}
PROTECTED_MARKERS = ("_CHECKPOINT.json", "CORPUS_OUTPUT_PROTECTED.json", "CORPUS_TRUST_STATUS")
IGNORED_AUDIT_FILES = {"guard.py", "cdss_encoding_guard.py", "test_guard.py", "test_consistency.py"}

def audit_directory(target_dir: Path, include_outputs: bool = False) -> Dict[str, Any]:
    """Scans all text/json files in target_dir and returns detailed audit metrics.

    Blocking violations (status FAIL): encoding corruption, raw microgram symbols, legacy corruption.
    ISMP dose-writing issues are reported as non-blocking `advisories`, because source text is kept verbatim.
    include_outputs=True also scans rag_pipeline_output/ folders (read-only), e.g. to find legacy corruption.
    """
    scanned = 0
    clean = 0
    violations = []
    advisories = []
    excluded = EXCLUDE_DIRS - {"rag_pipeline_output"} if include_outputs else EXCLUDE_DIRS

    for root, dirs, files in os.walk(target_dir):
        # Prune internal and cache directories
        dirs[:] = [d for d in dirs if d not in excluded and d not in NON_TEXT_DIRS and not d.startswith(".")]
        for f in files:
            if f.lower().endswith((".md", ".json", ".py", ".csv", ".txt", ".gbnf")):
                if f.lower() in IGNORED_AUDIT_FILES or f.endswith(".sha256"):
                    continue
                fp = Path(root) / f
                scanned += 1
                try:
                    content = fp.read_text(encoding="utf-8", errors="strict")
                    hits = CORRUPTION_REGEX.findall(content)
                    adv = ISMP_ADVISORY_REGEX.findall(content)
                    if adv:
                        advisories.append({
                            "file": str(fp.relative_to(target_dir)),
                            "issue": "ISMP dose-writing advisory (not rewritten in source)",
                            "hits": len(adv),
                            "samples": [a.strip() for a in adv[:3]]
                        })
                    if hits:
                        violations.append({
                            "file": str(fp.relative_to(target_dir)),
                            "issue": "Mojibake/Invisible artifact or OCR LaTeX tag / ISMP violation",
                            "hits": len(hits),
                            "samples": hits[:3]
                        })
                    else:
                        clean += 1
                except UnicodeDecodeError as e:
                    violations.append({
                        "file": str(fp.relative_to(target_dir)),
                        "issue": f"UnicodeDecodeError: {e}",
                        "hits": 1,
                        "samples": ["DECODE_ERROR"]
                    })

    status = "PASS" if not violations else "FAIL"
    return {
        "status": status,
        "total_scanned": scanned,
        "clean_files": clean,
        "violations": violations,
        "advisories": advisories
    }

def looks_non_utf8_text(raw: bytes) -> bool:
    """UTF-16/32 (BOM) or NUL-bearing data: must never be run through the byte-wise cp1252 repair, which
    rewrites it as UTF-8 garbage ("ÿþD\\x00o\\x00...")."""
    return raw.startswith((b"\xff\xfe", b"\xfe\xff", b"\x00\x00\xfe\xff")) or b"\x00" in raw[:8192]


def safe_decode_text(raw_bytes: bytes) -> str:
    """
    Decodes text safely without corrupting valid multi-byte UTF-8 sequences
    or crashing on stray single-byte CP1252 characters.
    Uses surrogateescape to isolate invalid UTF-8 bytes and maps only those bytes
    via CP1252 where possible.
    """
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        raw_bytes = raw_bytes[3:]
    try:
        return raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        pass

    # Decode with surrogateescape: valid UTF-8 sequences decode properly;
    # each invalid byte becomes a surrogate code point in U+DC80..U+DCFF.
    decoded = raw_bytes.decode("utf-8", errors="surrogateescape")
    out = []
    for ch in decoded:
        cp = ord(ch)
        if 0xDC80 <= cp <= 0xDCFF:
            byte_val = cp - 0xDC00
            try:
                out.append(bytes([byte_val]).decode("cp1252"))
            except UnicodeDecodeError:
                out.append("\ufffd")
        else:
            out.append(ch)
    return "".join(out)

def fix_directory(target_dir: Path, enforce_ismp: bool = True, clean_latex: bool = True, dry_run: bool = False) -> int:
    """Repairs mojibake, strips BOMs, and normalizes files in-place while protecting RAG pipelines and checkpoints.
    A directory holding a checkpoint/trust marker is skipped TOGETHER WITH ITS SUBDIRECTORIES. UTF-16/32 and
    binary-looking files are skipped, never rewritten. dry_run reports what would change and writes nothing.
    Returns the number of files fixed (or that would be fixed)."""
    fixed_count = 0
    skipped: List[str] = []
    for root, dirs, files in os.walk(target_dir):
        # Prune excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and d not in NON_TEXT_DIRS and not d.startswith(".")]
        # Skip directories protected by RAG checkpoint or trust markers (and everything beneath them)
        if any(f.endswith("_CHECKPOINT.json") or f in PROTECTED_MARKERS for f in files):
            dirs[:] = []
            continue

        for f in files:
            if f.lower().endswith((".md", ".json", ".py", ".csv", ".txt", ".gbnf")):
                if f.lower() in IGNORED_AUDIT_FILES or f in PROTECTED_MARKERS or f.endswith(".sha256") or f.endswith("_CHECKPOINT.json"):
                    continue
                fp = Path(root) / f
                try:
                    raw = fp.read_bytes()
                except Exception as e:
                    skipped.append(f"{fp}: unreadable ({e.__class__.__name__})")
                    continue
                if looks_non_utf8_text(raw):
                    skipped.append(f"{fp}: UTF-16/32 or binary-looking, not touched")
                    continue
                is_valid_utf8 = True
                try:
                    raw.decode("utf-8")
                except UnicodeDecodeError:
                    is_valid_utf8 = False
                text = safe_decode_text(raw)

                # enforce_ismp / clean_latex are accepted for CLI compatibility but no longer rewrite source text
                cleaned = repair_source_text(text)
                if cleaned != text or raw.startswith(b"\xef\xbb\xbf") or not is_valid_utf8:
                    if not dry_run:
                        fp.write_text(cleaned, encoding="utf-8")
                    fixed_count += 1
    for s in skipped:
        print(f"[MOJIBAKE-GUARD] skipped {s}", file=sys.stderr)
    return fixed_count


def main():
    parser = argparse.ArgumentParser(description="CDSS Unicode & Anti-Mojibake Guard")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # audit
    p_audit = subparsers.add_parser("audit", help="Audit directory for encoding errors without modifying files")
    p_audit.add_argument("--target-dir", "-t", required=True, help="Path to directory to audit")
    p_audit.add_argument("--include-outputs", action="store_true", help="Also scan rag_pipeline_output/ folders (read-only), e.g. for legacy corruption")

    # fix
    p_fix = subparsers.add_parser("fix", help="Repair encoding damage in-place (mojibake, BOM, invisible chars, CP1252 bytes); printed text is kept verbatim")
    p_fix.add_argument("--target-dir", "-t", required=True, help="Path to directory to repair")
    p_fix.add_argument("--dry-run", action="store_true", help="Report files that would be repaired; write nothing")
    p_fix.add_argument("--enforce-ismp", action="store_true", default=True, help="Deprecated no-op: ISMP conversions apply to generated output only")
    p_fix.add_argument("--clean-latex", action="store_true", default=True, help="Deprecated no-op: LaTeX is cleaned in generated output only")

    # gate
    p_gate = subparsers.add_parser("gate", help="Blocking pre-flight gate for build pipelines (exit code 0/1)")
    p_gate.add_argument("--target-dir", "-t", required=True, help="Path to directory to check")
    p_gate.add_argument("--include-outputs", action="store_true", help="Also scan rag_pipeline_output/ folders")

    # sanitize
    p_san = subparsers.add_parser("sanitize", help="Sanitize a specific file")
    p_san.add_argument("--file", "-f", required=True, help="Source file")
    p_san.add_argument("--output", "-o", help="Output file (overwrites source if omitted)")
    p_san.add_argument("--enforce-ismp", action="store_true", default=True)
    p_san.add_argument("--clean-latex", action="store_true", default=True)
    p_san.add_argument("--rewrite-doses", action="store_true", default=False,
                       help="Apply ISMP dose rewrites (5.0 mg -> 5 mg, QD -> once daily). Use only on generated output.")

    # cleanroom-docx
    p_cdox = subparsers.add_parser("cleanroom-docx", help="Sanitize markdown for Word .docx document generation")
    p_cdox.add_argument("--file", "-f", required=True, help="Source markdown file")
    p_cdox.add_argument("--output", "-o", help="Output sanitized markdown file (overwrites source if omitted)")

    args = parser.parse_args()
    target = Path(args.target_dir) if hasattr(args, "target_dir") and args.target_dir else None

    if args.command == "audit":
        res = audit_directory(target, include_outputs=args.include_outputs)
        print(f"[MOJIBAKE-GUARD] Audited: {target}")
        print(f"[MOJIBAKE-GUARD] Status: {res['status']}")
        print(f"[MOJIBAKE-GUARD] Clean: {res['clean_files']} / {res['total_scanned']}")
        if res["violations"]:
            print(f"[MOJIBAKE-GUARD] Violations ({len(res['violations'])}):")
            for v in res["violations"][:15]:
                print(f"  - {v['file']}: {v['issue']} (samples: {v['samples']})")
            sys.exit(1)
        else:
            print("[MOJIBAKE-GUARD] 100% of files clean. No mojibake or raw LaTeX detected.")
            if res["advisories"]:
                print(f"[MOJIBAKE-GUARD] ISMP advisories (non-blocking, source kept verbatim): {len(res['advisories'])} file(s)")
                for v in res["advisories"][:10]:
                    print(f"  - {v['file']}: {v['samples']}")
            sys.exit(0)

    elif args.command == "fix":
        count = fix_directory(target, enforce_ismp=args.enforce_ismp, clean_latex=args.clean_latex, dry_run=getattr(args, 'dry_run', False))
        print(f"[MOJIBAKE-GUARD] Fixed {count} file(s) in: {target}")

    elif args.command == "gate":
        res = audit_directory(target, include_outputs=args.include_outputs)
        if res["status"] == "PASS":
            print(f"[MOJIBAKE-GUARD-GATE] PASS: {target} is 100% clean.")
            sys.exit(0)
        else:
            print(f"[MOJIBAKE-GUARD-GATE] FAIL: Found {len(res['violations'])} corrupted file(s) in {target}!")
            sys.exit(1)

    elif args.command == "sanitize":
        src = Path(args.file)
        dst = Path(args.output) if args.output else src
        txt = safe_decode_text(src.read_bytes())
        clean_txt = sanitize_for_llm(txt, enforce_ismp=args.enforce_ismp, clean_latex=args.clean_latex,
                                     rewrite_doses=args.rewrite_doses)
        dst.write_text(clean_txt, encoding="utf-8")
        print(f"[MOJIBAKE-GUARD] Sanitized {src} -> {dst}")

    elif args.command == "cleanroom-docx":
        src = Path(args.file)
        dst = Path(args.output) if args.output else src
        txt = safe_decode_text(src.read_bytes())
        clean_txt = cleanroom_docx_filter(txt)
        dst.write_text(clean_txt, encoding="utf-8")
        print(f"[MOJIBAKE-GUARD] Cleanroom docx filtered {src} -> {dst}")

if __name__ == "__main__":
    main()
