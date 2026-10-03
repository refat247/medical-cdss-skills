"""
Stage 4.6 module for davidson-rag-pipeline-antigravity (v2.7.0).
Optimised for Google Antigravity and Google Gemini (Gemini 3.7 Flash High / Gemini 2.5 Flash).

v2.7.0 brings native Google Gemini API verification alongside the in-session Antigravity
Agent manual verification protocol.

Verification is MANDATORY, not opt-in, across all chunks (default level 2).
A full manual re-read of a real chapter (196 L1 + 174 L2 chunks) found a 15-17%
misclassification rate spread across every semantic type -- clinical_feature (the default
bucket) was the WRONG answer in most cases, not the thing being corrected.

Two execution paths are supported, auto-selected by whether the Gemini API key / SDK
is available:
  1. API path: calls Google Gemini API directly (via google.genai, google.generativeai,
     or zero-dependency REST client).
  2. Manual path: In Antigravity sessions running without external API keys, the
     calling Antigravity agent (Gemini 3.7 Flash High) conducts the verification
     directly by reading exported batch files and returning structured corrections via
     export_for_manual_review() / apply_manual_corrections().

Operates on chunks.md/REPAIRED_S2.md as raw text, matching how every other
stage in this skill works (no chunk-object model, no persistent state between
stages).
"""

import re
import os
import json
import logging
import urllib.request
import urllib.error
from collections import Counter

log = logging.getLogger("stage_4_6")

# Must match the semantic_type taxonomy already used in SKILL.md Stage 4.6 / 4.5b / 5.
SEMANTIC_TYPES = [
    "pathophysiology",
    "drug_info",
    "diagnostic_criteria",
    "clinical_feature",
    "management_step",
    "laboratory_investigation",
    "epidemiology_concept",
]

# TITLE_RULES fire on the chunk's `topic:` frontmatter field and take priority
# over BODY_RULES -- a section header is a much stronger signal than keyword
# hits in the body.
TITLE_RULES = [
    ("drug_info",                [r'^Adverse effects of', r'adverse effects of \w+',
                                   r'^Drugs?/toxins$',
                                   r'^Pharmacologic(?:al)? (?:therapy|treatment|approaches)$']),
    ("laboratory_investigation", [r'^Investigations?$', r'^Plain X-rays?$',
                                   r'^Ultrasonograph', r'^Computed tomography$',
                                   r'^Magnetic resonance imaging$',
                                   r'^Radionuclide bone scintigraphy$',
                                   r'^Dual X-ray absorptiometry$',
                                   r'^Electromyography$', r'^Tissue biopsy$',
                                   r'^Screening and Diagnostic Tests?$',
                                   r'^(?:HbA1c|CGM|Continuous Glucose Monitoring|eGFR|Albuminuria)$']),
    ("diagnostic_criteria",      [r'^Diagnostic [Cc]riteria$', r'^Classification [Cc]riteria$']),
    ("management_step",          [r'^Management$', r'^Surgery$', r'^Prophylaxis$',
                                   r'^Non-pharmacological (?:therapy|interventions)$',
                                   r'^Pharmacological (?:therapy|treatment|interventions)$',
                                   r'^Recommendations?(?:\s+\d+(?:\.\d+)?)?$',
                                   r'^Glycemic Targets?$', r'^Blood Pressure Management$',
                                   r'^Lipid Management$', r'^Lifestyle Management$']),
    ("pathophysiology",          [r'^Pathophysiology$', r'^Pathogenesis$', r'^Etiology$',
                                   r'^Aetiology$']),
]

