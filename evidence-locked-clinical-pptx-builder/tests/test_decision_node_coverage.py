from pathlib import Path
from scripts.decision_node_coverage import audit
def test_node_coverage():
    r=Path(__file__).parents[1]/'fixtures'; assert audit(r/'source_nodes.csv',r/'coverage_complete.csv')['pass']
