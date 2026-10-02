from __future__ import annotations
import argparse, json
from pathlib import Path
import yaml
try:
    from scripts.common import sha256
except ModuleNotFoundError:
    from common import sha256

ALLOWED_CONTEXT={'OPERATIONAL_CONTEXT','STYLE_REFERENCE','OFFICIAL_SOURCE_FIGURE','USER_CLINICAL_IMAGE','EXTERNAL_ILLUSTRATIVE_VISUAL','MODEL_GENERATED_DECORATIVE'}
def validate_lock(path, check_files=False):
    d=yaml.safe_load(Path(path).read_text()) or {}; issues=[]; ids=set()
    if not d.get('locked'): issues.append('evidence lock is not locked')
    for s in d.get('approved_clinical_sources',[]):
        sid=s.get('source_id') or s.get('id')
        if not sid or sid in ids: issues.append(f'invalid/duplicate source id: {sid}')
        ids.add(sid)
        if not s.get('path') or not s.get('role'): issues.append(f'{sid}: missing path/role')
        if check_files and s.get('path') and not Path(s['path']).exists(): issues.append(f'{sid}: missing file {s["path"]}')
        if check_files and s.get('sha256') and Path(s['path']).exists() and sha256(s['path'])!=s['sha256']: issues.append(f'{sid}: sha256 mismatch')
    for c in d.get('context_sources',[]):
        if c.get('class') not in ALLOWED_CONTEXT: issues.append(f"invalid context class: {c.get('class')}")
    return issues

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('lock'); ap.add_argument('--check-files',action='store_true'); a=ap.parse_args(); issues=validate_lock(a.lock,a.check_files); print(json.dumps({'pass':not issues,'issues':issues},indent=2)); raise SystemExit(1 if issues else 0)
if __name__=='__main__': main()
