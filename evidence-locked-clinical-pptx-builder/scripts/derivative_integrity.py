from __future__ import annotations
import argparse, json, hashlib, re
try:
    from scripts.common import read_csv
except ModuleNotFoundError:
    from common import read_csv

DEFAULT_COLS=['source_derived_scenario','distinct_decision','expected_answer','source_ids','source_provenance','threshold_timing_dose','class_loe','terminology_labels']
def norm(s): return re.sub(r'\s+',' ',(s or '').strip())
def fp(r,cols): return hashlib.sha256('||'.join(norm(r.get(c,'')) for c in cols).encode()).hexdigest()
def verify(master,derivative,cols=DEFAULT_COLS):
    m={r['case_id']:r for r in read_csv(master)}; issues=[]; checked=0
    for i,r in enumerate(read_csv(derivative),2):
        cid=r.get('case_id','')
        if cid not in m: issues.append({'row':i,'case_id':cid,'issue':'case absent from master'}); continue
        checked+=1
        if fp(r,cols)!=fp(m[cid],cols): issues.append({'row':i,'case_id':cid,'issue':'clinical fingerprint mismatch'})
    return {'checked':checked,'issues':issues,'pass':not issues}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--master',required=True); ap.add_argument('--derivative',required=True); ap.add_argument('--column',action='append'); a=ap.parse_args(); r=verify(a.master,a.derivative,a.column or DEFAULT_COLS); print(json.dumps(r,indent=2)); raise SystemExit(1 if not r['pass'] else 0)
if __name__=='__main__': main()
