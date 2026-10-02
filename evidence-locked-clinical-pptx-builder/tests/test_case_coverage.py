from pathlib import Path
from scripts.case_coverage_audit import audit
def test_case_coverage():
    r=Path(__file__).parents[1]/'fixtures'; assert audit(r/'source_nodes.csv',r/'cases_complete.csv')['pass']
