import json
from pathlib import Path
import yaml
from scripts.validate_project import validate_project

ROOT = Path(__file__).parents[1]


def test_v2_4_metadata_identifies_immediate_predecessor_correctly():
    m = json.loads((ROOT/'MANIFEST.json').read_text())
    assert m['version'] == '2.4.0'
    assert m['immediate_predecessor'] == '2.3.0'
    assert m['breaking_change'] is False
    assert m['lineage_origin'] == '1.0.0'
    assert m['major_predecessor'] == '2.0.0'
    assert 'predecessor' not in m


def test_default_high_stakes_policy_is_required_unless_explicit_user_waiver():
    s = yaml.safe_load((ROOT/'templates/project_state.yaml').read_text())
    assert s['settings']['high_stakes_clinical'] is True
    rp = s['release_policy']
    assert rp['independent_visual_qa_policy'] == 'required_unless_explicit_user_waiver'
    assert 'independent_visual_qa' not in rp
    assert 'independent_visual_qa_waivable' not in rp


def test_project_validator_accepts_new_policy_enum(tmp_path):
    s = yaml.safe_load((ROOT/'templates/project_state.yaml').read_text())
    s['project']['id'] = 'test'
    s['evidence_contract']['locked'] = False
    p = tmp_path/'state.yaml'; p.write_text(yaml.safe_dump(s, sort_keys=False))
    assert validate_project(p) == []


def test_project_validator_rejects_invalid_policy(tmp_path):
    s = yaml.safe_load((ROOT/'templates/project_state.yaml').read_text())
    s['project']['id'] = 'test'
    s['release_policy']['independent_visual_qa_policy'] = 'preferred'
    p = tmp_path/'state.yaml'; p.write_text(yaml.safe_dump(s, sort_keys=False))
    errs = validate_project(p)
    assert any('independent_visual_qa_policy' in e for e in errs)
