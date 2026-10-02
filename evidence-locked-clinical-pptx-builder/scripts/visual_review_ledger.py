from __future__ import annotations
import argparse, json
try:
    from scripts.common import read_csv
except ModuleNotFoundError:
    from common import read_csv

VALID={'PASS','PASS_WITH_WARNINGS','REPAIR','FAIL','RENDER-UNCERTIFIED','INDEPENDENT-QA-UNCERTIFIED'}
PASSLIKE={'PASS','PASS_WITH_WARNINGS'}
DOMAIN_COLUMNS=[
    'projector_readability','title_hierarchy','body_text_size','source_footer_readability',
    'clipping_overflow','overlap_alignment_spacing','image_ecg_chart_legibility',
    'density_whitespace','case_reveal_rhythm','local_constraint_separation'
]

def validate_ledger(path,slide_count,require_final_pass=False,require_domain_columns=False,allow_warnings=True):
    rows=read_csv(path); issues=[]; seen={}
    if require_domain_columns and rows:
        missing_cols=[c for c in DOMAIN_COLUMNS if c not in rows[0]]
        if missing_cols: issues.append({'issue':'missing required visual-domain columns','columns':missing_cols})
    for i,r in enumerate(rows,2):
        try: s=int(r.get('slide',''))
        except Exception:
            issues.append({'row':i,'issue':'invalid slide number'}); continue
        if s < 1 or s > slide_count:
            issues.append({'row':i,'slide':s,'issue':f'slide out of range 1..{slide_count}'})
        if s in seen:
            issues.append({'row':i,'slide':s,'issue':'duplicate slide row'})
        status=(r.get('final_status') or r.get('status') or '').strip().upper()
        if status not in VALID: issues.append({'row':i,'slide':s,'issue':f'invalid status {status}'})
        if not r.get('reviewer','').strip(): issues.append({'row':i,'slide':s,'issue':'missing reviewer'})
        if require_domain_columns:
            blank=[c for c in DOMAIN_COLUMNS if not str(r.get(c,'')).strip()]
            if blank: issues.append({'row':i,'slide':s,'issue':'blank visual-domain cells','columns':blank})
        seen[s]=status
    missing=[s for s in range(1,slide_count+1) if s not in seen]
    if missing: issues.append({'issue':'slides not individually reviewed','slides':missing})
    if require_final_pass:
        ok=PASSLIKE if allow_warnings else {'PASS'}
        nonpass=[s for s,st in seen.items() if st not in ok]
        if nonpass: issues.append({'issue':'final review not PASS/PASS_WITH_WARNINGS for all slides','slides':sorted(nonpass)})
    return {'rows':len(rows),'slide_count':slide_count,'issues':issues,'pass':not issues}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('ledger')
    ap.add_argument('--slides',type=int,required=True)
    ap.add_argument('--require-final-pass',action='store_true')
    ap.add_argument('--require-domain-columns',action='store_true')
    ap.add_argument('--strict-pass-only',action='store_true')
    a=ap.parse_args()
    r=validate_ledger(a.ledger,a.slides,a.require_final_pass,a.require_domain_columns,not a.strict_pass_only)
    print(json.dumps(r,indent=2))
    raise SystemExit(1 if not r['pass'] else 0)
if __name__=='__main__': main()
