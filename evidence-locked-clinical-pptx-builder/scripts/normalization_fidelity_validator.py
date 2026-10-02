from __future__ import annotations
import argparse, json, re
try:
    from scripts.common import read_csv
except ModuleNotFoundError:
    from common import read_csv

ALLOWED={'soft_hyphen_repair','line_break_join','ocr_spacing_repair','citation_reference_number_removal','extraction_whitespace_normalization','none'}
PASS={'pass','yes','true','1','adjudicated','certified'}

UNIT=r'(?:mg/dL|mmol/L|mg|g|mcg|μg|mL/min(?:/1\.73\s*m(?:2|²))?|wk|weeks?|mo|months?|y|years?|d/wk|min/wk|mm\s*Hg)'
CLINICAL_PATTERNS=[
    re.compile(rf'(?:≥|≤|>|<|=|±)\s*\d+(?:\.\d+)?(?:\s*(?:-|–|to)\s*\d+(?:\.\d+)?)?(?:\s*{UNIT})?',re.I),
    re.compile(rf'\b\d+(?:\.\d+)?(?:\s*(?:-|–|to)\s*\d+(?:\.\d+)?)?\s*{UNIT}\b',re.I),
    re.compile(r'\b\d+(?:\.\d+)?\s*%',re.I),
    re.compile(r'\b(?:COR|class(?: of recommendation)?)\s*[:=-]?\s*(?:1|2a|2b|3)\b',re.I),
    re.compile(r'\bLOE\s*[:=-]?\s*(?:A|B-R|B-NR|C-LD|C-EO)\b',re.I),
]
MARKER_RE=re.compile(r'[*†‡§¶]+')
NEGATION_RE=re.compile(r'\b(?:not|no|without|contraindicated)\b',re.I)
SUPERSCRIPT_CIT_RE=re.compile(r'[⁰¹²³⁴⁵⁶⁷⁸⁹]+(?:[⁻–-][⁰¹²³⁴⁵⁶⁷⁸⁹]+)?(?:[,，][⁰¹²³⁴⁵⁶⁷⁸⁹]+)*')
# Conservative ASCII citation pattern: citation cluster immediately follows sentence
# punctuation (with optional whitespace). This intentionally does not match ordinary
# clinical numerals such as "LDL-C 190 mg/dL".
ASCII_CIT_RE=re.compile(r'(?<=[.!?])\s*\d{1,3}(?:\s*(?:,|–|-)\s*\d{1,3})+(?=\s*(?:$|[.;:),\]†‡§¶*]))')
ASCII_SINGLE_CIT_RE=re.compile(r'(?<=[.!?])\s*\d{1,2}(?=\s*(?:$|[.;:),\]†‡§¶*]))')


def clinical_tokens(text):
    out=[]
    for pat in CLINICAL_PATTERNS: out.extend(m.group(0) for m in pat.finditer(text or ''))
    out.extend(MARKER_RE.findall(text or ''))
    out.extend(m.group(0).lower() for m in NEGATION_RE.finditer(text or ''))
    return out


def strip_bibliographic_citations(text):
    s=SUPERSCRIPT_CIT_RE.sub('', text or '')
    s=ASCII_CIT_RE.sub('', s)
    s=ASCII_SINGLE_CIT_RE.sub('', s)
    return s


def _canon(s): return re.sub(r'\s+',' ',s or '').strip()


def validate(path):
    issues=[]
    for i,r in enumerate(read_csv(path),2):
        rid=(r.get('record_id') or r.get('recommendation_id') or f'row-{i}').strip(); src=r.get('source_text') or ''; norm=r.get('normalized_text') or ''
        mode=(r.get('text_handling_policy') or '').strip()
        if mode not in {'SOURCE_NATIVE_EXACT','SOURCE_NATIVE_NORMALIZED','PEDAGOGIC_PARAPHRASE'}:
            issues.append({'severity':'HIGH','id':rid,'issue':'invalid/missing text_handling_policy'}); continue
        if mode=='SOURCE_NATIVE_EXACT' and src != norm:
            issues.append({'severity':'HIGH','id':rid,'issue':'exact source text changed'})
        if mode=='SOURCE_NATIVE_NORMALIZED':
            t=(r.get('transformation_type') or '').strip()
            if t not in ALLOWED:
                issues.append({'severity':'HIGH','id':rid,'issue':f'unapproved normalization transformation: {t}'})
            src_tokens=clinical_tokens(src); norm_tokens=clinical_tokens(norm)
            if src_tokens != norm_tokens:
                issues.append({'severity':'CRITICAL','id':rid,'issue':f'clinically meaningful protected token mutation: {src_tokens} -> {norm_tokens}'})
            if t=='citation_reference_number_removal':
                stripped=strip_bibliographic_citations(src)
                if _canon(stripped) != _canon(norm):
                    issues.append({'severity':'CRITICAL','id':rid,'issue':'citation-reference removal changed non-citation content'})
            if not (r.get('transformation_log') or '').strip():
                issues.append({'severity':'MEDIUM','id':rid,'issue':'normalization lacks transformation_log'})
        status=(r.get('validation_status') or '').strip().lower()
        if status not in PASS:
            issues.append({'severity':'HIGH','id':rid,'issue':'normalization validation unresolved'})
    return {'gate':'NORMALIZATION_FIDELITY','issues':issues,'pass':not any(x['severity'] in {'CRITICAL','HIGH'} for x in issues)}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('csv'); a=ap.parse_args(); r=validate(a.csv); print(json.dumps(r,indent=2)); raise SystemExit(0 if r['pass'] else 1)
if __name__=='__main__': main()
