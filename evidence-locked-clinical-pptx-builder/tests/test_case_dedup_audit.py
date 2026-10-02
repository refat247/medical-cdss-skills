from pathlib import Path
from scripts.case_dedup_audit import audit
def test_duplicates_detected():
    r=Path(__file__).parents[1]/'fixtures'; assert not audit(r/'cases_duplicate.csv',['distinct_decision','expected_answer','source_ids'])['pass']
