from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

PASS_STATUSES = {'PASS', 'PASS_WITH_WARNINGS'}
POLICIES = {'required', 'required_unless_explicit_user_waiver', 'optional'}
ADJUDICATIONS = {'ACCEPT', 'REJECT', 'CLINICAL_ADJUDICATION_REQUIRED'}
NO_FINDING_MARKERS = {'NONE', 'NO FINDING', 'NO FINDINGS', 'CLEAR', 'NO ISSUE', 'NO ISSUES'}
REQUIRED_JSON_FIELDS = [
    'reviewer', 'reviewer_runtime', 'candidate_pptx_sha256',
    'rendered_slide_set_sha256', 'slide_count', 'overall_status',
    'clinical_change_authority', 'slide_by_slide_findings',
]


def _sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _parse_report(report: str | Path) -> dict:
    p = Path(report)
    txt = p.read_text(encoding='utf-8', errors='ignore')
    try:
        data = json.loads(txt)
    except Exception:
        return {'kind': 'text', 'data': None, 'raw': txt}
    if not isinstance(data, dict):
        return {'kind': 'invalid_json', 'data': data, 'raw': txt}
    return {'kind': 'json', 'data': data, 'raw': txt}


def _is_substantive_finding(row: dict) -> bool:
    status = str(row.get('status', '')).strip().upper()
    finding = str(row.get('finding', '')).strip()
    repair = str(row.get('proposed_repair', '')).strip()
    if status != 'PASS':
        return True
    if repair:
        return True
    return finding.upper() not in NO_FINDING_MARKERS


def _validate_slide_rows(rows, slide_count: int, *, stage: str, require_passlike: bool):
    issues = []
    accepted_repairs = []
    clinical_blocks = []
    seen = set()
    if not isinstance(rows, list):
        return [f'{stage}: slide rows must be a list'], accepted_repairs, clinical_blocks

    for idx, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            issues.append(f'{stage}: row {idx} is not an object')
            continue
        try:
            slide = int(row.get('slide'))
        except Exception:
            issues.append(f'{stage}: row {idx} has invalid slide number')
            continue
        if slide < 1 or slide > slide_count:
            issues.append(f'{stage}: slide {slide} out of range 1..{slide_count}')
        if slide in seen:
            issues.append(f'{stage}: duplicate slide row {slide}')
        seen.add(slide)

        status = str(row.get('status', '')).strip().upper()
        finding = str(row.get('finding', '')).strip()
        repair = str(row.get('proposed_repair', '')).strip()
        adjud = str(row.get('adjudication', '')).strip().upper()

        if not status:
            issues.append(f'{stage}: slide {slide} has empty status')
        if not finding:
            issues.append(f'{stage}: slide {slide} has empty finding')
        if require_passlike and status not in PASS_STATUSES:
            issues.append(f'{stage}: slide {slide} final status must be PASS/PASS_WITH_WARNINGS, got {status or "MISSING"}')

        substantive = _is_substantive_finding(row)
        if substantive:
            if adjud not in ADJUDICATIONS:
                issues.append(f'{stage}: slide {slide} finding/warning requires adjudication ACCEPT/REJECT/CLINICAL_ADJUDICATION_REQUIRED')
            elif adjud == 'CLINICAL_ADJUDICATION_REQUIRED':
                clinical_blocks.append(slide)
            elif adjud == 'ACCEPT':
                if not repair:
                    issues.append(f'{stage}: slide {slide} ACCEPT requires proposed_repair')
                accepted_repairs.append(slide)

    missing = [s for s in range(1, slide_count + 1) if s not in seen]
    if missing:
        issues.append(f'{stage}: missing slide rows {missing}')
    return issues, sorted(set(accepted_repairs)), sorted(set(clinical_blocks))


