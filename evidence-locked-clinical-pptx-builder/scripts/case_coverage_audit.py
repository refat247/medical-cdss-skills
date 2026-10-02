from __future__ import annotations
import argparse, json
try:
    from scripts.common import read_csv, split_ids
except ModuleNotFoundError:
    from common import read_csv, split_ids


def audit(nodes,cases,node_id_col='node_id',case_node_col='decision_node_ids'):
    nr=read_csv(nodes); cr=read_csv(cases); required={r[node_id_col].strip() for r in nr if r.get(node_id_col,'').strip() and r.get('explanatory_only','').strip().lower() not in {'yes','true','1'}}; represented=set()
    for r in cr: represented.update(split_ids(r.get(case_node_col,'')))
    missing=sorted(required-represented); extra=sorted(represented-{r[node_id_col].strip() for r in nr if r.get(node_id_col,'').strip()})
    return {'required_nodes':len(required),'represented':len(required & represented),'missing':missing,'extra':extra,'pass':not missing}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--nodes',required=True); ap.add_argument('--cases',required=True); ap.add_argument('--node-id-col',default='node_id'); ap.add_argument('--case-node-col',default='decision_node_ids'); a=ap.parse_args(); r=audit(a.nodes,a.cases,a.node_id_col,a.case_node_col); print(json.dumps(r,indent=2)); raise SystemExit(1 if not r['pass'] else 0)
if __name__=='__main__': main()