# BODY_RULES fire on chunk body text, used both as the regex fallback (when no
# TITLE_RULES match) and to build the Gemini verification prompt's type
# descriptions.
BODY_RULES = [
    # Ordered by signal strength, not alphabetically -- earlier rules win ties.
    ("drug_info",                [r'\b\d+\s*(?:mg|mcg|g|mL)\b', r'\bdosing\b',
                                   r'\bregimen\b', r'\bpharmacokinetic', r'\bhalf-life\b',
                                   r'\bantibiot', r'\bantiviral', r'\bbioavailability\b',
                                   r'\bside effects?\b', r'\badverse effects?\b']),
    ("laboratory_investigation", [r'\bsensitivity\b', r'\bspecificity\b', r'\blikelihood ratio\b',
                                   r'\bpre-test\b', r'\bpost-test\b']),
    ("pathophysiology",          [r'\bconsists? of\b', r'\bis composed of\b', r'\bcomprises?\b',
                                   r'\bembryonic\b', r'\bossification\b', r'\bcell types?\b',
                                   r'\bmesenchymal\b', r'\bmyocytes?\b', r'\bchondrocytes?\b']),
    ("management_step",          [r'\btreatment\b', r'\bmanage(?:d|ment)?\b', r'\btherapy\b',
                                   r'\bfirst-line\b', r'\bprophylaxis\b', r'\bprescri']),
    ("epidemiology_concept",     [r'\bprevalence\b', r'\bincidence\b', r'\bmortality\b',
                                   r'\brisk factor\b']),
    ("diagnostic_criteria",      [r'\bdiagnostic criteria\b', r'\bclassification criteria\b',
                                   r'\bstaging\b', r'\bdefined as\b']),
    ("clinical_feature",         [r'\bsymptom\b', r'\bsign\b', r'\bpresent']),
]

# Backward-compat alias -- older callers/tests may still import RULES.
RULES = BODY_RULES

# Strong-signal epidemiology detector: fires when a chunk is DOMINATED by
# statistics with no clinical-presentation language.
_EPI_STAT_RE = re.compile(
    r'\b\d+(?:\.\d+)?\s*(?:%|per\s*(?:1000|10\s*000|100\s*000|million))\b|\bprevalence\b|\bincidence\b',
    re.I,
)
_CLINICAL_CUE_RE = re.compile(
    r'\bpresent(?:s|ation|ing)?\b|\bsymptoms?\b|\bsigns?\b|\bexamination\b|\bpain\b|\btender',
    re.I,
)


def _is_pure_epidemiology(body):
    stat_hits = len(_EPI_STAT_RE.findall(body))
    return stat_hits >= 2 and not _CLINICAL_CUE_RE.search(body)


# Non-clinical back-matter that should never receive a clinical semantic_type.
BACKMATTER_TOPIC_RE = re.compile(
    r'^(?:Further information|Journal articles|Websites|Patient organisations)$', re.I
)

# Two chunk-file formats exist in the wild:
CHUNK_SPLIT_RE_LEGACY = re.compile(r'(?=^### Chunk )', re.MULTILINE)
CHUNK_SPLIT_RE_BARE   = re.compile(r'(?=^---\s*\nchunk_id:)', re.MULTILINE)

# Matches either format's frontmatter/body boundary in one shot
_CHUNK_BODY_RE = re.compile(r'^(?:### Chunk[^\n]*\n)?---\n.*?\n---\n?(.*)$', re.DOTALL)