def _validate_repair_mapping(mapping, accepted_slides, slide_count):
    issues = []
    if not isinstance(mapping, list) or not mapping:
        return ['repair_mapping must be a non-empty list when a repair is accepted']
    mapped = set()
    for i, row in enumerate(mapping, 1):
        if not isinstance(row, dict):
            issues.append(f'repair_mapping row {i} is not an object')
            continue
        try:
            slide = int(row.get('slide'))
        except Exception:
            issues.append(f'repair_mapping row {i} has invalid slide number')
            continue
        if slide < 1 or slide > slide_count:
            issues.append(f'repair_mapping slide {slide} out of range 1..{slide_count}')
        if slide in mapped:
            issues.append(f'repair_mapping duplicate slide {slide}')
        mapped.add(slide)
        if not str(row.get('repair', '')).strip():
            issues.append(f'repair_mapping slide {slide} missing repair description')
    missing = [s for s in accepted_slides if s not in mapped]
    if missing:
        issues.append(f'repair_mapping missing accepted repair slides {missing}')
    return issues


def gate(report=None, waiver=None, policy='required_unless_explicit_user_waiver',
         pptx=None, rendered_slide_set_sha256=None,
         final_pptx=None, final_rendered_slide_set_sha256=None):
    """Fail-closed independent second-runtime visual-QA gate.

    JSON is the only certifying report format.

    policy values:
      required
      required_unless_explicit_user_waiver
      optional
    """
    policy = (policy or '').strip().lower()
    if policy not in POLICIES:
        return {
            'status': 'INVALID_POLICY', 'execution_status': 'INVALID_POLICY',
            'certification': 'NOT_CERTIFIED', 'policy': policy,
            'issues': [f'invalid independent_visual_qa_policy: {policy}'],
            'pass': False, 'details': {}
        }

    issues = []
    details = {}
    execution_status = None
    certification = 'NOT_CERTIFIED'

    if report:
        parsed = _parse_report(report)
        details['report_kind'] = parsed['kind']
        if parsed['kind'] != 'json':
            return {
                'status': 'NON_CERTIFYING_REPORT',
                'execution_status': 'NON_CERTIFYING_REPORT',
                'certification': 'NOT_CERTIFIED',
                'policy': policy,
                'issues': ['Markdown/free-text reports are non-certifying; normalize to the structured JSON schema'],
                'pass': False,
                'details': details,
            }

        data = parsed['data']
        for field in REQUIRED_JSON_FIELDS:
            if field not in data or data[field] in (None, ''):
                issues.append(f'missing required independent-review field: {field}')

        if str(data.get('clinical_change_authority', '')).strip().upper() != 'NONE':
            issues.append('clinical_change_authority must equal NONE')

        try:
            slide_count = int(data.get('slide_count', 0))
        except Exception:
            slide_count = 0
        if slide_count <= 0:
            issues.append('slide_count must be a positive integer')

        initial_accepted = []
        initial_clinical = []
        if slide_count > 0:
            row_issues, initial_accepted, initial_clinical = _validate_slide_rows(
                data.get('slide_by_slide_findings'), slide_count,
                stage='initial_review', require_passlike=False
            )
            issues.extend(row_issues)
        if initial_clinical:
            issues.append(f'clinical adjudication required for slides {initial_clinical}; independent QA cannot certify until resolved through the locked clinical pipeline')

        if pptx:
            expected = _sha256(pptx)
            if str(data.get('candidate_pptx_sha256', '')).lower() != expected:
                issues.append('candidate_pptx_sha256 does not match supplied PPTX')
        if rendered_slide_set_sha256:
            if str(data.get('rendered_slide_set_sha256', '')).lower() != str(rendered_slide_set_sha256).lower():
                issues.append('rendered_slide_set_sha256 does not match supplied rendered-slide set hash')

        overall = str(data.get('overall_status', '')).strip().upper()

        if initial_accepted:
            if not str(data.get('repaired_pptx_sha256', '')).strip():
                issues.append('accepted repair requires repaired_pptx_sha256')
            if not str(data.get('repaired_rendered_slide_set_sha256', '')).strip():
                issues.append('accepted repair requires repaired_rendered_slide_set_sha256')
            issues.extend(_validate_repair_mapping(data.get('repair_mapping'), initial_accepted, slide_count))
            if data.get('second_full_render_verification') is not True:
                issues.append('accepted repair requires second_full_render_verification=true')

            post_overall = str(data.get('post_repair_overall_status', '')).strip().upper()
            if post_overall not in PASS_STATUSES:
                issues.append(f'post_repair_overall_status must be PASS/PASS_WITH_WARNINGS, got {post_overall or "MISSING"}')

            if slide_count > 0:
                post_issues, post_accepted, post_clinical = _validate_slide_rows(
                    data.get('post_repair_slide_by_slide_findings'), slide_count,
                    stage='post_repair_review', require_passlike=True
                )
                issues.extend(post_issues)
                if post_accepted:
                    issues.append(f'post-repair review still contains ACCEPT repair adjudications on slides {post_accepted}')
                if post_clinical:
                    issues.append(f'post-repair review still requires clinical adjudication on slides {post_clinical}')

            if final_pptx:
                expected_final = _sha256(final_pptx)
                if str(data.get('repaired_pptx_sha256', '')).lower() != expected_final:
                    issues.append('repaired_pptx_sha256 does not match supplied final PPTX')
            if final_rendered_slide_set_sha256:
                if str(data.get('repaired_rendered_slide_set_sha256', '')).lower() != str(final_rendered_slide_set_sha256).lower():
                    issues.append('repaired_rendered_slide_set_sha256 does not match supplied final rendered-slide set hash')
        else:
            if overall not in PASS_STATUSES:
                issues.append(f'overall_status must be PASS/PASS_WITH_WARNINGS when no repair is accepted, got {overall or "MISSING"}')

        if issues:
            execution_status = 'INVALID_REPORT'
        else:
            execution_status = 'INDEPENDENT_QA_CERTIFIED'
            certification = 'CERTIFIED'

    elif waiver is not None:
        waiver_text = str(waiver).strip()
        if not waiver_text:
            execution_status = 'INDEPENDENT-QA-UNCERTIFIED'
            issues.append('independent QA waiver must be explicit and non-empty')
        elif policy == 'required':
            execution_status = 'INDEPENDENT-QA-UNCERTIFIED'
            issues.append('policy=required does not permit waiver')
        elif policy == 'required_unless_explicit_user_waiver':
            execution_status = 'INDEPENDENT_QA_WAIVED'
            details['waiver_reason'] = waiver_text
        else:
            execution_status = 'INDEPENDENT_QA_WAIVED'
            details['waiver_reason'] = waiver_text
    else:
        if policy == 'optional':
            execution_status = 'INDEPENDENT_QA_NOT_RUN_OPTIONAL'
        else:
            execution_status = 'INDEPENDENT-QA-UNCERTIFIED'
            issues.append('no structured independent review report and no explicit user waiver')

    pass_bool = (
        execution_status == 'INDEPENDENT_QA_CERTIFIED' or
        execution_status == 'INDEPENDENT_QA_WAIVED' or
        execution_status == 'INDEPENDENT_QA_NOT_RUN_OPTIONAL'
    )
    return {
        'status': execution_status,
        'execution_status': execution_status,
        'certification': certification,
        'policy': policy,
        'issues': issues,
        'pass': pass_bool,
        'details': details,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--report')
    ap.add_argument('--waiver')
    ap.add_argument('--policy', default='required_unless_explicit_user_waiver', choices=sorted(POLICIES))
    ap.add_argument('--pptx')
    ap.add_argument('--rendered-slide-set-sha256')
    ap.add_argument('--final-pptx')
    ap.add_argument('--final-rendered-slide-set-sha256')
    args = ap.parse_args()
    result = gate(
        args.report, args.waiver, args.policy,
        args.pptx, args.rendered_slide_set_sha256,
        args.final_pptx, args.final_rendered_slide_set_sha256,
    )
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['pass'] else 1)


if __name__ == '__main__':
    main()
