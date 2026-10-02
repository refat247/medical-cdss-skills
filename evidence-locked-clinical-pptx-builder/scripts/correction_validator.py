from __future__ import annotations
import argparse, json
try:
    from scripts.common import read_csv
except ModuleNotFoundError:
    from common import read_csv

def validate(corrections,supersessions):
    c=read_csv(corrections); s=read_csv(supersessions); issues=[]; cids={r.get('correction_id','').strip() for r in c}
    for i,r in enumerate(c,2):
        if not r.get('scope_locator','').strip(): issues.append({'row':i,'issue':'correction missing explicit scope_locator'})
        if r.get('status','').strip().lower() not in {'active','final','approved'}: issues.append({'row':i,'issue':'correction not active/final/approved'})
        if not r.get('original_source_id','').strip() or not r.get('correction_source_id','').strip(): issues.append({'row':i,'issue':'missing original/correction source id'})
    for i,r in enumerate(s,2):
        if r.get('correction_id','').strip() not in cids: issues.append({'row':i,'issue':'supersession references unknown correction'})
        if not r.get('scope_locator','').strip(): issues.append({'row':i,'issue':'supersession missing scope_locator'})
    return issues

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--corrections',required=True); ap.add_argument('--supersessions',required=True); a=ap.parse_args(); issues=validate(a.corrections,a.supersessions); print(json.dumps({'pass':not issues,'issues':issues},indent=2)); raise SystemExit(1 if issues else 0)
if __name__=='__main__': main()