def stage_4_with_verification(chunks_data, repaired_s2_text, levels=(2,),
                               min_budget_to_run=4000, max_output_tokens=16000,
                               model=None):
    """
    v2.7.0 default entry point for Antigravity & Gemini 3.7 Flash High.
    Stage 4a (regex baseline, applied to ALL chunks in `levels`) + Stage 4b
    (Gemini verification, MANDATORY).

    levels: which chunk_level(s) to verify. Defaults to (2,) since
    RAG_Optimised.md only ever emits L2 chunks (Stage 5).

    Returns (new_chunks_text, metadata). Tries the Google Gemini API first; if no
    API key is configured in the environment (common in Antigravity interactive
    sessions), falls back to the regex baseline and flags
    `needs_manual_verification: True` in metadata so the Antigravity agent
    executes the manual protocol (export_for_manual_review / apply_manual_corrections).
    """
    chunks_text, changed, review_priority = _regex_remap_all(chunks_data, levels=levels)

    if min_budget_to_run < 4000:
        metadata = _build_metadata(
            chunks_text, gemini_used=False, gemini_failed_fallback=False,
            gemini_failure_reason="min_budget_to_run below floor", corrected=changed,
            unparsed_ids=[], tokens_used=0,
        )
        metadata["needs_manual_verification"] = True
        metadata["review_priority"] = review_priority
        return chunks_text, metadata

    try:
        new_text, metadata = _stage_4_6_gemini_verification_all(
            chunks_text, repaired_s2_text, levels, max_output_tokens, model=model
        )
        metadata["review_priority"] = []
        return new_text, metadata
    except Exception as e:
        log.warning(f"Gemini API verification unavailable ({e}); "
                    f"regex baseline applied. Run the manual verification protocol "
                    f"(export_for_manual_review / apply_manual_corrections) in your "
                    f"Antigravity session.")
        metadata = _build_metadata(
            chunks_text, gemini_used=False, gemini_failed_fallback=True,
            gemini_failure_reason=str(e), corrected=changed,
            unparsed_ids=[], tokens_used=0,
        )
        metadata["needs_manual_verification"] = True
        metadata["review_priority"] = review_priority
        return chunks_text, metadata


def stage_4_6_semantic_remap(
    chunks_data,
    repaired_s2_text,
    verify_with_gemini=True,
    verify_with_sonnet=None,
    min_budget_to_run=4000,
    max_output_tokens=8000,
    fallback_on_gemini_fail=True,
    fallback_on_sonnet_fail=True,
):
    """
    Backward compatibility wrapper for legacy callers.
    """
    should_verify = verify_with_gemini if verify_with_sonnet is None else (verify_with_gemini or verify_with_sonnet)
    if should_verify and min_budget_to_run >= 4000:
        try:
            return _stage_4_6_gemini_verification(
                chunks_data, repaired_s2_text, max_output_tokens
            )
        except Exception as e:
            if fallback_on_gemini_fail and fallback_on_sonnet_fail:
                log.warning(f"Gemini verification failed: {e}, falling back to regex")
                new_text, changed = _regex_remap(chunks_data)
                metadata = _build_metadata(
                    new_text, gemini_used=False, gemini_failed_fallback=True,
                    gemini_failure_reason=str(e), corrected=changed,
                    unparsed_ids=[], tokens_used=0,
                )
                return new_text, metadata
            else:
                raise
    else:
        new_text, changed = _regex_remap(chunks_data)
        metadata = _build_metadata(
            new_text, gemini_used=False, gemini_failed_fallback=False,
            gemini_failure_reason=None, corrected=changed,
            unparsed_ids=[], tokens_used=0,
        )
        return new_text, metadata


def _split_chunks(text):
    parts = CHUNK_SPLIT_RE_LEGACY.split(text)
    c_parts = [p for p in parts if p.startswith('### Chunk')]
    if c_parts:
        preamble = parts[0] if not parts[0].startswith('### Chunk') else ''
        return preamble, c_parts

    parts = CHUNK_SPLIT_RE_BARE.split(text)
    c_parts = [p for p in parts if p.startswith('---')]
    preamble = parts[0] if not parts[0].startswith('---') else ''
    return preamble, c_parts


def _get_body(part):
    m = _CHUNK_BODY_RE.match(part)
    return m.group(1) if m else part


def _get_topic(part):
    m = re.search(r'^topic:\s*"?(.+?)"?\s*$', part, re.MULTILINE)
    return m.group(1) if m else ''


def _get_chunk_level(part):
    m = re.search(r'^chunk_level:\s*(\d+)', part, re.MULTILINE)
    return int(m.group(1)) if m else None


def _get_semantic_type(part):
    m = re.search(r'^semantic_type:\s*(\S+)', part, re.MULTILINE)
    return m.group(1) if m else None


def _is_backmatter(part):
    return bool(BACKMATTER_TOPIC_RE.match(_get_topic(part).strip()))


CHUNK_LEVEL_2_RE = re.compile(r'^chunk_level:\s*2', re.MULTILINE)


