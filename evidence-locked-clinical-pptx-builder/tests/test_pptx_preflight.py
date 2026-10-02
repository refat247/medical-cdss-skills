from pathlib import Path
from scripts.pptx_preflight import audit
def test_clean_and_bad():
    r=Path(__file__).parents[1]/'fixtures/pptx'; assert audit(r/'clean.pptx')['pass']; assert not audit(r/'tiny_source.pptx')['pass']; assert not audit(r/'offslide_overlap_placeholder.pptx')['pass']
