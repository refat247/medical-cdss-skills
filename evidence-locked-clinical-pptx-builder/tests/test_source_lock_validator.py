import yaml
from pathlib import Path
from scripts.source_lock_validator import validate_lock
def test_lock(tmp_path):
    d={'locked':True,'approved_clinical_sources':[{'source_id':'S1','path':'a.pdf','role':'guideline'}],'context_sources':[{'class':'OPERATIONAL_CONTEXT'}]}; p=tmp_path/'l.yaml'; p.write_text(yaml.safe_dump(d)); assert validate_lock(p)==[]
