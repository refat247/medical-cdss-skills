from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path
import yaml

ALLOWED={'pending','in_progress','blocked','fail','pass','frozen','built','audited','canonical','complete','waived','closed','render_uncertified'}
DONE={'pass','frozen','built','audited','canonical','complete','waived','closed'}
HARD={'blocked','fail','render_uncertified'}

def load(path): return yaml.safe_load(Path(path).read_text(encoding='utf-8')) or {}
def save(path,state):
    state.setdefault('project',{})['updated_at']=datetime.now(timezone.utc).isoformat()
    Path(path).write_text(yaml.safe_dump(state,sort_keys=False,allow_unicode=True),encoding='utf-8')

def all_states(state):
    out=[]
    for pipe in state.get('pipelines',{}).values(): out.extend(pipe.get('states',[]))
    return out

def mapping(state): return {x['id']:x for x in all_states(state)}
def validate(state):
    errs=[]; ids=[]
    for x in all_states(state):
        ids.append(x.get('id'))
        if x.get('status') not in ALLOWED: errs.append(f"{x.get('id')}: invalid status {x.get('status')}")
    if len(ids)!=len(set(ids)): errs.append('duplicate state ids')
    m=mapping(state)
    for x in all_states(state):
        for d in x.get('depends_on',[]):
            if d not in m: errs.append(f"{x['id']}: missing dependency {d}")
    return errs

def next_state(state):
    m=mapping(state)
    for x in all_states(state):
        if x.get('status') in HARD: return {'hard_stop':True,**x}
    for x in all_states(state):
        if x.get('status') in DONE: continue
        if all(m[d].get('status') in DONE for d in x.get('depends_on',[])): return x
    return None

def mark(state,item_id,status,note=None):
    m=mapping(state)
    if item_id not in m: raise KeyError(item_id)
    if status not in ALLOWED: raise ValueError(status)
    m[item_id]['status']=status
    state.setdefault('history',[]).append({'at':datetime.now(timezone.utc).isoformat(),'item':item_id,'status':status,'note':note})
    nxt=next_state(state); state['next_action']=None if nxt is None else nxt.get('id')
    return state

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('state'); sub=ap.add_subparsers(dest='cmd',required=True)
    sub.add_parser('status'); sub.add_parser('next'); p=sub.add_parser('mark'); p.add_argument('id'); p.add_argument('status'); p.add_argument('--note')
    a=ap.parse_args(); s=load(a.state); errs=validate(s)
    if errs: raise SystemExit('INVALID STATE: '+'; '.join(errs))
    if a.cmd=='mark': mark(s,a.id,a.status,a.note); save(a.state,s)
    print(json.dumps({'errors':errs,'next':next_state(s),'mode':s.get('project',{}).get('mode')},indent=2))
if __name__=='__main__': main()
