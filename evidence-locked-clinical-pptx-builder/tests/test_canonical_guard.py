from pathlib import Path
import json
from scripts.canonical_guard import snapshot,verify
def test_guard(tmp_path):
    p=tmp_path/'a'; p.write_text('x'); s=snapshot([p]); j=tmp_path/'s.json'; j.write_text(json.dumps(s)); assert verify(j)['pass']; p.write_text('y'); assert not verify(j)['pass']
