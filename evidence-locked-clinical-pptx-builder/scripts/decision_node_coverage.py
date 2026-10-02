from __future__ import annotations
import argparse, json
try:
    from scripts.common import read_csv, split_ids
except ModuleNotFoundError:
    from common import read_csv, split_ids


def audit(nodes,coverage,node_id='node_id'):
    n=read_csv(nodes); c=read_csv(coverage); required={r[node_id].strip() for r in n if r.get(node_id,'').strip()}; represented=set(); unchecked=[]
    for r in c:
        if r.get('checked','').strip().lower() not in {'yes','true','1','checked','pass'}: unchecked.append(r.get('source_section',''))
        represented.update(split_ids(r.get('node_ids','')))
    missing=sorted(required-represented)
    return {'nodes':len(required),'represented':len(required & represented),'missing':missing,'unchecked_sections':unchecked,'pass':not missing and not unchecked}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--nodes',required=True); ap.add_argument('--coverage',required=True); a=ap.parse_args(); r=audit(a.nodes,a.coverage); print(json.dumps(r,indent=2)); raise SystemExit(1 if not r['pass'] else 0)
if __name__=='__main__': main()
