"""Header Normalizer & OCR Artifact Cleaner for Davidson OCR Pre-Ready Pipeline."""
import re


def clean_ocr_running_headers(md_text: str) -> str:
    """Removes running headers, stray page numbers, and textbook watermark artifacts."""
    lines = md_text.splitlines()
    cleaned = []
    
    skip_exact = {
        "medical", "higher study", "elsevier", "davidson's principles and practice of medicine",
        "principles and practice of medicine", "clinical decision-making", "clinical decision making",
        "cardiovascular disease", "respiratory disease", "endocrinology and diabetes",
        "gastroenterology", "rheumatology and bone disease", "neurology",
        "infectious diseases", "nephrology", "haematology", "oncology",
        "national guideline for clinical management of dengue",
        "national guideline for the management of measles",
        "diabetesjournals.org/care", "diabetes carear"
    }

    for l in lines:
        s = l.strip()
        s_lower = s.lower()

        # Skip isolated running header watermarks and OCR math hallucinations
        if s_lower in skip_exact or re.match(r'^\\\(.*\\therefore.*\\\)$', s):
            continue

        # Skip journal running headers, mastheads, DOIs, and URLs
        if re.match(r'^.+?\bvolume\s+\d+.*supplement.*$', s_lower):
            continue
        if re.match(r'^[a-z]+ \d{4}\s*\|\s*volume \d+\s*\|\s*supplement \d+$', s_lower):
            continue
        if re.match(r'^diabetes care volume \d+,\s*supplement \d+,\s*[a-z]+ \d{4}$', s_lower):
            continue
        if re.match(r'^(?:https?://|doi(?:\.org)?/|downloaded from ).*$', s_lower):
            continue
        
        # Convert isolated running page numbers to page marker:
        # Bare digits (1-4 digits alone), supplement pages (S1-S9999, Suppl. 12, P-12, A1-A99)
        m_page = re.match(r'^(?:([A-Za-z]{1,2}|suppl\.?)[-\s]?)?(\d{1,4})$', s, re.IGNORECASE)
        if m_page:
            raw_pfx = m_page.group(1) or ""
            page_num = m_page.group(2)
            pfx_clean = "S" if raw_pfx.upper().startswith("S") else raw_pfx.upper()
            # Preserve 4-digit publication years alone on a line without prefix (1900-2099)
            if not pfx_clean and 1900 <= int(page_num) <= 2099:
                cleaned.append(l)
                continue
            cleaned.append(f"<!-- page: {pfx_clean}{page_num} -->")
            continue

        # Convert running header with page number e.g. "142 • CLINICAL DECISION-MAKING" or "CLINICAL DECISION-MAKING • 142"
        m_hdr_page = re.match(r'^(\d{1,4})\s*[·•]\s*[A-Z\s\-]+$', s) or re.match(r'^[A-Z\s\-]+\s*[·•]\s*(\d{1,4})$', s)
        if m_hdr_page:
            page_num = m_hdr_page.group(1)
            cleaned.append(f"<!-- page: {page_num} -->")
            continue

        # Skip running chapter marker lines e.g. "CHAPTER 1 • CLINICAL DECISION-MAKING"
        if re.match(r'^CHAPTER\s+\d+\s*[·•]\s*[A-Z\s\-]+$', s, re.IGNORECASE):
            continue

        cleaned.append(l)

    result = "\n".join(cleaned)
    # Collapse duplicate consecutive page comments
    result = re.sub(r'(<!-- page: [A-Za-z0-9\-]+ -->\n?)+', r'\1', result)
    # Collapse 3+ consecutive newlines to 2
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result


def normalize_heading_hierarchy(md_text: str) -> str:
    """Ensures consistent # (Title), ## (Section), ### (Subsection/Box) hierarchy."""
    lines = md_text.splitlines()
    normalized = []

    seen_h1 = False
    for l in lines:
        if l.startswith("# "):
            if not seen_h1:
                normalized.append(l)
                seen_h1 = True
            else:
                # Down-level subsequent # headers to ##
                normalized.append(f"## {l[2:].strip()}")
        elif re.match(r'^(?:Box|Table)\s*\d+\.\d+', l.strip(), re.IGNORECASE):
            # Ensure Box/Table headings have ###
            normalized.append(f"### {l.strip()}")
        elif re.match(r'^\d+\.\d+\s+[A-Z]', l.strip()):
            # e.g. "1.1 Root causes of diagnostic error" -> "### 1.1 Root causes..."
            normalized.append(f"### {l.strip()}")
        else:
            normalized.append(l)

    return "\n".join(normalized)
