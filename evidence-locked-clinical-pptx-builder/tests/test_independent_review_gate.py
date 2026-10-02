import json
from pathlib import Path
from scripts.independent_review_gate import gate


def _write(tmp_path, data, name='report.json'):
    p = tmp_path / name
    p.write_text(json.dumps(data), encoding='utf-8')
    return p


def _base(slides=2):
    return {
        'reviewer': 'independent-reviewer',
        'reviewer_runtime': 'second-runtime',
        'candidate_pptx_sha256': 'candidate-hash',
        'rendered_slide_set_sha256': 'render-hash',
        'slide_count': slides,
        'overall_status': 'PASS',
        'clinical_change_authority': 'NONE',
        'slide_by_slide_findings': [
            {'slide': i, 'status': 'PASS', 'finding': 'NONE', 'proposed_repair': '', 'adjudication': ''}
            for i in range(1, slides + 1)
        ],
    }


def test_simple_free_text_pass_is_non_certifying():
    root = Path(__file__).parents[1]
    r = gate(report=root/'fixtures/independent_review_bad_pass_marker.txt', policy='required')
    assert not r['pass']
    assert r['status'] == 'NON_CERTIFYING_REPORT'
    assert r['certification'] == 'NOT_CERTIFIED'


def test_markdown_marker_only_is_non_certifying():
    root = Path(__file__).parents[1]
    r = gate(report=root/'fixtures/independent_review_marker_only.md', policy='required')
    assert not r['pass']
    assert r['status'] == 'NON_CERTIFYING_REPORT'


def test_required_policy_does_not_permit_waiver():
    r = gate(waiver='user explicitly waives second-runtime review', policy='required')
    assert not r['pass']
    assert r['status'] == 'INDEPENDENT-QA-UNCERTIFIED'
    assert r['certification'] == 'NOT_CERTIFIED'


def test_explicit_user_waiver_returns_waived_never_certified():
    r = gate(waiver='user explicitly accepts release without second-runtime QA', policy='required_unless_explicit_user_waiver')
    assert r['pass']
    assert r['status'] == 'INDEPENDENT_QA_WAIVED'
    assert r['certification'] == 'NOT_CERTIFIED'


def test_missing_report_without_waiver_fails_closed():
    r = gate(policy='required_unless_explicit_user_waiver')
    assert not r['pass']
    assert r['status'] == 'INDEPENDENT-QA-UNCERTIFIED'


def test_clean_structured_json_passes(tmp_path):
    r = gate(report=_write(tmp_path, _base()), policy='required')
    assert r['pass']
    assert r['status'] == 'INDEPENDENT_QA_CERTIFIED'
    assert r['certification'] == 'CERTIFIED'


def test_duplicate_slide_rows_fail(tmp_path):
    d = _base()
    d['slide_by_slide_findings'][1]['slide'] = 1
    r = gate(report=_write(tmp_path, d), policy='required')
    assert not r['pass']
    assert any('duplicate slide row 1' in x for x in r['issues'])


def test_missing_slide_row_fails(tmp_path):
    d = _base(3)
    d['slide_by_slide_findings'] = d['slide_by_slide_findings'][:2]
    r = gate(report=_write(tmp_path, d), policy='required')
    assert not r['pass']
    assert any('missing slide rows [3]' in x for x in r['issues'])


def test_out_of_range_slide_row_fails(tmp_path):
    d = _base()
    d['slide_by_slide_findings'][1]['slide'] = 3
    r = gate(report=_write(tmp_path, d), policy='required')
    assert not r['pass']
    assert any('out of range' in x for x in r['issues'])


def test_warning_without_adjudication_fails(tmp_path):
    d = _base()
    d['slide_by_slide_findings'][1].update(status='PASS_WITH_WARNINGS', finding='footer small')
    r = gate(report=_write(tmp_path, d), policy='required')
    assert not r['pass']
    assert any('requires adjudication' in x for x in r['issues'])


def _accepted_repair_base():
    d = _base()
    d['overall_status'] = 'REPAIR'
    d['slide_by_slide_findings'][1].update(
        status='PASS_WITH_WARNINGS', finding='footer too small',
        proposed_repair='enlarge source footer', adjudication='ACCEPT'
    )
    d['repair_mapping'] = [{'slide': 2, 'repair': 'enlarge source footer'}]
    d['repaired_pptx_sha256'] = 'repaired-pptx-hash'
    d['repaired_rendered_slide_set_sha256'] = 'repaired-render-hash'
    d['second_full_render_verification'] = True
    d['post_repair_overall_status'] = 'PASS'
    d['post_repair_slide_by_slide_findings'] = [
        {'slide': 1, 'status': 'PASS', 'finding': 'NONE', 'proposed_repair': '', 'adjudication': ''},
        {'slide': 2, 'status': 'PASS', 'finding': 'NONE', 'proposed_repair': '', 'adjudication': ''},
    ]
    return d


def test_accepted_repair_without_repaired_pptx_hash_fails(tmp_path):
    d = _accepted_repair_base(); d['repaired_pptx_sha256'] = ''
    r = gate(report=_write(tmp_path, d), policy='required')
    assert not r['pass']
    assert any('repaired_pptx_sha256' in x for x in r['issues'])


def test_accepted_repair_without_final_render_hash_fails(tmp_path):
    d = _accepted_repair_base(); d['repaired_rendered_slide_set_sha256'] = ''
    r = gate(report=_write(tmp_path, d), policy='required')
    assert not r['pass']
    assert any('repaired_rendered_slide_set_sha256' in x for x in r['issues'])


def test_accepted_repair_without_second_full_render_fails(tmp_path):
    d = _accepted_repair_base(); d['second_full_render_verification'] = False
    r = gate(report=_write(tmp_path, d), policy='required')
    assert not r['pass']
    assert any('second_full_render_verification' in x for x in r['issues'])


def test_clinical_adjudication_required_blocks_certification(tmp_path):
    d = _base()
    d['slide_by_slide_findings'][0].update(
        status='PASS_WITH_WARNINGS', finding='possible misleading clinical emphasis',
        proposed_repair='', adjudication='CLINICAL_ADJUDICATION_REQUIRED'
    )
    r = gate(report=_write(tmp_path, d), policy='required')
    assert not r['pass']
    assert any('clinical adjudication required' in x.lower() for x in r['issues'])


def test_complete_post_repair_structured_review_passes(tmp_path):
    d = _accepted_repair_base()
    r = gate(report=_write(tmp_path, d), policy='required')
    assert r['pass']
    assert r['status'] == 'INDEPENDENT_QA_CERTIFIED'
    assert r['certification'] == 'CERTIFIED'


def test_post_repair_missing_slide_fails(tmp_path):
    d = _accepted_repair_base()
    d['post_repair_slide_by_slide_findings'] = d['post_repair_slide_by_slide_findings'][:1]
    r = gate(report=_write(tmp_path, d), policy='required')
    assert not r['pass']
    assert any('post_repair_review: missing slide rows' in x for x in r['issues'])
