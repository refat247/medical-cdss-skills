"""Stage 4 — Header Map (4A) & Deterministic Hybrid Slicer Engine (4B) Module (v2.15.0).

Encapsulates:
- Stage 4A: Pre-flight heading-depth manifest & header map (Rule J3)
- Stage 4B: Deterministic hybrid code-slicing parser with parent disease slug inheritance (Rule P),
  flat-## fallback (Rule J), per-#### sub-sections (Rule J2), intro overviews (Rule Q),
  intra-section backmatter boundary detection, multi-modal figure asset extraction, and
  clinical algorithm / decision tree detection.
"""
import io
import json
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

from pipeline.checkpoint_utils import (
    format_markdown_provenance_header,
    load_checkpoint,
    mark_stage_complete,
    should_run_stage,
)



# Typographic ligatures and exotic spaces are safe to flatten. Everything else NFKC touches is NOT:
# it rewrites superscripts/subscripts (10^9 -> 109, m^2 -> m2, CO2), vulgar fractions, micro sign
# (U+00B5 -> Greek mu) and units, which silently changes clinical values.
_SAFE_COMPAT = {
    "\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi", "\ufb04": "ffl",
    "\ufb05": "st", "\ufb06": "st",
    "\u00a0": " ", "\u2007": " ", "\u2009": " ", "\u200a": " ", "\u202f": " ",
}
_INVISIBLE = ("\ufeff", "\u200b", "\u00ad")


def sanitize_chunk_text(text):
    """Stage 4B text hygiene: flatten ligatures / odd spaces and strip zero-width artifacts.
    Deliberately NOT unicodedata.NFKC -- see _SAFE_COMPAT."""
    for k, v in _SAFE_COMPAT.items():
        text = text.replace(k, v)
    for ch in _INVISIBLE:
        text = text.replace(ch, "")
    return text

def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"^\d+\.\d+\s*", "", s)
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", "_", s).strip("_")[:40]


def extract_figure_metadata(body_text: str, out_dir: Optional[str] = None) -> Tuple[str, List[str], List[str]]:
    """Extracts figure references, decoupled assets, and figure captions from chunk body."""
    assets = []
    captions = []

    # 1. Markdown image tags: ![alt](url)
    md_imgs = re.findall(r'!\[(.*?)\]\((.*?)\)', body_text)
    for alt, url in md_imgs:
        clean_url = url.strip()
        clean_alt = alt.strip()
        if clean_url and clean_url not in assets:
            assets.append(clean_url)
        if clean_alt and clean_alt not in captions:
            captions.append(clean_alt)

    # 2. Textbook figure citations / caption patterns: e.g. "Fig. 18.4: ...", "Figure 1.3 ..."
    fig_citations = re.findall(r'\b(Fig(?:ure)?\.?\s*\d+\.\d+(?:\s*[:—–-]\s*[^\n\)\;\.]+)?)\b', body_text, re.IGNORECASE)
    for fc in fig_citations:
        cleaned = fc.strip()
        if cleaned and cleaned not in captions:
            captions.append(cleaned)
        fig_match = re.search(r'Fig(?:ure)?\.?\s*(\d+)\.(\d+)', cleaned, re.IGNORECASE)
        if fig_match:
            ch_n, fig_n = fig_match.group(1), fig_match.group(2)
            base_stem = f"ch{int(ch_n):02d}_fig_{int(fig_n):02d}"

            # Dynamic extension resolution against assets/figures/ directory if present
            resolved_ext = None
            if out_dir:
                fig_dir = os.path.join(out_dir, "assets", "figures")
                for ext in [".jpeg", ".jpg", ".png", ".webp"]:
                    if os.path.exists(os.path.join(fig_dir, f"{base_stem}{ext}")):
                        resolved_ext = ext
                        break
            # v2.23.0 fix: default to .jpeg (davidson-ocr-preready standard) when assets folder is decoupled
            chosen_ext = resolved_ext if resolved_ext else ".jpeg"
            derived_asset = f"assets/figures/{base_stem}{chosen_ext}"
            if derived_asset not in assets:
                assets.append(derived_asset)

    has_figures = "true" if bool(assets or captions) else "false"
    return has_figures, assets, captions