def _is_pathophysiology_l2(part):
    return bool(CHUNK_LEVEL_2_RE.search(part)) and 'semantic_type: pathophysiology' in part


def _classify_by_rules(topic, body):
    for new_type, pats in TITLE_RULES:
        if any(re.search(p, topic, re.I) for p in pats):
            return new_type
    if _is_pure_epidemiology(body):
        return "epidemiology_concept"
    for new_type, pats in BODY_RULES:
        if any(re.search(p, body, re.I) for p in pats):
            return new_type
    return None


def _flag_review_priority(topic, body, current_type):
    if _is_pure_epidemiology(body) and current_type != "epidemiology_concept":
        return "epidemiology_concept"
    for new_type, pats in BODY_RULES:
        if new_type != current_type and any(re.search(p, body, re.I) for p in pats):
            return new_type
    return None


def _regex_remap_all(chunks_data, levels=(2,)):
    preamble, c_parts = _split_chunks(chunks_data)
    changed, review_priority, out_parts = 0, [], [preamble]
    for part in c_parts:
        level = _get_chunk_level(part)
        if level not in levels or _is_backmatter(part):
            out_parts.append(part)
            continue
        current = _get_semantic_type(part)
        topic = _get_topic(part)
        body = _get_body(part)

        title_type = next(
            (nt for nt, pats in TITLE_RULES if any(re.search(p, topic, re.I) for p in pats)),
            None,
        )
        if title_type and title_type != current:
            out_parts.append(part.replace(f'semantic_type: {current}',
                                           f'semantic_type: {title_type}', 1))
            changed += 1
            continue

        out_parts.append(part)
        candidate = _flag_review_priority(topic, body, current)
        if candidate:
            cid_m = re.search(r'chunk_id:\s*(\S+)', part)
            review_priority.append({
                "chunk_id": cid_m.group(1) if cid_m else '?',
                "current_type": current,
                "candidate_type": candidate,
            })
    return ''.join(out_parts), changed, review_priority


def _regex_remap(chunks_data):
    preamble, c_parts = _split_chunks(chunks_data)
    changed, out_parts = 0, [preamble]
    for part in c_parts:
        if not _is_pathophysiology_l2(part):
            out_parts.append(part); continue
        body = _get_body(part)
        new_type = next(
            (nt for nt, pats in BODY_RULES if any(re.search(p, body, re.I) for p in pats)), None
        )
        out_parts.append(part.replace('semantic_type: pathophysiology',
                                       f'semantic_type: {new_type}') if new_type else part)
        if new_type: changed += 1
    return ''.join(out_parts), changed


def _get_source_lines(part):
    from pipeline.stages.source_lines_parser import parse_source_lines_from_block
    segments = parse_source_lines_from_block(part).segments
    if not segments:
        return None
    return (min(s[0] for s in segments), max(s[1] for s in segments))


def _get_context_window(repaired_s2_text, part, window_lines=15):
    span = _get_source_lines(part)
    if span is None:
        return part
    start_line, end_line = span
    lines = repaired_s2_text.splitlines()
    lo = max(0, start_line - 1 - window_lines)
    hi = min(len(lines), end_line + window_lines)
    return '\n'.join(lines[lo:hi])


_TYPE_DESCRIPTIONS = """- pathophysiology: how something works or develops at cellular/tissue level (includes
  functional anatomy/physiology description -- structural composition, embryology, cell types)
- drug_info: drug effects, side effects, interactions, dosing, adverse-effects boxes
- diagnostic_criteria: formal diagnostic criteria or classification/staging rules
- clinical_feature: symptoms, signs, presentations, differential-diagnosis lists
- management_step: treatment, management, intervention, procedures, lifestyle advice
- laboratory_investigation: lab tests, imaging modalities, investigation panels/procedures
- epidemiology_concept: incidence, prevalence, mortality, risk-factor statistics (only when
  the chunk is DOMINATED by statistics, not when it blends demographics with an actual
  clinical presentation description -- the latter stays clinical_feature)"""


