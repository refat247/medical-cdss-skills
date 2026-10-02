import csv
from pathlib import Path

from scripts.case_reveal_layout_gate import audit as layout_audit
from scripts.prompt_semantics_validator import validate as prompt_validate


ROOT = Path(__file__).parents[1]
BASELINE = Path('D:/DYS_2026_v1.3_NEW_CHAT_CONTINUATION_PACKAGE/DYS_2026_v1.3_NEW_CHAT_CONTINUATION_PACKAGE/03_CANDIDATE_DECK/DYS_2026_Master_Core_v1.3_REPAIRED_PRECANONICAL.pptx')
REFERENCE = ROOT / 'assets/design_references/DYS_2026_Master_Core_v1.5_VISUAL_REPAIR_PRECANONICAL.pptx'


def _row(**changes):
    scenario = 'An adult is being assessed for ASCVD risk after a standard lipid profile.'
    question = 'Which measurement should guide the next risk assessment decision?'
    row = dict(case_id='C1', source_derived_scenario=scenario, case_query_setup=question,
               expected_answer='measure apoB', expected_decision_class='risk assessment',
               withheld_decision_text='measure apoB', prompt_text=f'{scenario} {question}',
               prompt_leak_status='PASS', prompt_coherence_status='PASS',
               prompt_semantic_review_status='PASS', reviewer_notes='source review complete')
    row.update(changes)
    return row


def _check(tmp_path, row):
    path = tmp_path / 'prompts.csv'
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=row)
        writer.writeheader()
        writer.writerow(row)
    return prompt_validate(path)


def test_neutral_should_question_is_allowed(tmp_path):
    scenario = 'An adult has a lipid profile available for risk assessment.'
    question = 'Should a further measurement be considered for risk assessment?'
    assert _check(tmp_path, _row(source_derived_scenario=scenario, case_query_setup=question,
                                 prompt_text=f'{scenario} {question}'))['pass']


def test_source_metalanguage_is_rejected(tmp_path):
    scenario = 'In the source-defined branch, an adult has elevated risk.'
    result = _check(tmp_path, _row(source_derived_scenario=scenario,
                                   prompt_text=f'{scenario} Which decision follows?'))
    assert not result['pass']
    assert any('metalanguage' in i['issue'] for i in result['issues'])


def test_recommendation_action_and_fragment_are_rejected(tmp_path):
    scenario = 'An adult has elevated risk; treatment with a statin is recommended; rechallenge.'
    result = _check(tmp_path, _row(source_derived_scenario=scenario,
                                   prompt_text=f'{scenario} Which decision follows?'))
    assert not result['pass']
    assert any('leaked' in i['issue'] for i in result['issues'])
    assert any('dangling fragment' in i['issue'] for i in result['issues'])


def test_scenario_prompt_drift_and_short_stem_are_rejected(tmp_path):
    result = _check(tmp_path, _row(source_derived_scenario='Adult at risk.',
                                   case_query_setup='What now?', prompt_text='What now?'))
    assert not result['pass']
    assert any('drift' in i['issue'] for i in result['issues'])
    assert any('short' in i['issue'] for i in result['issues'])


def test_layout_screen_detects_baseline_risks_without_certifying_reference():
    if not BASELINE.exists():
        return  # Portable package tests do not require the user's source deck.
    old = layout_audit(BASELINE, [5, 14, 16])
    new = layout_audit(REFERENCE, [5, 14, 16])
    assert old['certifies_visual_quality'] is False
    assert new['certifies_visual_quality'] is False
    assert len(new['issues']) < len(old['issues'])
    assert any(i['code'] == 'TITLE_TEXT_FIT' for i in old['issues'])
