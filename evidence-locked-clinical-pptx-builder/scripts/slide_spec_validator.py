from __future__ import annotations
import argparse, json
REQ=['slide_spec_id','slide_role','title_concept','source_ids','exact_provenance','speaker_note_requirement','status']
def validate(path,case_ids=None):
    rows=read_csv(path); issues=[]; ids=set(); known=set(case_ids or [])
    for i,r in enumerate(rows,2):
        sid=r.get('slide_spec_id','').strip()
        if not sid or sid in ids: issues.append({'row':i,'issue':'missing/duplicate slide_spec_id'})
        ids.add(sid)
        for c in REQ:
            if (r.get(c) or '').strip().lower() in EMPTY: issues.append({'row':i,'slide':sid,'issue':f'missing {c}'})
        if known:
            for cid in split_ids(r.get('case_ids','')):
                if cid not in known: issues.append({'row':i,'slide':sid,'issue':f'unknown case id {cid}'})
    return issues
try:
    from scripts.common import read_csv, split_ids, EMPTY
except ModuleNotFoundError:
    from common import read_csv, split_ids, EMPTY


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('spec'); ap.add_argument('--case',action='append',default=[]); a=ap.parse_args(); issues=validate(a.spec,a.case); print(json.dumps({'pass':not issues,'issues':issues},indent=2)); raise SystemExit(1 if issues else 0)
if __name__=='__main__': main()