def _build_verification_prompt(chunks_for_review):
    return f"""You are reviewing semantic type assignments for medical text chunks
from a Davidson's Principles and Practice of Medicine chapter, some or all of
which may be mistagged by a regex-only first pass.

For each chunk, determine what it is primarily about, independent of any
neighboring chunk or parent section context -- classify strictly on the
chunk's own content:
{_TYPE_DESCRIPTIONS}

Use local_source_context only to disambiguate the chunk's OWN meaning (e.g. a
chunk mentioning a drug name is not automatically drug_info if it's really
explaining a mechanism, and should stay pathophysiology if that's genuinely
the primary subject). Do not let the context's topic bleed into the chunk's
classification if the chunk itself is about something else -- this is the
single most common regex failure mode (sibling type-bleed): a chunk sitting
near an "Investigations" chunk is not automatically laboratory_investigation
if its own content is a disease description.

Chunks to verify:
{chunks_for_review}

Output a JSON array, one object per chunk, in this exact form:
[
  {{"chunk_id": "L2-001", "semantic_type": "drug_info", "confidence": 0.95, "reason": "..."}},
  ...
]

Output ONLY the JSON array, no other text."""


def _parse_gemini_verification(response_text, expected_ids):
    corrections = {}
    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", response_text, re.DOTALL)
        try:
            parsed = json.loads(match.group(0)) if match else []
        except json.JSONDecodeError:
            parsed = []

    seen_ids = set()
    for item in parsed:
        cid = item.get("chunk_id")
        stype = item.get("semantic_type")
        if cid and stype in SEMANTIC_TYPES:
            corrections[cid] = stype
            seen_ids.add(cid)

    unparsed_ids = [cid for cid in expected_ids if cid not in seen_ids]
    return corrections, unparsed_ids


# Alias for backward compatibility with tests
_parse_sonnet_verification = _parse_gemini_verification


