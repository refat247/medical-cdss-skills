from __future__ import annotations
import argparse, json
from collections import Counter
try:
    from scripts.common import read_csv
except ModuleNotFoundError:
    from common import read_csv

PASS={'pass','yes','true','1','certified','adjudicated','verified'}
YES={'yes','true','1','pass'}
DETERMINISTIC={'deterministic','structured_table_enumeration','machine_enumeration'}
SEMANTIC={'semantic_manual','manual_semantic','human_semantic','manual'}


def _ival(v):
    try: return int(str(v or '0').strip())
    except ValueError: return None


def certify(census_csv, source_inventory_csv):
    census=read_csv(census_csv); inv=read_csv(source_inventory_csv); issues=[]
    inventory_ids=[]
    for i,r in enumerate(inv,2):
        rid=(r.get('source_recommendation_id') or '').strip()
        if not rid:
            issues.append({'severity':'HIGH','row':i,'issue':'source inventory row missing source_recommendation_id'})
        else:
            inventory_ids.append(rid)
    dup=[rid for rid,c in Counter(inventory_ids).items() if c>1]
    for rid in dup:
        issues.append({'severity':'HIGH','source_recommendation_id':rid,'issue':'duplicate source inventory recommendation ID'})

    inv_counts=Counter()
    for r in inv:
        sid=(r.get('source_id') or '').strip()
        section=(r.get('source_section_id') or '').strip()
        table=(r.get('recommendation_table_id') or '').strip()
        inv_counts[(sid,section,table)] += 1

    seen=set(); expected_total=0; matched_total=0
    census_rows=[]
    for i,r in enumerate(census,2):
        sid=(r.get('source_id') or '').strip(); section=(r.get('source_section_id') or '').strip(); table=(r.get('recommendation_table_id') or '').strip()
        key=(sid,section,table)
        if not sid:
            issues.append({'severity':'HIGH','row':i,'issue':'census row missing source_id'}); continue
        if key in seen:
            issues.append({'severity':'HIGH','row':i,'source_id':sid,'recommendation_table_id':table,'issue':'duplicate census source/table row'})
            continue
        seen.add(key)
        rows=_ival(r.get('expected_recommendation_row_count'))
        narrative=_ival(r.get('standalone_narrative_recommendation_count'))
        if rows is None or narrative is None or rows < 0 or narrative < 0:
            issues.append({'severity':'HIGH','row':i,'issue':'invalid expected recommendation count(s)'})
            continue
        expected=rows+narrative
        actual=inv_counts.get(key,0)
        expected_total += expected
        matched_total += min(expected,actual)
        method=(r.get('enumeration_method') or '').strip().lower()
        cert=(r.get('certification_status') or '').strip().lower()
        reviewer=(r.get('reviewer') or '').strip()
        independent=(r.get('independent_from_inventory_generation') or '').strip().lower()
        semantic=(r.get('semantic_review_status') or '').strip().lower()
        reason=(r.get('deterministic_unavailable_reason') or '').strip()
        if cert not in PASS:
            issues.append({'severity':'HIGH','row':i,'issue':'source census certification unresolved'})
        if independent not in YES:
            issues.append({'severity':'HIGH','row':i,'issue':'source census is not attested independent from inventory generation pathway'})
        if not reviewer:
            issues.append({'severity':'HIGH','row':i,'issue':'source census reviewer missing'})
        if method not in DETERMINISTIC|SEMANTIC:
            issues.append({'severity':'HIGH','row':i,'issue':f'unsupported/blank enumeration_method: {method or "<blank>"}'})
        if method in SEMANTIC and (semantic not in PASS or not reason):
            issues.append({'severity':'HIGH','row':i,'issue':'manual/semantic census lacks completed semantic review and deterministic-unavailable reason'})
        if expected != actual:
            issues.append({'severity':'HIGH','row':i,'source_id':sid,'recommendation_table_id':table,'issue':f'source census expects {expected} recommendation(s), inventory contains {actual}'})
        census_rows.append({'source_id':sid,'source_section_id':section,'recommendation_table_id':table,'expected':expected,'inventory':actual})

    uncensused=[]
    for key,count in inv_counts.items():
        if key not in seen:
            uncensused.append({'source_id':key[0],'source_section_id':key[1],'recommendation_table_id':key[2],'inventory_count':count})
            issues.append({'severity':'HIGH','source_id':key[0],'source_section_id':key[1],'recommendation_table_id':key[2],'issue':'source inventory row(s) have no corresponding independently certified census scope'})

    return {
        'gate':'SOURCE_INVENTORY_CERTIFICATION',
        'census_expected_recommendations':expected_total,
        'inventory_recommendations':len(inventory_ids),
        'census_rows':census_rows,
        'uncensused_inventory_scopes':uncensused,
        'issues':issues,
        'pass':not issues,
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source-census',required=True); ap.add_argument('--source-inventory',required=True); a=ap.parse_args()
    r=certify(a.source_census,a.source_inventory); print(json.dumps(r,indent=2)); raise SystemExit(0 if r['pass'] else 1)
if __name__=='__main__': main()
