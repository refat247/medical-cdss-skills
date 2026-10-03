from __future__ import annotations
import argparse, json, re

MODES=['INSPECT','PATCH','BUILD_STANDARD','BUILD_CASE_BASED','CORPUS_BUILD','DERIVATIVE_BUILD','VISUAL_QA','VISUAL_POLISH','FINAL_RELEASE','MAINTENANCE']

def route(text:str, project_status='active'):
    t=text.lower()
    if project_status=='closed':
        return {'mode':'MAINTENANCE','reason':'project is closed; new request must be classified as maintenance'}
    rules=[
        ('FINAL_RELEASE', r'canonical|final release|promot'),
        ('VISUAL_POLISH', r'beauti|polish|restyle|improve (the )?(visual|look|design)|visual repair|make (it|the deck) look'),
        ('VISUAL_QA', r'visual qa|projector|render.*audit|visual review'),
        ('DERIVATIVE_BUILD', r'derivative|30.?min|45.?min|60.?min|90.?min|audience-specific|local-resource'),
        ('CORPUS_BUILD', r'master case library|case corpus|decision node|exhaustive.*cases'),
        ('BUILD_CASE_BASED', r'case[- ]based|case based'),
        ('PATCH', r'patch|repair|fix|correct this deck'),
        ('INSPECT', r'audit|inspect|review|check'),
        ('BUILD_STANDARD', r'build|create|presentation|pptx|slides'),
    ]
    for mode,pat in rules:
        if re.search(pat,t): return {'mode':mode,'reason':f'intent matched {pat}'}
    return {'mode':'INSPECT','reason':'no build/edit intent detected; safest default is read-only inspect'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('text'); ap.add_argument('--project-status',default='active')
    a=ap.parse_args(); print(json.dumps(route(a.text,a.project_status),indent=2))
if __name__=='__main__': main()
