from __future__ import annotations
import argparse, csv, re
from pathlib import Path

def split_md(line): return [p.strip().replace('\\|','|') for p in re.split(r'(?<!\\)\|',line.strip().strip('|'))]
def parse_map(path):
    lines=Path(path).read_text(encoding='utf-8',errors='ignore').splitlines(); header=None; rows=[]
    for line in lines:
        if line.startswith('| ') and 'Slide' in line.split('|')[1]: header=split_md(line)
        elif header and line.startswith('| ') and not line.startswith('|---') and not line.startswith('| ---'):
            parts=split_md(line)
            if len(parts)==len(header): rows.append(dict(zip(header,parts)))
    return rows
def no(v):
    if str(v).isdigit(): return int(v)
    m=re.search(r'(\d+)$',str(v)); return int(m.group(1)) if m else None
def build(specs,case_regex=r'[A-Z]+-CASE-\d+'):
    slides=[]; occ=[]; cre=re.compile(case_regex)
    for deck_id,product,pptx,map_path in specs:
        for r in parse_map(map_path):
            first=next(iter(r)); n=no(r[first]);
            if n is None: continue
            cases=r.get('Included Case ID(s)',r.get('Case ID(s)',r.get('Cases','—'))); cids=sorted(set(cre.findall(cases or '')))
            slides.append({'deck_id':deck_id,'product':product,'canonical_filename':pptx,'slide':n,'case_ids':', '.join(cids) if cids else '—'})
            for c in cids: occ.append({'case_id':c,'deck_id':deck_id,'product':product,'slide':n})
    return slides,occ
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source-map',action='append',required=True,help='DECK|PRODUCT|PPTX|MAP'); ap.add_argument('--slides-out',required=True); ap.add_argument('--cases-out',required=True); ap.add_argument('--case-regex',default=r'[A-Z]+-CASE-\d+'); a=ap.parse_args(); specs=[x.split('|',3) for x in a.source_map]; slides,occ=build(specs,a.case_regex)
    for path,rows in [(a.slides_out,slides),(a.cases_out,occ)]:
        with open(path,'w',newline='',encoding='utf-8') as f:
            fields=list(rows[0]) if rows else []; w=csv.DictWriter(f,fieldnames=fields); w.writeheader() if fields else None; w.writerows(rows)
    print({'slides':len(slides),'case_occurrences':len(occ)})
if __name__=='__main__': main()
