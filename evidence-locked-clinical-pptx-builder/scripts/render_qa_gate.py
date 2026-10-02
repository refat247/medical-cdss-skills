from __future__ import annotations
import argparse, json, re, hashlib
from pathlib import Path
from pptx import Presentation
from PIL import Image

def _hash_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()

def _hash_slide_set(paths):
    h=hashlib.sha256()
    for p in sorted(paths, key=lambda x: x.name):
        h.update(p.name.encode('utf-8')); h.update(b'\0'); h.update(_hash_file(p).encode('ascii')); h.update(b'\n')
    return h.hexdigest()

def gate(pptx,render_dir,ledger=None,require_ledger=False,manifest_out=None):
    n=len(Presentation(pptx).slides); d=Path(render_dir); files=list(d.glob('*.png'))+list(d.glob('*.jpg'))+list(d.glob('*.jpeg'))
    nums={}
    for f in files:
        m=re.search(r'(\d+)',f.stem)
        if m: nums[int(m.group(1))]=f
    missing=[i for i in range(1,n+1) if i not in nums]
    bad_dim=[]; rendered=[]
    for i,f in sorted(nums.items()):
        if not 1<=i<=n: continue
        try:
            with Image.open(f) as im:
                if im.width<800 or im.height<450: bad_dim.append({'slide':i,'size':im.size})
                rendered.append({'slide':i,'file':str(f),'width':im.width,'height':im.height,'sha256':_hash_file(f)})
        except Exception:
            bad_dim.append({'slide':i,'size':'unreadable'})
    slide_set_hash=_hash_slide_set([Path(x['file']) for x in rendered]) if rendered else None
    result={'slides':n,'rendered_unique':len(rendered),'missing':missing,'low_or_bad_dimensions':bad_dim,'rendered_slide_set_sha256':slide_set_hash,'pass':not missing and not bad_dim}
    if manifest_out:
        Path(manifest_out).write_text(json.dumps({'pptx':str(pptx),'slides':n,'rendered_slide_set_sha256':slide_set_hash,'slides_rendered':rendered},indent=2),encoding='utf-8')
    if ledger:
        try:
            from scripts.visual_review_ledger import validate_ledger
        except ModuleNotFoundError:
            from visual_review_ledger import validate_ledger
        lr=validate_ledger(ledger,n,require_final_pass=True,require_domain_columns=True)
        result['ledger']=lr; result['pass']=result['pass'] and lr['pass']
    elif require_ledger:
        result['ledger']={'pass':False,'status':'RENDER-UNCERTIFIED','issues':['no per-slide visual review ledger supplied']}
        result['pass']=False
    return result

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('pptx'); ap.add_argument('render_dir'); ap.add_argument('--ledger'); ap.add_argument('--require-ledger',action='store_true'); ap.add_argument('--manifest-out')
    a=ap.parse_args(); r=gate(a.pptx,a.render_dir,a.ledger,a.require_ledger,a.manifest_out); print(json.dumps(r,indent=2)); raise SystemExit(1 if not r['pass'] else 0)
if __name__=='__main__': main()
