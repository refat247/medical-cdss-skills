from __future__ import annotations
import argparse, json
from pathlib import Path
import yaml
try:
    from scripts.state_manager import validate
except ModuleNotFoundError:
    from state_manager import validate

VALID_MODES={'INSPECT','PATCH','BUILD_STANDARD','BUILD_CASE_BASED','CORPUS_BUILD','DERIVATIVE_BUILD','VISUAL_QA','VISUAL_POLISH','FINAL_RELEASE','MAINTENANCE'}
VALID_INDEPENDENT_QA_POLICIES={'required','required_unless_explicit_user_waiver','optional'}
def validate_project(path):
    s=yaml.safe_load(Path(path).read_text()) or {}; errs=validate(s); p=s.get('project',{}); e=s.get('evidence_contract',{}); rp=s.get('release_policy',{})
    if not p.get('id'): errs.append('project.id missing')
    if p.get('mode') not in VALID_MODES: errs.append('invalid project.mode')
    if e.get('locked') and not e.get('approved_clinical_sources'): errs.append('evidence locked but no approved sources')
    if rp.get('require_visual_review_100_percent') and rp.get('contact_sheet_certifies_slides'): errs.append('contact sheet cannot certify slides')
    policy=rp.get('independent_visual_qa_policy')
    if policy not in VALID_INDEPENDENT_QA_POLICIES: errs.append('release_policy.independent_visual_qa_policy missing or invalid')
    vp=rp.get('visual_polish') or {}
    if vp.get('enabled'):
        try:
            from scripts.visual_polish.style import PROFILES
        except ModuleNotFoundError:
            from visual_polish.style import PROFILES
        prof=vp.get('profile','projector_default')
        if prof not in PROFILES: errs.append(f'release_policy.visual_polish.profile invalid: {prof}')
        elif PROFILES[prof]['requires_approval'] and not str(vp.get('profile_approved_by','')).strip():
            errs.append(f'visual_polish profile {prof} lowers body floors and requires profile_approved_by')
        if vp.get('content_lock_required_when_enabled') is False:
            errs.append('visual_polish content lock cannot be disabled')
    return errs

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('state'); a=ap.parse_args(); errs=validate_project(a.state); print(json.dumps({'valid':not errs,'errors':errs},indent=2)); raise SystemExit(1 if errs else 0)
if __name__=='__main__': main()
