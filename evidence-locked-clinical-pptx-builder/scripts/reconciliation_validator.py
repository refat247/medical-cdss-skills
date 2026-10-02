from __future__ import annotations
import argparse, json
try:
    from scripts.common import read_csv, split_ids
except ModuleNotFoundError:
    from common import read_csv, split_ids


def validate(nodes_a,nodes_b,recon):
    A={r['node_id'].strip() for r in read_csv(nodes_a) if r.get('node_id','').strip()}; B={r['node_id'].strip() for r in read_csv(nodes_b) if r.get('node_id','').strip()}; issues=[]
    for i,r in enumerate(read_csv(recon),2):
        refs=split_ids(r.get('source_item_a',''))+split_ids(r.get('source_item_b',''))
        for x in refs:
            if x not in A and x not in B: issues.append({'row':i,'issue':f'unknown source item {x}'})
        if not r.get('relationship','').strip(): issues.append({'row':i,'issue':'missing relationship'})
    return issues

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--nodes-a',required=True); ap.add_argument('--nodes-b',required=True); ap.add_argument('--reconciliation',required=True); a=ap.parse_args(); issues=validate(a.nodes_a,a.nodes_b,a.reconciliation); print(json.dumps({'pass':not issues,'issues':issues},indent=2)); raise SystemExit(1 if issues else 0)
if __name__=='__main__': main()
