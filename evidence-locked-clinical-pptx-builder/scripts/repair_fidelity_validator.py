from __future__ import annotations
import argparse, json
try:
    from scripts.common import read_csv
except ModuleNotFoundError:
    from common import read_csv

CLINICAL_CHANGE_TYPES={'clinical_terminology','population_criteria','threshold','unit','cor','loe','source_wording','dose','frequency','negation','contraindication','recommendation_polarity'}
UNSUPPORTED_EDITORIAL={'audience_tier','source_section_as_deck_module','table_relocation','figure_relocation','footnote_reassignment'}
PASS={'pass','yes','true','1','adjudicated','certified','verified'}
YES={'yes','true','1','pass'}


def _valid_approved_source_support(r):
    support=(r.get('source_support') or '').strip()
    support_status=(r.get('source_support_status') or '').strip().lower()
    approved=(r.get('source_is_approved') or '').strip().lower()
    lock=(r.get('source_lock_status') or '').strip().lower()
    return bool(support) and support_status in PASS and approved in YES and lock in {'locked','pass','certified','verified'}


def validate(path):
    issues=[]
    for i,r in enumerate(read_csv(path),2):
        rid=(r.get('repair_id') or f'row-{i}').strip(); ctype=(r.get('change_type') or '').strip().lower(); source=(r.get('source_support') or '').strip(); user=(r.get('user_authority') or '').strip()
        clinical=(r.get('clinical_content_changed') or '').strip().lower() in YES
        wording=(r.get('source_wording_changed') or '').strip().lower() in YES
        clinical_change=clinical or ctype in CLINICAL_CHANGE_TYPES or wording
        if clinical_change and not _valid_approved_source_support(r):
            issues.append({'severity':'CRITICAL','id':rid,'issue':'clinical/source wording change lacks validated support from a currently approved locked source'})
        if ctype in UNSUPPORTED_EDITORIAL and not user and not source:
            issues.append({'severity':'HIGH','id':rid,'issue':f'editorial relocation/tier change lacks authority: {ctype}'})
        if ctype=='footnote_reassignment' and not (r.get('binding_evidence') or '').strip():
            issues.append({'severity':'CRITICAL','id':rid,'issue':'footnote reassignment lacks marker/scope binding evidence'})
        if ctype in {'table_relocation','figure_relocation'} and not (r.get('source_object_link') or '').strip():
            issues.append({'severity':'HIGH','id':rid,'issue':'source object relocated without source link'})
        if (r.get('adjudication') or '').strip().lower() not in PASS:
            issues.append({'severity':'HIGH','id':rid,'issue':'repair adjudication unresolved'})
        if (r.get('post_repair_validation') or '').strip().lower() not in PASS:
            issues.append({'severity':'HIGH','id':rid,'issue':'post-repair validation unresolved'})
    return {'gate':'REPAIR_FIDELITY','issues':issues,'pass':not issues}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('csv'); a=ap.parse_args(); r=validate(a.csv); print(json.dumps(r,indent=2)); raise SystemExit(0 if r['pass'] else 1)
if __name__=='__main__': main()