def detect_clinical_algorithm(body_text: str, topic: str) -> Tuple[str, Optional[str]]:
    """Detects if chunk contains structured clinical decision logic, scoring, or stepwise escalation."""
    t_lower = topic.lower()
    b_lower = body_text.lower()

    # Scoring system detection
    scoring_keywords = [
        "score", "scoring system", "curb-65", "wells", "cha2ds2", "has-bled",
        "meld", "gcs", "glasgow coma", "nyha class", "child-pugh", "apache", "timi",
        "score ≥", "score >", "score <", "score <=", "score >="
    ]
    if any(k in t_lower or k in b_lower for k in scoring_keywords) and bool(re.search(r'\b\d+\s*(?:points?|pts?)\b|\bscore\s*[:=≥><]\s*\d+', b_lower)):
        return "true", "scoring_system"

    # Stepwise escalation
    escalation_keywords = [
        "step 1", "step 2", "step 3", "stepwise", "first-line", "second-line",
        "third-line", "stage 1", "stage 2", "escalat", "titrat"
    ]
    if any(k in t_lower for k in escalation_keywords) or (
        bool(re.search(r'\bstep\s*1\b.*?\bstep\s*2\b', b_lower, re.DOTALL)) or
        bool(re.search(r'\bfirst-line\b.*?\bsecond-line\b', b_lower, re.DOTALL))
    ):
        return "true", "stepwise_escalation"

    # Decision tree / conditional branch logic
    tree_keywords = [
        "algorithm", "flowchart", "decision tree", "diagnostic pathway",
        "management pathway", "clinical pathway", "if suspected"
    ]
    if any(k in t_lower for k in tree_keywords) or (
        bool(re.search(r'\bif\b.*?\b(?:then|proceed to|consider|indicated|perform)\b', b_lower, re.DOTALL)) and
        ("low risk" in b_lower or "high risk" in b_lower or "positive" in b_lower or "negative" in b_lower)
    ):
        return "true", "decision_tree"

    return "false", None


def detect_clinical_urgency_and_box(body_text: str, topic: str, is_algo: str = "false") -> Tuple[str, str]:
    """Classifies clinical urgency and specific visual archetype box type for CDSS prioritization."""
    t_lower, b_lower = topic.lower(), body_text[:300].lower()

    # Urgency classification
    emergency_kws = [
        "emergency", "resuscitation", "immediate management", "cardiac arrest",
        "anaphylaxis", "status epilepticus", "tension pneumothorax", "severe shock",
        "overdose management", "acute poisoning", "acute severe", "life-threatening"
    ]
    urgent_kws = [
        "urgent", "unstable", "rapidly progressive", "impending", "red flag",
        "admission criteria", "deterioration", "monitoring in icu", "high risk"
    ]

    if any(k in t_lower or k in b_lower for k in emergency_kws) or "▲ emergency" in b_lower or "emergency:" in b_lower:
        urgency = "emergency"
    elif any(k in t_lower or k in b_lower for k in urgent_kws):
        urgency = "urgent"
    else:
        urgency = "routine"

    # Box type classification
    if "emergency" in t_lower or "emergency" in b_lower[:150] or "resuscitation" in t_lower or "resuscitation" in b_lower[:150] or "▲ emergency" in b_lower or "cardiac arrest" in t_lower:
        box_type = "emergency_management"
    elif "prescribing point" in t_lower or "prescribing point" in b_lower[:150] or "drug safety" in t_lower:
        box_type = "prescribing_point"
    elif "practice point" in t_lower or "good practice point" in b_lower[:150]:
        box_type = "practice_point"
    elif any(l.strip().startswith("|") for l in body_text.splitlines()) and ("summary" in t_lower or "investigation" in t_lower or "overview" in t_lower):
        box_type = "summary_table"
    elif is_algo == "true":
        box_type = "clinical_algorithm"
    else:
        box_type = "none"

    return urgency, box_type


