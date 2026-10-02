import yaml
from pathlib import Path
from scripts.state_manager import validate,next_state
def test_state_template():
    p=Path(__file__).parents[1]/'templates/project_state.yaml'; s=yaml.safe_load(p.read_text()); assert validate(s)==[]; assert next_state(s)['id']=='evidence_lock'
