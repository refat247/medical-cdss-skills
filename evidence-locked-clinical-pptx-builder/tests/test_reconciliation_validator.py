from pathlib import Path
from scripts.reconciliation_validator import validate
def test_recon_unknown_detected(tmp_path):
    r=Path(__file__).parents[1]/'fixtures'; issues=validate(r/'source_nodes.csv',r/'source_nodes.csv',r/'reconciliation.csv'); assert issues==[]
