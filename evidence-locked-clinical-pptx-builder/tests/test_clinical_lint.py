from pathlib import Path
from scripts.clinical_lint import lint
def test_context_not_evidence():
    r=Path(__file__).parents[1]/'fixtures'; assert lint(r/'slide_spec_good.csv',['S1'])==[]; assert lint(r/'slide_spec_bad_context.csv',['S1'],['LOCAL_CONTEXT'])
