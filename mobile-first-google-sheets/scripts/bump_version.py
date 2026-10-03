#!/usr/bin/env python3
import argparse, pathlib, re, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
FILES=[
    ROOT/'SKILL.md', ROOT/'README.md', ROOT/'CHANGELOG.md',
    ROOT/'MANUAL_ACTIVATION.md', ROOT/'ACTIVATION_SMOKE_TEST.md',
    ROOT/'agents'/'openai.yaml', ROOT/'PACKAGE_MANIFEST.json'
]
SEMVER=re.compile(r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$')

def versions():
    out={}
    s=(ROOT/'SKILL.md').read_text()
    out['SKILL.md']=re.search(r'^version:\s*([^\s]+)',s,re.M).group(1)
    a=(ROOT/'agents'/'openai.yaml').read_text()
    out['agents/openai.yaml']=re.search(r'^version:\s*([^\s]+)',a,re.M).group(1)
    r=(ROOT/'README.md').read_text()
    out['README.md']=re.search(r'v(\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?)',r).group(1)
    c=(ROOT/'CHANGELOG.md').read_text()
    out['CHANGELOG.md']=re.search(r'^## \[([^\]]+)\]',c,re.M).group(1)
    m=(ROOT/'MANUAL_ACTIVATION.md').read_text()
    out['MANUAL_ACTIVATION.md']=re.search(r'v(\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?)',m).group(1)
    t=(ROOT/'ACTIVATION_SMOKE_TEST.md').read_text()
    out['ACTIVATION_SMOKE_TEST.md']=re.search(r'- version:\s*(\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?)',t).group(1)
    import json
    j=json.loads((ROOT/'PACKAGE_MANIFEST.json').read_text())
    out['PACKAGE_MANIFEST.json']=j['version']
    return out

def verify():
    v=versions(); vals=set(v.values())
    ok=len(vals)==1 and all(SEMVER.match(x) for x in vals)
    print('\n'.join(f'{k}: {x}' for k,x in v.items()))
    print('ZERO VERSION DRIFT: PASS' if ok else 'ZERO VERSION DRIFT: FAIL')
    return 0 if ok else 1

p=argparse.ArgumentParser(); p.add_argument('--verify',action='store_true'); args=p.parse_args()
sys.exit(verify())