from pathlib import Path
from scripts.slide_spec_validator import validate
def test_slide_spec():
    r=Path(__file__).parents[1]/'fixtures'; assert validate(r/'slide_spec_good.csv',['CASE-001'])==[]