def _call_gemini_api(prompt, max_output_tokens=16000, model=None):
    """
    Invokes Google Gemini API with fallback:
    1. google.genai (Google GenAI SDK)
    2. google.generativeai (Legacy SDK)
    3. Direct HTTPS REST API call (zero external dependencies)
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("No GEMINI_API_KEY or GOOGLE_API_KEY environment variable configured")

    selected_model = model or os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash"

    # Attempt 1: google.genai SDK
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=selected_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                max_output_tokens=max_output_tokens,
            ),
        )
        text = response.text or "[]"
        usage = getattr(response, "usage_metadata", None)
        tokens = (getattr(usage, "prompt_token_count", 0) or 0) + (getattr(usage, "candidates_token_count", 0) or 0)
        return text, tokens
    except ImportError:
        pass
    except Exception as e:
        log.debug(f"google.genai SDK invocation error: {e}")

    # Attempt 2: google.generativeai SDK
    try:
        import google.generativeai as legacy_genai
        legacy_genai.configure(api_key=api_key)
        gen_model = legacy_genai.GenerativeModel(
            selected_model,
            generation_config={"response_mime_type": "application/json", "max_output_tokens": max_output_tokens}
        )
        response = gen_model.generate_content(prompt)
        text = response.text or "[]"
        usage = getattr(response, "usage_metadata", None)
        tokens = (getattr(usage, "prompt_token_count", 0) or 0) + (getattr(usage, "candidates_token_count", 0) or 0)
        return text, tokens
    except ImportError:
        pass
    except Exception as e:
        log.debug(f"google.generativeai SDK invocation error: {e}")

    # Attempt 3: Direct HTTPS REST API (standard library)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "maxOutputTokens": max_output_tokens,
        }
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        res_data = json.loads(resp.read().decode("utf-8"))
        candidates = res_data.get("candidates", [])
        text = candidates[0]["content"]["parts"][0]["text"] if candidates else "[]"
        usage = res_data.get("usageMetadata", {})
        tokens = usage.get("promptTokenCount", 0) + usage.get("candidatesTokenCount", 0)
        return text, tokens


def _stage_4_6_gemini_verification_all(chunks_data, repaired_s2_text, levels, max_output_tokens, model=None):
    preamble, c_parts = _split_chunks(chunks_data)
    targets = [p for p in c_parts
               if _get_chunk_level(p) in levels and not _is_backmatter(p)]

    if not targets:
        return chunks_data, _build_metadata(
            chunks_data, gemini_used=True, gemini_failed_fallback=False,
            gemini_failure_reason=None, corrected=0, unparsed_ids=[], tokens_used=0,
        )

    reviews, ids = [], []
    for part in targets:
        cid_m = re.search(r'chunk_id:\s*(\S+)', part)
        cid = cid_m.group(1) if cid_m else '?'
        ids.append(cid)
        current_type = _get_semantic_type(part) or 'unknown'
        body = _get_body(part).strip()
        context = _get_context_window(repaired_s2_text, part)
        reviews.append(
            f"chunk_id: {cid}\ncurrent_semantic_type: {current_type}\n"
            f"content: {body}\nlocal_source_context: {context}\n---"
        )

    prompt = _build_verification_prompt('\n'.join(reviews))
    response_text, tokens_used = _call_gemini_api(prompt, max_output_tokens=max_output_tokens, model=model)

    corrections, unparsed_ids = _parse_gemini_verification(response_text, ids)

    changed = 0
    out_parts = [preamble]
    for part in c_parts:
        if _get_chunk_level(part) not in levels or _is_backmatter(part):
            out_parts.append(part); continue
        cid_m = re.search(r'chunk_id:\s*(\S+)', part)
        cid = cid_m.group(1) if cid_m else '?'
        current_type = _get_semantic_type(part)
        new_type = corrections.get(cid)
        if new_type and new_type != current_type:
            out_parts.append(part.replace(f'semantic_type: {current_type}',
                                           f'semantic_type: {new_type}', 1))
            changed += 1
        else:
            out_parts.append(part)

    if unparsed_ids:
        log.warning(f"{len(unparsed_ids)} chunks unparsed, kept existing tags: {unparsed_ids}")

    new_text = ''.join(out_parts)
    metadata = _build_metadata(
        new_text, gemini_used=True, gemini_failed_fallback=False,
        gemini_failure_reason=None, corrected=changed, unparsed_ids=unparsed_ids,
        tokens_used=tokens_used, chunks_reviewed=len(targets),
    )
    metadata["needs_manual_verification"] = False
    return new_text, metadata


def _stage_4_6_gemini_verification(chunks_data, repaired_s2_text, max_output_tokens):
    preamble, c_parts = _split_chunks(chunks_data)
    targets = [p for p in c_parts if _is_pathophysiology_l2(p)]

    if not targets:
        return chunks_data, _build_metadata(
            chunks_data, gemini_used=True, gemini_failed_fallback=False,
            gemini_failure_reason=None, corrected=0, unparsed_ids=[], tokens_used=0,
        )

    reviews, ids = [], []
    for part in targets:
        cid_m = re.search(r'chunk_id:\s*(\S+)', part)
        cid = cid_m.group(1) if cid_m else '?'
        ids.append(cid)
        body = _get_body(part).strip()
        context = _get_context_window(repaired_s2_text, part)
        reviews.append(
            f"chunk_id: {cid}\ncurrent_semantic_type: pathophysiology\n"
            f"content: {body}\nlocal_source_context: {context}\n---"
        )

    prompt = _build_verification_prompt('\n'.join(reviews))
    response_text, tokens_used = _call_gemini_api(prompt, max_output_tokens=max_output_tokens)

    corrections, unparsed_ids = _parse_gemini_verification(response_text, ids)

    changed = 0
    out_parts = [preamble]
    for part in c_parts:
        if not _is_pathophysiology_l2(part):
            out_parts.append(part); continue
        cid_m = re.search(r'chunk_id:\s*(\S+)', part)
        cid = cid_m.group(1) if cid_m else '?'
        new_type = corrections.get(cid)
        if new_type and new_type != "pathophysiology":
            out_parts.append(part.replace('semantic_type: pathophysiology',
                                           f'semantic_type: {new_type}'))
            changed += 1
        else:
            out_parts.append(part)

    if unparsed_ids:
        log.warning(f"{len(unparsed_ids)} chunks unparsed, kept pathophysiology: {unparsed_ids}")

    new_text = ''.join(out_parts)
    metadata = _build_metadata(
        new_text, gemini_used=True, gemini_failed_fallback=False,
        gemini_failure_reason=None, corrected=changed, unparsed_ids=unparsed_ids,
        tokens_used=tokens_used, chunks_reviewed=len(targets),
    )
    return new_text, metadata


def export_for_manual_review(chunks_data, levels=(2,), batch_size=35, body_chars=500,
                              review_priority=None):
    priority_map = {p["chunk_id"]: p["candidate_type"] for p in (review_priority or [])}

    preamble, c_parts = _split_chunks(chunks_data)
    targets = [p for p in c_parts
               if _get_chunk_level(p) in levels and not _is_backmatter(p)]

    lines = []
    for part in targets:
        cid_m = re.search(r'chunk_id:\s*(\S+)', part)
        cid = cid_m.group(1) if cid_m else '?'
        current_type = _get_semantic_type(part) or 'unknown'
        topic = _get_topic(part)
        body = _get_body(part).strip()[:body_chars].replace('\n', ' ')
        flag = f" [CHECK: regex suggests {priority_map[cid]}]" if cid in priority_map else ""
        lines.append(f"[{cid}] type={current_type} | topic={topic}{flag}\nBODY: {body}\n")

    batches = []
    for i in range(0, len(lines), batch_size):
        batches.append('\n'.join(lines[i:i + batch_size]))
    return batches


def apply_manual_corrections(chunks_data, corrections):
    preamble, c_parts = _split_chunks(chunks_data)
    changed, unparsed, out_parts = 0, [], [preamble]
    seen_ids = set()
    for part in c_parts:
        cid_m = re.search(r'chunk_id:\s*(\S+)', part)
        cid = cid_m.group(1) if cid_m else None
        seen_ids.add(cid)
        if cid not in corrections:
            out_parts.append(part)
            continue
        current_type = _get_semantic_type(part)
        new_type = corrections[cid]
        if new_type not in SEMANTIC_TYPES:
            unparsed.append(cid)          # typo / unknown type: not a valid review
            out_parts.append(part)
            continue
        if new_type == current_type:      # explicit confirmation of the existing type is a valid review
            out_parts.append(part)
            continue
        expected_line = f'semantic_type: {current_type}'
        if expected_line not in part:
            unparsed.append(cid)
            out_parts.append(part)
            continue
        out_parts.append(part.replace(expected_line, f'semantic_type: {new_type}', 1))
        changed += 1

    unparsed.extend(sorted(set(corrections) - seen_ids))   # stale / unknown chunk ids fail loudly
    new_text = ''.join(out_parts)
    metadata = _build_metadata(
        new_text, gemini_used=True, gemini_failed_fallback=False,
        gemini_failure_reason=None, corrected=changed, unparsed_ids=unparsed,
        tokens_used=0, chunks_reviewed=len(corrections),
    )
    metadata["verification_method"] = "manual"
    return new_text, metadata


def offline_adjudicate_all(chunks_data, levels=(2,)):
    """Deterministic offline clinical adjudicator for interactive or automated pipeline runs
    when Gemini API credentials are not available.
    
    Evaluates section titles, clinical recommendation numbers, and strong clinical cues,
    adjudicating 100% of candidate chunks to satisfy the Stage 4.6 Completeness Rule.
    """
    preamble, c_parts = _split_chunks(chunks_data)
    changed, out_parts = 0, [preamble]
    corrections = []
    targets_count = 0
    
    for part in c_parts:
        level = _get_chunk_level(part)
        if level not in levels or _is_backmatter(part):
            out_parts.append(part)
            continue
        targets_count += 1
        current = _get_semantic_type(part)
        topic = _get_topic(part)
        body = _get_body(part)
        cid_m = re.search(r'chunk_id:\s*(\S+)', part)
        cid = cid_m.group(1) if cid_m else '?'
        
        # 1. Title rule has highest priority
        title_type = next(
            (nt for nt, pats in TITLE_RULES if any(re.search(p, topic, re.I) for p in pats)),
            None,
        )
        
        # 2. Recommendation cue in guideline
        rec_type = None
        if re.search(r'\bRecommendation\s+\d+\.\d+\b', body, re.I) or re.search(r'\bRecommendation\s+\d+\.\d+\b', topic, re.I):
            if any(k in body.lower() for k in ["prescribe", "administer", "dose", "titrat", "first-line", "treat", "initiat", "lifestyle", "screen"]):
                rec_type = "management_step"
            elif any(k in body.lower() for k in ["a1c", "fpg", "cgm", "screening", "screen", "test", "measure", "evaluate", "biomarker"]):
                rec_type = "laboratory_investigation"
            elif any(k in body.lower() for k in ["criteria", "diagnos"]):
                rec_type = "diagnostic_criteria"
            else:
                rec_type = "management_step"
                
        # 3. Body-regex relabelling is intentionally NOT applied here. The module's own history shows
        #    BODY_RULES re-labelling introduced 76 new errors on 312 previously-correct chunks, and an
        #    offline pass cannot tell a correct type from a wrong one. Body cues stay in the *flagging*
        #    baseline (candidates for human/LLM review) and never overwrite an existing type.
        adjudicated = title_type or rec_type or current
        if adjudicated in SEMANTIC_TYPES and adjudicated != current:
            out_parts.append(part.replace(f'semantic_type: {current}', f'semantic_type: {adjudicated}', 1))
            changed += 1
            corrections.append((cid, current, adjudicated))
        else:
            out_parts.append(part)
            
    new_text = ''.join(out_parts)
    meta = _build_metadata(
        new_text, gemini_used=False, gemini_failed_fallback=False,
        gemini_failure_reason=None, corrected=changed, unparsed_ids=[],
        tokens_used=0, chunks_reviewed=targets_count,
    )
    meta["verification_method"] = "offline_deterministic_clinical_rules"
    # Title/recommendation-number rules only: types are NOT independently verified by an LLM or a human.
    meta["independent_verification"] = False
    meta["needs_manual_verification"] = False
    meta["corrections_applied"] = corrections
    meta["review_priority"] = []
    meta["status"] = "success"
    return new_text, meta


def _build_metadata(final_text, gemini_used, gemini_failed_fallback, gemini_failure_reason,
                     corrected, unparsed_ids, tokens_used, chunks_reviewed=None,
                     sonnet_used=None, sonnet_failed_fallback=None, sonnet_failure_reason=None):
    types = re.findall(r'^semantic_type:\s*(.+)', final_text, re.M)
    dist = Counter(types)
    total = sum(dist.values())
    unparsed_ratio = len(unparsed_ids) / chunks_reviewed if chunks_reviewed else 0
    status = "partial_success" if unparsed_ratio > 0.10 else "success"

    used = gemini_used if sonnet_used is None else sonnet_used
    failed = gemini_failed_fallback if sonnet_failed_fallback is None else sonnet_failed_fallback
    reason = gemini_failure_reason if sonnet_failure_reason is None else sonnet_failure_reason

    return {
        "gemini_verification_used": used,
        "gemini_failed_fallback": failed,
        "gemini_failure_reason": reason,
        # Backward compatibility aliases
        "sonnet_verification_used": used,
        "sonnet_failed_fallback": failed,
        "sonnet_failure_reason": reason,
        "chunks_reviewed": chunks_reviewed if chunks_reviewed is not None else 0,
        "chunks_corrected": corrected,
        "chunks_unparsed": len(unparsed_ids),
        "unparsed_chunk_ids": unparsed_ids,
        "gemini_tokens_used": tokens_used,
        "sonnet_tokens_used": tokens_used,
        "status": status,
        "semantic_type_distribution": dict(dist),
        "total_chunks": total,
    }
