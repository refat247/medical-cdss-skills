from __future__ import annotations
import argparse, json, re, hashlib
try:
    from scripts.common import read_csv
except ModuleNotFoundError:
    from common import read_csv

def norm(s): return re.sub(r'[^a-z0-9]+',' ',(s or '').lower()).strip()
def fingerprint(r,cols): return hashlib.sha256('||'.join(norm(r.get(c,'')) for c in cols).encode()).hexdigest()
def audit(path,cols):
    rows=read_csv(path); groups={}
    for i,r in enumerate(rows,2): groups.setdefault(fingerprint(r,cols),[]).append((i,r.get('case_id','')))
    dup=[{'fingerprint':k,'rows':v} for k,v in groups.items() if len(v)>1]
    return {'rows':len(rows),'exact_normalized_duplicate_groups':dup,'pass':not dup}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('cases'); ap.add_argument('--column',action='append',default=['distinct_decision','expected_answer','source_ids']); a=ap.parse_args(); r=audit(a.cases,a.column); print(json.dumps(r,indent=2)); raise SystemExit(1 if not r['pass'] else 0)
if __name__=='__main__': main()
