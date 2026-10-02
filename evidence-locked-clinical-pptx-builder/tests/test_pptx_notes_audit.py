from pathlib import Path
from scripts.pptx_notes_audit import audit
def test_notes():
    r=Path(__file__).parents[1]/'fixtures/pptx'; assert audit(r/'clean.pptx')['pass']; assert not audit(r/'missing_notes.pptx')['pass']
