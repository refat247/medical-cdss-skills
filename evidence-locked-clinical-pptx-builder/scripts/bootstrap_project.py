from __future__ import annotations
import argparse, shutil
from datetime import datetime, timezone
from pathlib import Path
import yaml

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--project-dir',required=True); ap.add_argument('--project-id',required=True); ap.add_argument('--title',required=True); ap.add_argument('--mode',default='BUILD_CASE_BASED'); ap.add_argument('--source',action='append',default=[],help='PATH::ROLE')
    a=ap.parse_args(); root=Path(__file__).resolve().parents[1]; out=Path(a.project_dir); out.mkdir(parents=True,exist_ok=True)
    for d in ['01_control','02_extraction','03_reconciliation','04_cases','05_architecture','06_spec','07_builds','08_audits','09_canonical','10_indexes','11_closure']: (out/d).mkdir(exist_ok=True)
    s=yaml.safe_load((root/'templates/project_state.yaml').read_text()); now=datetime.now(timezone.utc).isoformat(); s['project'].update({'id':a.project_id,'title':a.title,'mode':a.mode,'created_at':now,'updated_at':now})
    src=[]
    for i,x in enumerate(a.source,1):
        if '::' not in x: raise SystemExit('--source PATH::ROLE')
        p,r=x.split('::',1); src.append({'source_id':f'SRC-{i:02d}','path':p,'role':r,'source_type':'CLINICAL','status':'approved'})
    s['evidence_contract']['approved_clinical_sources']=src; s['evidence_contract']['locked']=bool(src)
    (out/'project_state.yaml').write_text(yaml.safe_dump(s,sort_keys=False,allow_unicode=True),encoding='utf-8')
    lock=yaml.safe_load((root/'templates/evidence_lock.yaml').read_text()); lock['project_id']=a.project_id; lock['approved_clinical_sources']=src; (out/'01_control/evidence_lock.yaml').write_text(yaml.safe_dump(lock,sort_keys=False,allow_unicode=True),encoding='utf-8')
    shutil.copy2(root/'templates/handoff.md',out/'01_control/project_handoff.md'); print(out/'project_state.yaml')
if __name__=='__main__': main()
