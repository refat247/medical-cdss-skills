from __future__ import annotations
import argparse, json, re
try:
    from scripts.common import read_csv, split_ids
except ModuleNotFoundError:
    from common import read_csv, split_ids

CONTAMINATION_PATTERNS = {
 'running_header': r'\b(?:CLINICAL STATEMENTS(?: AND GUIDELINES)?|Downloaded from|Blumenthal et al|Circulation\.\s*20\d\d)\b',
 'doi': r'\bDOI\s*:\s*10\.\d{4,9}/\S+',
 'page_string': r'\be\d{4}\b',
 'neighbour_heading': r'\b(?:Table\s+\d+\.|Figure\s+\d+\.|Estimated 10-Year ASCVD Risk|Severe Hypercholesterolemia With|Heart Failure With Reduced Ejection Fraction)\b'
}
PASS={'pass','yes','true','1','adjudicated'}

def validate(path):
    issues=[]
    for i,r in enumerate(read_csv(path),2):
        rid=(r.get('recommendation_id') or r.get('node_id') or f'row-{i}').strip()
        required=['source_id','source_object_type','start_locator','end_locator','source_section_id','source_section_title','boundary_validation_status']
        for col in required:
            if not (r.get(col) or '').strip(): issues.append({'severity':'HIGH','row':i,'id':rid,'issue':f'missing {col}'})
        text=(r.get('extracted_text') or r.get('source_text') or '')
        hits=[name for name,pat in CONTAMINATION_PATTERNS.items() if re.search(pat,text,re.I)]
        if hits: issues.append({'severity':'CRITICAL','row':i,'id':rid,'issue':f'boundary contamination detected: {hits}'})
        allowed_assoc=set(split_ids(r.get('associated_table_ids',''))+split_ids(r.get('associated_figure_ids',''))+split_ids(r.get('footnote_ids','')))
        displayed=set(split_ids(r.get('displayed_associated_ids','')))
        bad=sorted(displayed-allowed_assoc)
        if bad: issues.append({'severity':'CRITICAL','row':i,'id':rid,'issue':f'unbound associated source object(s): {bad}'})
        status=(r.get('boundary_validation_status') or '').strip().lower()
        sem=(r.get('boundary_semantic_review_status') or '').strip().lower()
        if status not in PASS:
            issues.append({'severity':'HIGH','row':i,'id':rid,'issue':'boundary validation not PASS'})
        # Every final source boundary receives semantic adjudication; deterministic checks are necessary but not sufficient.
        if sem not in PASS:
            issues.append({'severity':'HIGH','row':i,'id':rid,'issue':'mandatory boundary semantic review unresolved/failed'})
    return {'gate':'SOURCE_BOUNDARY_INTEGRITY','issues':issues,'pass':not issues}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('csv'); a=ap.parse_args(); r=validate(a.csv); print(json.dumps(r,indent=2)); raise SystemExit(0 if r['pass'] else 1)
if __name__=='__main__': main()
