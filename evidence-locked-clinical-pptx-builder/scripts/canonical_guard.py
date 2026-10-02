from __future__ import annotations
import argparse, json
from pathlib import Path
try:
    from scripts.common import sha256
except ModuleNotFoundError:
    from common import sha256

def snapshot(paths): return {str(Path(p)):sha256(p) for p in paths}
def verify(path):
    exp=json.loads(Path(path).read_text()); mm=[]
    for p,h in exp.items():
        if not Path(p).exists(): mm.append({'file':p,'issue':'missing'})
        elif sha256(p)!=h: mm.append({'file':p,'expected':h,'actual':sha256(p)})
    return {'pass':not mm,'mismatches':mm}
def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True); s=sub.add_parser('snapshot'); s.add_argument('--output',required=True); s.add_argument('files',nargs='+'); v=sub.add_parser('verify'); v.add_argument('snapshot'); a=ap.parse_args()
    if a.cmd=='snapshot': d=snapshot(a.files); Path(a.output).write_text(json.dumps(d,indent=2)); print(json.dumps(d,indent=2))
    else: r=verify(a.snapshot); print(json.dumps(r,indent=2)); raise SystemExit(1 if not r['pass'] else 0)
if __name__=='__main__': main()
