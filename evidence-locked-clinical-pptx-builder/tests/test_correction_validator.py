from pathlib import Path
from scripts.correction_validator import validate
def test_correction():
    r=Path(__file__).parents[1]/'fixtures'; assert validate(r/'corrections.csv',r/'supersessions.csv')==[]
