from __future__ import annotations
import argparse, json
from collections import Counter, defaultdict
try:
    from scripts.common import read_csv, split_ids
except ModuleNotFoundError:
    from common import read_csv, split_ids

PASS = {'pass','yes','true','1','complete','adjudicated','certified'}
NON_NODE_DISPOSITIONS={'EXPLANATORY_ONLY','NO_INDEPENDENT_DECISION','DUPLICATE_SOURCE_EXPRESSION','OTHER_EXPLICITLY_ADJUDICATED_DISPOSITION'}


def audit(source_inventory, extraction_accounting, source_rec_col='source_recommendation_id', node_col='decision_node_id'):
    src=read_csv(source_inventory); acc=read_csv(extraction_accounting)
    issues=[]; expected=[]; nondeterministic=[]
    for i,r in enumerate(src,2):
        rid=(r.get(source_rec_col) or '').strip()
        if not rid:
            issues.append({'severity':'HIGH','row':i,'issue':'source recommendation missing stable ID'}); continue
        expected.append(rid)
        enum=(r.get('enumeration_mode') or 'deterministic').strip().lower()
        if enum != 'deterministic':
            status=(r.get('completeness_adjudication_status') or '').strip().lower(); scope=(r.get('reviewed_source_scope') or '').strip(); reason=(r.get('deterministic_unavailable_reason') or '').strip()
            if status not in PASS or not scope or not reason: nondeterministic.append(rid)

    counts=Counter(); mapped_nodes=defaultdict(list); orphan_nodes=[]
    for j,r in enumerate(acc,2):
        rid=(r.get(source_rec_col) or '').strip(); node_ids=split_ids(r.get(node_col,'')); status=(r.get('accounting_status') or '').strip().upper()
        if node_ids and not rid:
            orphan_nodes.extend(node_ids)
            for nid in node_ids: issues.append({'severity':'HIGH','row':j,'decision_node_id':nid,'issue':'decision node mapped to no source recommendation'})
        if rid:
            counts[rid]+=1
        if status == 'EXTRACTED':
            if not node_ids:
                issues.append({'severity':'HIGH','row':j,'source_recommendation_id':rid,'issue':'EXTRACTED accounting row has blank decision_node_id'})
        elif status in NON_NODE_DISPOSITIONS:
            if node_ids:
                issues.append({'severity':'HIGH','row':j,'source_recommendation_id':rid,'issue':'non-node disposition must not carry decision_node_id'})
            reason=(r.get('adjudication_reason') or '').strip(); reviewer=(r.get('reviewer') or '').strip(); sem=(r.get('semantic_review_status') or '').strip().lower()
            if not reason or not reviewer or sem not in PASS:
                issues.append({'severity':'HIGH','row':j,'source_recommendation_id':rid,'issue':'non-node disposition lacks reason/reviewer/completed semantic review'})
        else:
            issues.append({'severity':'HIGH','row':j,'source_recommendation_id':rid,'issue':f'unknown or blank accounting_status: {status or "<blank>"}'})
        if rid and node_ids:
            mapped_nodes[rid].extend(node_ids)

    expected_set=set(expected); missing=sorted(rid for rid in expected_set if counts[rid] == 0)
    duplicate_accounting=sorted(rid for rid,c in counts.items() if c != 1 and rid in expected_set)
    unknown=sorted(rid for rid in counts if rid not in expected_set)
    node_to_rows=defaultdict(list)
    for rid,nodes in mapped_nodes.items():
        for nid in nodes: node_to_rows[nid].append(rid)
    duplicate_node_mapping={nid:rows for nid,rows in node_to_rows.items() if len(set(rows))>1}
    for rid in missing: issues.append({'severity':'HIGH','source_recommendation_id':rid,'issue':'source recommendation has no extraction-accounting record'})
    for rid in duplicate_accounting: issues.append({'severity':'HIGH','source_recommendation_id':rid,'issue':f'source recommendation accounting count is {counts[rid]}, expected exactly 1'})
    for rid in unknown: issues.append({'severity':'HIGH','source_recommendation_id':rid,'issue':'extraction record references unknown source recommendation'})
    for nid,rows in duplicate_node_mapping.items(): issues.append({'severity':'HIGH','decision_node_id':nid,'issue':f'decision node mapped to multiple source recommendations: {sorted(set(rows))}'})
    for rid in nondeterministic: issues.append({'severity':'HIGH','source_recommendation_id':rid,'issue':'nondeterministic source scope lacks completed semantic completeness adjudication'})
    return {
      'gate':'SOURCE_EXTRACTION_COMPLETENESS','expected_source_recommendations':len(expected_set),
      'accounted_source_recommendations':len(expected_set-set(missing)), 'missing':missing,
      'duplicate_accounting':duplicate_accounting,'unknown_source_ids':unknown,
      'duplicate_node_mapping':duplicate_node_mapping,'orphan_nodes':sorted(set(orphan_nodes)),'nondeterministic_unadjudicated':nondeterministic,
      'issues':issues,'pass':not issues
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source-inventory',required=True); ap.add_argument('--extraction-accounting',required=True); a=ap.parse_args()
    r=audit(a.source_inventory,a.extraction_accounting); print(json.dumps(r,indent=2)); raise SystemExit(0 if r['pass'] else 1)
if __name__=='__main__': main()
