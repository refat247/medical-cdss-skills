from __future__ import annotations
import argparse, json
try:
    from scripts.common import read_csv
except ModuleNotFoundError:
    from common import read_csv

def validate(nodes, source_inventory):
    inv={r.get('source_recommendation_id','').strip():r for r in read_csv(source_inventory)}; issues=[]
    for i,r in enumerate(read_csv(nodes),2):
        rid=(r.get('recommendation_id') or r.get('node_id') or f'row-{i}').strip(); srid=(r.get('source_recommendation_id') or '').strip(); src=inv.get(srid)
        if not src:
            issues.append({'severity':'HIGH','id':rid,'issue':f'unknown source recommendation {srid}' }); continue
        for col in ('source_section_id','source_section_title','recommendation_table_id','recommendation_table_heading'):
            expected=(src.get(col) or '').strip(); actual=(r.get(col) or '').strip()
            if expected and actual != expected:
                issues.append({'severity':'HIGH','id':rid,'issue':f'{col} mismatch: {actual!r} != {expected!r}'})
        # Editorial grouping is allowed but must be distinct and labelled.
        if (r.get('deck_teaching_module') or '').strip() and (r.get('deck_module_is_editorial') or '').strip().lower() not in {'yes','true','1'}:
            issues.append({'severity':'MEDIUM','id':rid,'issue':'deck teaching module present but not explicitly marked editorial'})
    return {'gate':'SOURCE_SECTION_ATTRIBUTION','issues':issues,'pass':not any(x['severity'] in {'CRITICAL','HIGH'} for x in issues)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--nodes',required=True); ap.add_argument('--source-inventory',required=True); a=ap.parse_args(); r=validate(a.nodes,a.source_inventory); print(json.dumps(r,indent=2)); raise SystemExit(0 if r['pass'] else 1)
if __name__=='__main__': main()