DRUG_SYNONYMS = {
    "paracetamol": ["acetaminophen", "tylenol"],
    "acetaminophen": ["paracetamol"],
    "adrenaline": ["epinephrine"],
    "epinephrine": ["adrenaline"],
    "noradrenaline": ["norepinephrine"],
    "norepinephrine": ["noradrenaline"],
    "salbutamol": ["albuterol"],
    "albuterol": ["salbutamol"],
    "frusemide": ["furosemide", "lasix"],
    "furosemide": ["frusemide", "lasix"],
    "pethidine": ["meperidine"],
    "meperidine": ["pethidine"],
    "lignocaine": ["lidocaine"],
    "lidocaine": ["lignocaine"],
    "bendroflumethiazide": ["thiazide"],
    "diamorphine": ["heroin", "diacetylmorphine"],
    "glyceryl trinitrate": ["nitroglycerin", "gtn"],
    "nitroglycerin": ["glyceryl trinitrate", "gtn"],
    "isoprenaline": ["isoproterenol"],
    "isoproterenol": ["isoprenaline"],
    "rifampicin": ["rifampin"],
    "rifampin": ["rifampicin"],
    "methohexitone": ["methohexital"],
    "thiopentone": ["thiopental"],
    "amoxicillin": ["amoxycillin"],
    "amoxycillin": ["amoxicillin"],
    "ciclosporin": ["cyclosporine"],
    "cyclosporine": ["ciclosporin"],
}


def detect_drug_synonyms(text: str) -> List[str]:
    """Finds cross-lexicon drug synonyms (USAN/INN vs British Pharmacopoeia)."""
    t_low = text.lower()
    found_synonyms = []
    for drug, syns in DRUG_SYNONYMS.items():
        if re.search(r'\b' + re.escape(drug) + r'\b', t_low):
            for s in syns:
                if s not in found_synonyms:
                    found_synonyms.append(s)
    return sorted(found_synonyms)


def infer_initial_semantic_type(title: str, body: str) -> str:
    t, b = title.lower(), body.lower()[:300]
    if any(k in t for k in ["adverse effect", "anti-arrhythmic", "drug", "pharmacotherapy", "dosing", "dose"]):
        return "drug_info"
    if any(k in t for k in ["investigation", "biomarker", "troponin", "ecg", "echocardiograph", "x-ray", "catheterisation", "mri", "ct"]):
        return "laboratory_investigation"
    if any(k in t for k in ["management", "treatment", "resuscitation", "therapy", "cardioversion", "ablation", "surgery", "pci", "cabg", "pericardiocentesis", "pacemaker"]):
        return "management_step"
    if any(k in t for k in ["clinical feature", "symptom", "sign", "presentation", "murmur", "pulse", "jvp", "examination"]):
        return "clinical_feature"
    if any(k in t for k in ["criteria", "score", "classification", "nyha", "ccs", "duke", "jones"]):
        return "diagnostic_criteria"
    if any(k in t for k in ["pathogenesis", "pathophysiology", "anatomy", "physiology", "mechanism", "aetiology", "cause"]):
        return "pathophysiology"
    if any(k in t for k in ["epidemiology", "prevalence", "incidence", "risk factor", "prognosis", "in old age", "in adolescence"]):
        return "epidemiology_concept"
    return "clinical_feature"


def make_chunk(
    cid: str,
    level: int,
    sem_type: str,
    disease: str,
    topic: str,
    start_l: int,
    end_l: int,
    body_text: str,
    page_numbers: Optional[List[int]] = None,
    pdf_page: Optional[int] = None,
    breadcrumb: Optional[str] = None,
    out_dir: Optional[str] = None,
) -> str:
    has_tbl = "true" if any(l.strip().startswith("|") for l in body_text.splitlines()) else "false"
    has_box = "true" if bool(re.search(r"(?:###\s*\d+\.\d+|Box\s*\d+\.\d+|▲)", body_text)) else "false"
    has_fig, fig_assets, fig_captions = extract_figure_metadata(body_text, out_dir=out_dir)
    is_algo, algo_type = detect_clinical_algorithm(body_text, topic)
    urgency, box_type = detect_clinical_urgency_and_box(body_text, topic, is_algo=is_algo)
    synonyms = detect_drug_synonyms(body_text + " " + topic)

    header_lines = [
        "---",
        f"chunk_id: {cid}",
        f"chunk_level: {level}",
    ]
    if page_numbers:
        header_lines.append(f"page_numbers: [{', '.join(str(p) for p in page_numbers)}]")
    if pdf_page is not None:
        header_lines.append(f"pdf_page: {pdf_page}")
    if breadcrumb:
        header_lines.append(f"breadcrumb: {json.dumps(breadcrumb, ensure_ascii=False)}")
    header_lines.extend([
        f"semantic_type: {sem_type}",
        f"disease_focus: {disease}",
        f"contains_tables: {has_tbl}",
        f"contains_boxes: {has_box}",
        f"contains_figures: {has_fig}",
    ])
    if fig_assets:
        header_lines.append(f"figure_assets: [{', '.join(json.dumps(a, ensure_ascii=False) for a in fig_assets)}]")
    if fig_captions:
        header_lines.append(f"figure_captions: [{', '.join(json.dumps(c, ensure_ascii=False) for c in fig_captions)}]")
    header_lines.append(f"is_clinical_algorithm: {is_algo}")
    if algo_type:
        header_lines.append(f"algorithm_type: {algo_type}")
    header_lines.append(f"clinical_urgency: {urgency}")
    if box_type != "none":
        header_lines.append(f"box_type: {box_type}")
    if synonyms:
        header_lines.append(f"synonyms: [{', '.join(json.dumps(s, ensure_ascii=False) for s in synonyms)}]")
    header_lines.extend([
        f"topic: {topic}",
        f'source_lines: "{start_l}-{end_l}"',
        "---"
    ])
    header = "\n".join(header_lines)
    return f"{header}\n\n{body_text.strip()}"


