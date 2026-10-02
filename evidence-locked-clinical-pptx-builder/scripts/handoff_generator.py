from __future__ import annotations
import argparse
from pathlib import Path
import yaml

def generate(state):
    s=yaml.safe_load(Path(state).read_text()) or {}; p=s.get('project',{}); lines=[f"# {p.get('title','Clinical Presentation Project')} — Handoff","",f"**Status:** {p.get('status','unknown')}",f"**Mode:** {p.get('mode','unknown')}","","## Evidence boundary"]
    for x in s.get('evidence_contract',{}).get('approved_clinical_sources',[]): lines.append(f"- {x.get('source_id',x.get('id'))}: {x.get('path')} — {x.get('role')}")
    lines += ['','## Next action',f"- {s.get('next_action')}"]
    return '\n'.join(lines)+'\n'
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('state'); ap.add_argument('--output',required=True); a=ap.parse_args(); Path(a.output).write_text(generate(a.state),encoding='utf-8')
if __name__=='__main__': main()
