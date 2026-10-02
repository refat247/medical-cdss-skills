from __future__ import annotations
import argparse, json
try:
    from scripts.common import read_csv, split_ids
except ModuleNotFoundError:
    from common import read_csv, split_ids

PASS={'pass','yes','true','1','adjudicated','certified'}
YES={'yes','true','1'}
BROADER_SCOPES={'table','section','document'}


def _validate_new(rows):
    issues=[]
    seen=set()
    for i,r in enumerate(rows,2):
        rid=(r.get('recommendation_id') or '').strip(); fid=(r.get('footnote_id') or '').strip(); marker=(r.get('marker_id') or '').strip()
        key=(rid,fid)
        if not rid or not fid:
            issues.append({'severity':'HIGH','row':i,'id':rid or f'row-{i}','issue':'recommendation_id and footnote_id are required'}); continue
        if key in seen:
            issues.append({'severity':'HIGH','row':i,'id':rid,'issue':f'duplicate recommendation-footnote binding row for {fid}'})
        seen.add(key)
        scope=(r.get('scope') or '').strip().lower(); owner=(r.get('source_owner_recommendation_id') or '').strip(); source_scope=(r.get('source_scope_id') or '').strip()
        rec_markers=set(split_ids(r.get('recommendation_marker_ids','')))
        binding=(r.get('binding_status') or '').strip().lower(); sem=(r.get('semantic_adjudication') or '').strip().lower()
        required=(r.get('required_for_meaning') or '').strip().lower() in YES
        display=(r.get('display_location') or '').strip().lower()
        locator=(r.get('source_locator') or '').strip()

        if binding not in PASS:
            issues.append({'severity':'HIGH','id':rid,'footnote_id':fid,'issue':'footnote binding status unresolved'})
        if not locator:
            issues.append({'severity':'HIGH','id':rid,'footnote_id':fid,'issue':'footnote source locator missing'})
        if scope == 'recommendation':
            if owner != rid:
                issues.append({'severity':'CRITICAL','id':rid,'footnote_id':fid,'issue':f'footnote source owner {owner or "<blank>"} does not match recommendation {rid}'})
            if not marker:
                issues.append({'severity':'HIGH','id':rid,'footnote_id':fid,'issue':'recommendation-scoped footnote lacks marker'})
            elif marker not in rec_markers:
                issues.append({'severity':'CRITICAL','id':rid,'footnote_id':fid,'issue':f'footnote marker {marker} not present on recommendation'})
        elif scope in BROADER_SCOPES:
            if not source_scope:
                issues.append({'severity':'HIGH','id':rid,'footnote_id':fid,'issue':f'{scope}-scoped footnote lacks source_scope_id'})
        else:
            issues.append({'severity':'HIGH','id':rid,'footnote_id':fid,'issue':f'invalid/blank footnote scope: {scope or "<blank>"}'})

        if required and display in {'','omitted','dropped','none'}:
            issues.append({'severity':'HIGH','id':rid,'footnote_id':fid,'issue':'required footnote definition dropped'})
        elif required and display not in {'on_screen','onscreen'} and sem not in PASS:
            issues.append({'severity':'HIGH','id':rid,'footnote_id':fid,'issue':'required semantic footnote moved off-screen without adjudication'})
    return {'gate':'FOOTNOTE_BINDING','model':'one-row-per-binding','issues':issues,'pass':not issues}


def _validate_legacy(rows):
    # Backward-compatible legacy reader for v2.2.0 ledgers. New projects should
    # migrate to the one-row-per-binding template; legacy ledgers remain fail-closed.
    issues=[]
    for i,r in enumerate(rows,2):
        rid=(r.get('recommendation_id') or f'row-{i}').strip(); markers=set(split_ids(r.get('marker_ids',''))); footnotes=set(split_ids(r.get('footnote_ids','')))
        displayed=set(split_ids(r.get('displayed_footnote_ids',''))); required=set(split_ids(r.get('required_footnote_ids','')))
        binding=(r.get('footnote_binding_status') or '').strip().lower()
        if binding not in PASS: issues.append({'severity':'HIGH','id':rid,'issue':'footnote binding status unresolved'})
        if required-displayed: issues.append({'severity':'HIGH','id':rid,'issue':f'required footnote definition dropped: {sorted(required-displayed)}'})
        if displayed-footnotes: issues.append({'severity':'CRITICAL','id':rid,'issue':f'displayed footnote not bound to recommendation: {sorted(displayed-footnotes)}'})
        for item in footnotes:
            marker=(r.get(f'footnote_marker__{item}') or '').strip(); scope=(r.get(f'footnote_scope__{item}') or r.get('footnote_scope') or '').strip().lower()
            if not marker and scope not in BROADER_SCOPES:
                issues.append({'severity':'HIGH','id':rid,'issue':f'footnote {item} lacks marker or explicit broader scope'})
            if marker and marker not in markers:
                issues.append({'severity':'CRITICAL','id':rid,'issue':f'footnote {item} marker {marker} not present on recommendation'})
        if displayed and (r.get('footnote_display_policy') or '').strip().lower() == 'speaker_notes_only':
            sem=(r.get('footnote_semantic_adjudication') or '').strip().lower()
            if required and sem not in PASS: issues.append({'severity':'HIGH','id':rid,'issue':'required semantic footnote moved off-screen without adjudication'})
    return {'gate':'FOOTNOTE_BINDING','model':'legacy-v2.2.0','issues':issues,'pass':not issues}


def validate(path):
    rows=read_csv(path)
    if not rows:
        return {'gate':'FOOTNOTE_BINDING','model':'empty','issues':[],'pass':True}
    return _validate_new(rows) if 'footnote_id' in rows[0] else _validate_legacy(rows)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('csv'); a=ap.parse_args(); r=validate(a.csv); print(json.dumps(r,indent=2)); raise SystemExit(0 if r['pass'] else 1)
if __name__=='__main__': main()