# An explanation ends only at the next ANSWER entry ("5.1 B", "Answer 5.2: C"), not at any line that merely begins
# with a decimal ("2.5 mg is the usual starting dose" used to cut the explanation and drop it from the L2 chunk).
MCQ_EXPLANATION_END_RE = re.compile(r"(?:Answer\s+)?\d+\.\d+\.?\s*[:—–-]?\s*(?:Answer\s*[:—–-]?\s*)?(?-i:[A-E])\b", re.IGNORECASE)


def run_stage_4a(rep_path: str, out_dir: str, prefix: str) -> dict:
    """Executes Stage 4A pre-flight heading map and manifest."""
    checkpoint, checkpoint_path = load_checkpoint(out_dir, prefix)
    if not should_run_stage(checkpoint, "4a"):
        return {"status": "skipped", "reason": "already complete"}

    with open(rep_path, encoding="utf-8") as f:
        # splitlines(), like Stage 4B and the source_lines parser: readlines() split on "\n" only, so a form feed
        # (common in PDF OCR) made Stage 4A's "Line N" disagree with Stage 4B's source_lines.
        lines = f.read().splitlines()

    hmap = [f"Line {i+1}: {l.rstrip()}" for i, l in enumerate(lines) if re.match(r"^#{1,4}\s", l)]

    sections = []
    cur = None
    for i, l in enumerate(lines):
        if re.match(r"^## [^#]", l):
            if cur:
                sections.append(cur)
            cur = {"title": l.rstrip(), "line": i + 1, "has_h3": False, "has_h4": False}
        elif cur and re.match(r"^### ", l):
            cur["has_h3"] = True
        elif cur and re.match(r"^#### ", l):
            cur["has_h4"] = True
    if cur:
        sections.append(cur)

    def strategy(s):
        if s["has_h3"]:
            return "per-### (and per-#### too if any #### also present — Rule J2)"
        if s["has_h4"]:
            return "per-#### (Rule J2 — NOT flat-fallback, #### is not 'no children')"
        return "flat-fallback: ONE L2 for the whole section (Rule J)"

    manifest = [
        f"| {s['title'][3:]} | line {s['line']} | ###={s['has_h3']} ####={s['has_h4']} | {strategy(s)} |"
        for s in sections
    ]
    manifest_header = "| ## section | location | children present | required L2 strategy |\n|---|---|---|---|"

    log_path = os.path.join(out_dir, f"{prefix}_AUDIT_REPORT.md")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n\n## Stage 4 Header Map ({len(hmap)} headers)\n\n" + "\n".join(hmap))
        f.write(f"\n\n## Stage 4A Heading-Depth Manifest ({len(sections)} ## sections) — Rule J3\n\n"
                + manifest_header + "\n" + "\n".join(manifest))

    h4_only = sum(1 for s in sections if s["has_h4"] and not s["has_h3"])
    flat = sum(1 for s in sections if not s["has_h3"] and not s["has_h4"])

    mark_stage_complete(
        checkpoint,
        checkpoint_path,
        "4a",
        output_file=os.path.basename(log_path),
        header_count=len(hmap),
        sections_h4_only=h4_only,
        sections_flat=flat,
    )
    return {"header_count": len(hmap), "sections_count": len(sections), "sections_h4_only": h4_only, "sections_flat": flat}


