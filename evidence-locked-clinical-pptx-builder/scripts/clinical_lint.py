from __future__ import annotations
import argparse, json
try:
    from scripts.common import read_csv, split_ids, EMPTY
except ModuleNotFoundError:
    from common import read_csv, split_ids, EMPTY


def lint(path,approved_sources,context_ids=()):
    issues=[]; approved=set(approved_sources); context=set(context_ids)
    for i,r in enumerate(read_csv(path),2):
        sid=r.get('slide_spec_id',r.get('slide','row'))
        sources=set(split_ids(r.get('source_ids','')))
        bad=sources-approved
        if bad: issues.append({'row':i,'id':sid,'issue':f'unapproved clinical source(s): {sorted(bad)}'})
        if sources & context: issues.append({'row':i,'id':sid,'issue':'context source used as clinical evidence'})
        if (r.get('exact_provenance') or '').strip().lower() in EMPTY and sources: issues.append({'row':i,'id':sid,'issue':'clinical source listed but exact provenance missing'})
        if 'operational' in (r.get('source_ids') or '').lower(): issues.append({'row':i,'id':sid,'issue':'operational context appears in clinical source field'})
    return issues

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('csv'); ap.add_argument('--approved',action='append',default=[]); ap.add_argument('--context',action='append',default=[]); a=ap.parse_args(); issues=lint(a.csv,a.approved,a.context); print(json.dumps({'pass':not issues,'issues':issues},indent=2)); raise SystemExit(1 if issues else 0)
if __name__=='__main__': main()
