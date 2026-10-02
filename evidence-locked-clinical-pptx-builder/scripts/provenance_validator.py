from __future__ import annotations
import argparse, json
try:
    from scripts.common import read_csv, split_ids, EMPTY
except ModuleNotFoundError:
    from common import read_csv, split_ids, EMPTY


def validate(path,id_col='case_id',source_col='source_ids',prov_col='source_provenance',approved=None,required=()):
    rows=read_csv(path); issues=[]; approved=set(approved or [])
    for i,r in enumerate(rows,2):
        rid=(r.get(id_col) or f'row-{i}').strip(); src=split_ids(r.get(source_col,'')); prov=(r.get(prov_col) or '').strip().lower()
        if prov in EMPTY: issues.append({'row':i,'id':rid,'issue':'missing provenance'})
        if approved:
            bad=[x for x in src if x not in approved]
            if bad: issues.append({'row':i,'id':rid,'issue':f'unapproved source ids: {bad}'})
        for col in required:
            if (r.get(col) or '').strip().lower() in EMPTY: issues.append({'row':i,'id':rid,'issue':f'missing {col}'})
    return issues

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('csv'); ap.add_argument('--id-column',default='case_id'); ap.add_argument('--source-column',default='source_ids'); ap.add_argument('--provenance-column',default='source_provenance'); ap.add_argument('--approved',action='append',default=[]); ap.add_argument('--required',action='append',default=[]); a=ap.parse_args(); issues=validate(a.csv,a.id_column,a.source_column,a.provenance_column,a.approved,a.required); print(json.dumps({'pass':not issues,'issues':issues},indent=2)); raise SystemExit(1 if issues else 0)
if __name__=='__main__': main()
