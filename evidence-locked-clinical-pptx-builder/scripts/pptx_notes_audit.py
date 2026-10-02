from __future__ import annotations
import argparse, json, re, zipfile
from pathlib import PurePosixPath
from xml.etree import ElementTree as ET
REL_NS='http://schemas.openxmlformats.org/package/2006/relationships'; A_NS='http://schemas.openxmlformats.org/drawingml/2006/main'
def resolve(base,target):
    p=PurePosixPath(base).parent/target; parts=[]
    for x in p.parts:
        if x=='..':
            if parts: parts.pop()
        elif x!='.': parts.append(x)
    return '/'.join(parts)
def text(zf,path):
    root=ET.fromstring(zf.read(path)); return ' '.join((n.text or '').strip() for n in root.findall(f'.//{{{A_NS}}}t') if (n.text or '').strip()).strip()
def audit(path):
    missing=[]; empty=[]
    with zipfile.ZipFile(path) as zf:
        names=set(zf.namelist()); slides=sorted([x for x in names if re.fullmatch(r'ppt/slides/slide\d+\.xml',x)],key=lambda x:int(re.search(r'(\d+)',x).group(1)))
        for slide in slides:
            n=int(re.search(r'slide(\d+)\.xml',slide).group(1)); rel=f'ppt/slides/_rels/slide{n}.xml.rels'
            if rel not in names: missing.append(n); continue
            rr=ET.fromstring(zf.read(rel)); target=None
            for x in rr.findall(f'{{{REL_NS}}}Relationship'):
                if x.attrib.get('Type','').endswith('/notesSlide'): target=x.attrib.get('Target'); break
            if not target: missing.append(n); continue
            np=resolve(slide,target)
            if np not in names: missing.append(n); continue
            if not re.search(r'[A-Za-zÀ-ÿΑ-ωА-я一-龯অ-হ]',text(zf,np)): empty.append(n)
    return {'slides':len(slides),'missing_notes':missing,'empty_notes':empty,'pass':not missing and not empty}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('pptx'); a=ap.parse_args(); r=audit(a.pptx); print(json.dumps(r,indent=2)); raise SystemExit(1 if not r['pass'] else 0)
if __name__=='__main__': main()
