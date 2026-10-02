from pathlib import Path
from scripts.derivative_integrity import verify
def test_derivative_fingerprint():
    r=Path(__file__).parents[1]/'fixtures'; assert verify(r/'master_cases.csv',r/'derivative_cases_good.csv')['pass']; assert not verify(r/'master_cases.csv',r/'derivative_cases_bad.csv')['pass']
