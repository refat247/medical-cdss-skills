from __future__ import annotations
import argparse, zipfile, fnmatch
from pathlib import Path
try:
    from scripts.common import sha256
except ModuleNotFoundError:
    from common import sha256

HYGIENE_DIRS={'.pytest_cache','__pycache__'}
HYGIENE_GLOBS=('*.pyc','*.pyo')


def is_runtime_artifact(rel):
    p=Path(rel)
    if any(part in HYGIENE_DIRS for part in p.parts): return True
    return any(fnmatch.fnmatch(p.name,pat) for pat in HYGIENE_GLOBS)


def create(root,out,exclude=()):
    root=Path(root).resolve(); out=Path(out).resolve(); ex={str(x).replace('\\','/') for x in exclude}
    files=[]
    for p in sorted(root.rglob('*')):
        if not p.is_file() or p.resolve()==out: continue
        rel=p.relative_to(root).as_posix()
        if rel in ex or is_runtime_artifact(rel): continue
        files.append((p,rel))
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for p,rel in files: z.write(p,rel)
    with zipfile.ZipFile(out) as z:
        names=z.namelist(); bad=z.testzip()
        if bad: raise RuntimeError(f'bad zip part {bad}')
        if len(names)!=len(set(names)): raise RuntimeError('duplicate entries')
        dirty=[n for n in names if is_runtime_artifact(n)]
        if dirty: raise RuntimeError(f'runtime/cache artifacts included: {dirty}')
    return {'entries':len(names),'bytes':out.stat().st_size,'sha256':sha256(out),'runtime_artifacts':0}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('output'); ap.add_argument('--exclude',action='append',default=[]); a=ap.parse_args(); print(create(a.root,a.output,a.exclude))
if __name__=='__main__': main()