def run_stage_4b(rep_path: str, out_dir: str, prefix: str) -> dict:
    """Executes Stage 4B Deterministic Hybrid Slicer Engine."""
    checkpoint, checkpoint_path = load_checkpoint(out_dir, prefix)
    if not should_run_stage(checkpoint, "4b"):
        return {"status": "skipped", "reason": "already complete"}

    with open(rep_path, encoding="utf-8") as f:
        full_text = f.read().replace("\r\n", "\n").replace("\r", "\n")

    lines = full_text.splitlines()
    total_lines = len(lines)
    h2_indices = [idx for idx, l in enumerate(lines) if re.match(r"^##\s", l)]

    # 1. Build line-by-line page tracking map from <!-- page: N --> and <!-- pdf_page: N -->
    line_to_page = {}
    line_to_pdf_page = {}
    cur_p = None
    cur_pdf_p = None
    for idx, line in enumerate(lines):
        line_num = idx + 1
        m_page = re.search(r'<!--\s*page:\s*(\d+)(?:\s*\(pdf:\s*(\d+)\))?\s*-->', line)
        if m_page:
            cur_p = int(m_page.group(1))
            if m_page.group(2):
                cur_pdf_p = int(m_page.group(2))
        m_pdf = re.search(r'<!--\s*pdf_page:\s*(\d+)\s*-->', line)
        if m_pdf:
            cur_pdf_p = int(m_pdf.group(1))
        if cur_p is not None:
            line_to_page[line_num] = cur_p
        if cur_pdf_p is not None:
            line_to_pdf_page[line_num] = cur_pdf_p

    def get_chunk_pages(start_l: int, end_l: int) -> Tuple[Optional[List[int]], Optional[int]]:
        pgs = sorted(set(line_to_page[ln] for ln in range(start_l, min(end_l + 1, total_lines + 1)) if ln in line_to_page))
        pdf_pgs = sorted(set(line_to_pdf_page[ln] for ln in range(start_l, min(end_l + 1, total_lines + 1)) if ln in line_to_pdf_page))
        pdf_p = pdf_pgs[0] if pdf_pgs else None
        return (pgs if pgs else None), pdf_p

    # 2. Derive Chapter Title for Breadcrumbs
    h1_match = re.search(r"^#\s+([^#\n]+)", full_text, re.MULTILINE)
    ch_display = h1_match.group(1).strip() if h1_match else prefix.replace("_", " ")

    l1_chunks, l2_chunks = [], []
    l1_counter, l2_counter = 1, 1
    current_parent_disease = slugify(prefix)

    sections = []
    for i, start_idx in enumerate(h2_indices):
        end_idx = h2_indices[i + 1] if i + 1 < len(h2_indices) else total_lines
        sections.append((start_idx, end_idx))

    for start_idx, end_idx in sections:
        sec_lines = lines[start_idx:end_idx]
        sec_title = re.sub(r"^##\s+", "", sec_lines[0]).strip()

        if re.match(r"^(Further information|Journal articles?|Websites?|Patient organisations?)", sec_title, re.I):
            continue

        sec_slug = slugify(sec_title)
        if len(sec_slug) >= 5 and not any(k in sec_slug for k in ["investigation", "management", "clinical", "pathophysiology"]):
            current_parent_disease = sec_slug
        sec_disease = current_parent_disease

        if "multiple choice questions" in sec_title.lower():
            l1_cid = f"L1-{l1_counter:03d}"
            l1_counter += 1
            l1_body = "\n".join(sec_lines)
            l1_pgs, l1_pdf = get_chunk_pages(start_idx + 1, end_idx)
            l1_crumb = f"{ch_display} > {sec_title}"
            l1_chunks.append(make_chunk(l1_cid, 1, "diagnostic_criteria", "self_assessment", "Multiple Choice Questions", start_idx + 1, end_idx, l1_body, page_numbers=l1_pgs, pdf_page=l1_pdf, breadcrumb=l1_crumb, out_dir=out_dir))

            # Scan for MCQ answers/explanations within sec_lines
            mcq_answers = {}
            ans_block_start = None
            for j, l in enumerate(sec_lines):
                if re.match(r"^###?\s*(?:Answers|Answers to Multiple Choice Questions)", l, re.I):
                    ans_block_start = j
                    break
            if ans_block_start is not None:
                ans_text = "\n".join(sec_lines[ans_block_start:])
                # Multi-item True/False answers (e.g. 1.1 A: True, B: False, C: True, D: False, E: False)
                for m in re.finditer(r'(?:^|\n)(?:Answer\s+)?(\d+\.\d+)\.?\s*[:—–-]?\s*((?:[A-E]\s*[:—–-]?\s*(?:True|False|T|F)\b\s*[,;]?\s*)+)(.*?)(?=(?:\n(?:Answer\s+)?\d+\.\d+\.?\s*[:—–-]?\s*(?:Answer\s*[:—–-]?\s*)?(?-i:[A-E])\b|\Z))', ans_text, re.DOTALL | re.IGNORECASE):
                    q_num, ans_opts, exp = m.group(1), m.group(2).strip(), m.group(3).strip()
                    mcq_answers[q_num] = f"**Answers: {ans_opts}**\n{exp}".strip()
                # Single-letter choice answers (e.g. 1.1 Answer: A)
                for m in re.finditer(r'(?:^|\n)(?:Answer\s+)?(\d+\.\d+)\.?\s*[:—–-]?\s*(?:Answer\s*[:—–-]?)?\s*([A-E])\b[.:—–\s]*(.*?)(?=(?:\n(?:Answer\s+)?\d+\.\d+\.?\s*[:—–-]?\s*(?:Answer\s*[:—–-]?\s*)?(?-i:[A-E])\b|\Z))', ans_text, re.DOTALL | re.IGNORECASE):
                    q_num, ans_opt, exp = m.group(1), m.group(2), m.group(3).strip()
                    if q_num not in mcq_answers:
                        mcq_answers[q_num] = f"**Answer: {ans_opt.upper()}**\n{exp}".strip()

            mcq_starts = [j for j, l in enumerate(sec_lines) if re.match(r"^(?:###\s+)?\d+\.\d+[\.\s]", l.strip()) and (ans_block_start is None or j < ans_block_start)]
            for k, m_start in enumerate(mcq_starts):
                m_end = mcq_starts[k + 1] if k + 1 < len(mcq_starts) else (ans_block_start if ans_block_start is not None and ans_block_start > m_start else len(sec_lines))
                mcq_body = "\n".join(sec_lines[m_start:m_end]).strip()
                mcq_num_m = re.search(r"^(?:###\s+)?(\d+\.\d+)[\.\s]", sec_lines[m_start].strip())
                mcq_num = mcq_num_m.group(1) if mcq_num_m else f"{k+1}"
                mcq_stem_m = re.search(r"^(?:###\s+)?\d+\.\d+[\.\s]+(.+)", sec_lines[m_start].strip())
                mcq_stem = mcq_stem_m.group(1)[:50] if mcq_stem_m else sec_lines[m_start][:50]
                
                # Pair Answer & Explanation if available
                if mcq_num in mcq_answers and mcq_answers[mcq_num] not in mcq_body:
                    mcq_body = f"{mcq_body}\n\n### Answer & Explanation\n{mcq_answers[mcq_num]}"

                l2_cid = f"L2-{l2_counter:03d}"
                l2_counter += 1
                mcq_pgs, mcq_pdf = get_chunk_pages(start_idx + m_start + 1, start_idx + m_end)
                mcq_crumb = f"{ch_display} > {sec_title} > MCQ {mcq_num}"
                l2_chunks.append(make_chunk(l2_cid, 2, infer_initial_semantic_type(mcq_stem, mcq_body), sec_disease, f"MCQ {mcq_num}: {mcq_stem}", start_idx + m_start + 1, start_idx + m_end, mcq_body, page_numbers=mcq_pgs, pdf_page=mcq_pdf, breadcrumb=mcq_crumb, out_dir=out_dir))
            continue

        child_headings = []
        backmatter_rel = None
        for j, l in enumerate(sec_lines):
            if j == 0:
                continue
            m3, m4 = re.match(r"^###\s+(.+)$", l), re.match(r"^####\s+(.+)$", l)
            if m3:
                h_title = m3.group(1).strip()
                if re.match(r"^(Further information|Journal articles?|Websites?|Patient organisations?)", h_title, re.I):
                    if backmatter_rel is None:
                        backmatter_rel = j
                    continue
                if backmatter_rel is None:
                    child_headings.append((j, 3, h_title))
            elif m4:
                h_title = m4.group(1).strip()
                if re.match(r"^(Further information|Journal articles?|Websites?|Patient organisations?)", h_title, re.I):
                    if backmatter_rel is None:
                        backmatter_rel = j
                    continue
                if backmatter_rel is None:
                    child_headings.append((j, 4, h_title))

        effective_end_idx = (start_idx + backmatter_rel) if backmatter_rel is not None else end_idx
        if h2_indices and start_idx == h2_indices[0]:
            # v2.23.0 / v2.24.0 fix: skip ALL leading HTML comment provenance headers if present so source_lines match on-disk content
            prov_offset = 0
            curr = 0
            while curr < len(lines):
                while curr < len(lines) and not lines[curr].strip():
                    curr += 1
                if curr < len(lines) and lines[curr].strip().startswith("<!--"):
                    end_c = curr
                    while end_c < len(lines) and "-->" not in lines[end_c]:
                        end_c += 1
                    if end_c < len(lines):
                        curr = end_c + 1
                        prov_offset = curr
                        while prov_offset < len(lines) and not lines[prov_offset].strip():
                            prov_offset += 1
                        curr = prov_offset
                    else:
                        break
                else:
                    break
            actual_l1_start = prov_offset + 1 if prov_offset > 0 else 1
        else:
            actual_l1_start = start_idx + 1
        l1_body = "\n".join(lines[actual_l1_start - 1:effective_end_idx])
        l1_cid = f"L1-{l1_counter:03d}"
        l1_counter += 1
        l1_pgs, l1_pdf = get_chunk_pages(actual_l1_start, effective_end_idx)
        l1_crumb = f"{ch_display} > {sec_title}"
        l1_chunks.append(make_chunk(l1_cid, 1, infer_initial_semantic_type(sec_title, l1_body), sec_disease, sec_title, actual_l1_start, effective_end_idx, l1_body, page_numbers=l1_pgs, pdf_page=l1_pdf, breadcrumb=l1_crumb, out_dir=out_dir))

        if not child_headings:
            # Rule J4: Bold-Topic Micro-Splitting for flat monolithic sections (>40 lines)
            bold_headings = []
            if len(sec_lines) > 40:
                for j, l in enumerate(sec_lines):
                    if j == 0:
                        continue
                    mb = re.match(r"^\*\*(?:[a-zA-Z0-9\.\s—–-]+)\*\*", l.strip())
                    if mb:
                        bold_title = re.sub(r"^\*\*|\*\*.*$", "", l.strip()).strip()
                        if len(bold_title) >= 3 and len(bold_title) <= 60:
                            bold_headings.append((j, bold_title))

            if bold_headings and len(bold_headings) >= 2:
                first_bold_rel = bold_headings[0][0]
                intro_lines = lines[actual_l1_start - 1 : start_idx + first_bold_rel]
                intro_text = "\n".join(intro_lines).strip()
                if len(intro_lines) > 1 and len(intro_text) > len(sec_title) + 5:
                    l2_cid = f"L2-{l2_counter:03d}"
                    l2_counter += 1
                    intro_pgs, intro_pdf = get_chunk_pages(actual_l1_start, start_idx + first_bold_rel)
                    intro_crumb = f"{ch_display} > {sec_title} > Overview"
                    l2_chunks.append(make_chunk(l2_cid, 2, infer_initial_semantic_type(sec_title + " Overview", intro_text), sec_disease, f"{sec_title} — Overview", actual_l1_start, start_idx + first_bold_rel, intro_text, page_numbers=intro_pgs, pdf_page=intro_pdf, breadcrumb=intro_crumb, out_dir=out_dir))

                for k, (b_rel_start, b_title) in enumerate(bold_headings):
                    b_rel_end = bold_headings[k + 1][0] if k + 1 < len(bold_headings) else (backmatter_rel if backmatter_rel is not None else len(sec_lines))
                    b_lines = sec_lines[b_rel_start:b_rel_end]
                    b_body = "\n".join(b_lines).strip()
                    if not b_body:
                        continue
                    l2_cid = f"L2-{l2_counter:03d}"
                    l2_counter += 1
                    b_pgs, b_pdf = get_chunk_pages(start_idx + b_rel_start + 1, start_idx + b_rel_end)
                    b_crumb = f"{ch_display} > {sec_title} > {b_title}"
                    l2_chunks.append(make_chunk(l2_cid, 2, infer_initial_semantic_type(b_title, b_body), sec_disease, f"{sec_title} — {b_title}", start_idx + b_rel_start + 1, start_idx + b_rel_end, b_body, page_numbers=b_pgs, pdf_page=b_pdf, breadcrumb=b_crumb, out_dir=out_dir))
            else:
                l2_cid = f"L2-{l2_counter:03d}"
                l2_counter += 1
                l2_pgs, l2_pdf = get_chunk_pages(actual_l1_start, effective_end_idx)
                l2_chunks.append(make_chunk(l2_cid, 2, infer_initial_semantic_type(sec_title, l1_body), sec_disease, sec_title, actual_l1_start, effective_end_idx, l1_body, page_numbers=l2_pgs, pdf_page=l2_pdf, breadcrumb=l1_crumb, out_dir=out_dir))
        else:
            first_child_rel = child_headings[0][0]
            intro_lines = lines[actual_l1_start - 1 : start_idx + first_child_rel]
            intro_text = "\n".join(intro_lines).strip()
            if len(intro_lines) > 1 and len(intro_text) > len(sec_title) + 5:
                l2_cid = f"L2-{l2_counter:03d}"
                l2_counter += 1
                intro_pgs, intro_pdf = get_chunk_pages(actual_l1_start, start_idx + first_child_rel)
                intro_crumb = f"{ch_display} > {sec_title} > Overview"
                l2_chunks.append(make_chunk(l2_cid, 2, infer_initial_semantic_type(sec_title + " Overview", intro_text), sec_disease, f"{sec_title} — Overview", actual_l1_start, start_idx + first_child_rel, intro_text, page_numbers=intro_pgs, pdf_page=intro_pdf, breadcrumb=intro_crumb, out_dir=out_dir))

            for k, (ch_rel_start, ch_lvl, ch_title) in enumerate(child_headings):
                ch_rel_end = child_headings[k + 1][0] if k + 1 < len(child_headings) else (backmatter_rel if backmatter_rel is not None else len(sec_lines))
                ch_lines = sec_lines[ch_rel_start:ch_rel_end]
                ch_body = "\n".join(ch_lines).strip()
                if not ch_body:
                    continue
                ch_slug = slugify(ch_title)
                ch_disease = ch_slug if (len(ch_slug) >= 5 and not any(k in ch_slug for k in ["investigation", "management", "clinical", "pathophysiology"])) else sec_disease
                l2_cid = f"L2-{l2_counter:03d}"
                l2_counter += 1
                ch_pgs, ch_pdf = get_chunk_pages(start_idx + ch_rel_start + 1, start_idx + ch_rel_end)
                ch_crumb = f"{ch_display} > {sec_title} > {ch_title}"
                l2_chunks.append(make_chunk(l2_cid, 2, infer_initial_semantic_type(ch_title, ch_body), ch_disease, ch_title, start_idx + ch_rel_start + 1, start_idx + ch_rel_end, ch_body, page_numbers=ch_pgs, pdf_page=ch_pdf, breadcrumb=ch_crumb, out_dir=out_dir))

    chunk_path = os.path.join(out_dir, f"{prefix}_chunks.md")
    s4b_prov = format_markdown_provenance_header(rep_path, "4b")
    all_chunks = s4b_prov + "\n\n".join(l1_chunks + l2_chunks)

    all_chunks = sanitize_chunk_text(all_chunks)

    with open(chunk_path, "w", encoding="utf-8") as f:
        f.write(all_chunks)

    if not l1_chunks and not l2_chunks:
        # A document with no "## " section headings yields no chunks; that is a failed parse, not a completed stage
        # (it used to be COMPLETED and Stages 4.5 / 4.5c then cleared an empty chunk file).
        from pipeline.checkpoint_utils import mark_stage_blocked
        mark_stage_blocked(checkpoint, checkpoint_path, "4b", output_file=os.path.basename(chunk_path),
                           reason="0 L1 and 0 L2 chunks produced: the repaired source has no '## ' section headings")
        return {"l1_count": 0, "l2_count": 0, "sections_run": len(sections), "chunk_path": chunk_path,
                "blocked": True, "reason": "no chunks produced"}

    mark_stage_complete(
        checkpoint,
        checkpoint_path,
        "4b",
        output_file=os.path.basename(chunk_path),
        sections_run=len(sections),
        l1_count=len(l1_chunks),
        l2_count=len(l2_chunks),
    )
    return {
        "l1_count": len(l1_chunks),
        "l2_count": len(l2_chunks),
        "sections_run": len(sections),
        "chunk_path": chunk_path,
    }