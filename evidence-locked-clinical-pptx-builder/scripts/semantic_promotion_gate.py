from __future__ import annotations
import argparse, json
try:
    from scripts.common import read_csv
except ModuleNotFoundError:
    from common import read_csv

# Fail-closed rule: every unresolved CRITICAL/HIGH defect blocks promotion by default.
# A future nonblocking exception must be explicitly documented here; keep empty unless
# governance deliberately introduces one.
NONBLOCKING_CRITICAL_HIGH_FAMILIES = set()

REQUIRED_GATES=[
    'source_lock',
    'source_inventory_certification',
    'source_extraction_completeness',
    'downstream_node_coverage',
    'source_boundary_integrity',
    'footnote_binding',
    'source_section_attribution',
    'prompt_semantics',
    'normalization_fidelity',
    'repair_fidelity',
    'correction_erratum_reconciliation',
    'case_fidelity',
    'slide_provenance',
    'speaker_notes_fidelity',
    'mechanical_preflight',
    'render_qa_100_percent',
    'independent_visual_qa',
    'canonical_hash_immutability',
]
NON_INDEPENDENT_REQUIRED_GATES=[g for g in REQUIRED_GATES if g != 'independent_visual_qa']
GOOD={'PASS','CERTIFIED'}


def _normalize_iq_status(value):
    status=str(value or '').strip().upper()
    return {'INDEPENDENT_QA_CERTIFIED':'CERTIFIED','INDEPENDENT_QA_WAIVED':'WAIVED'}.get(status,status)

def _independent_qa_waiver_is_valid(gates):
    policy=str(gates.get('independent_visual_qa_policy','')).strip().lower()
    status=_normalize_iq_status(gates.get('independent_visual_qa',''))
    waiver_reason=str(gates.get('independent_visual_qa_waiver_reason','')).strip()
    waiver_explicit=str(gates.get('independent_visual_qa_waiver_explicit','')).strip().lower() in {'yes','true','1','pass'}
    return (
        status == 'WAIVED'
        and policy == 'required_unless_explicit_user_waiver'
        and bool(waiver_reason)
        and waiver_explicit
    )


def evaluate(defects_csv, gates_json):
    defects=read_csv(defects_csv); unresolved=[]; counts={'CRITICAL':0,'HIGH':0,'MEDIUM':0,'LOW':0}
    for r in defects:
        if (r.get('status') or 'OPEN').strip().upper() in {'RESOLVED','CLOSED','PASS'}:
            continue
        sev=(r.get('severity') or '').strip().upper(); fam=(r.get('defect_family') or '').strip().lower()
        if sev in counts:
            counts[sev]+=1
        if sev in {'CRITICAL','HIGH'} and fam not in NONBLOCKING_CRITICAL_HIGH_FAMILIES:
            unresolved.append(r)

    gates=json.loads(open(gates_json,encoding='utf-8').read())
    missing=[]; failed=[]
    for g in NON_INDEPENDENT_REQUIRED_GATES:
        status=str(gates.get(g,'NOT_RUN')).strip().upper()
        if status in {'NOT_RUN','MISSING','PENDING',''}:
            missing.append(g)
        elif status not in GOOD:
            failed.append(g)

    # v2.4.0: a deck that went through VISUAL_POLISH must also pass the polish
    # content-lock gate. Declared via gates['visual_polish_applied']; never waivable.
    if str(gates.get('visual_polish_applied','')).strip().lower() in {'yes','true','1'}:
        status=str(gates.get('visual_polish_content_lock','NOT_RUN')).strip().upper()
        if status in {'NOT_RUN','MISSING','PENDING',''}:
            missing.append('visual_polish_content_lock')
        elif status not in GOOD:
            failed.append('visual_polish_content_lock')

    iq_status=_normalize_iq_status(gates.get('independent_visual_qa','NOT_RUN'))
    iq_waived=_independent_qa_waiver_is_valid(gates)
    if iq_status in {'NOT_RUN','MISSING','PENDING',''}:
        missing.append('independent_visual_qa')
    elif iq_status not in GOOD and not iq_waived:
        failed.append('independent_visual_qa')

    semantic_block=bool(unresolved)
    if semantic_block:
        outcome='REPAIR_REQUIRED'
    elif missing or failed:
        if 'render_qa_100_percent' in missing or 'render_qa_100_percent' in failed:
            outcome='RENDER-UNCERTIFIED'
        elif 'independent_visual_qa' in missing or 'independent_visual_qa' in failed:
            outcome='INDEPENDENT-QA-UNCERTIFIED'
        else:
            outcome='SEMANTIC-AUDIT-UNCERTIFIED'
    else:
        outcome='CANONICAL_WITH_EXPLICIT_INDEPENDENT_QA_WAIVER' if iq_waived else 'FULLY_CERTIFIED_CANONICAL'

    return {
        'unresolved_defect_count_by_severity':counts,
        'blocking_defects':unresolved,
        'missing_gates':missing,
        'failed_gates':failed,
        'independent_visual_qa_waiver_valid':iq_waived,
        'promotion_outcome':outcome,
        'pass':outcome in {'FULLY_CERTIFIED_CANONICAL','CANONICAL_WITH_EXPLICIT_INDEPENDENT_QA_WAIVER'}
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--defects',required=True); ap.add_argument('--gates',required=True); a=ap.parse_args(); r=evaluate(a.defects,a.gates); print(json.dumps(r,indent=2)); raise SystemExit(0 if r['pass'] else 1)
if __name__=='__main__': main()
