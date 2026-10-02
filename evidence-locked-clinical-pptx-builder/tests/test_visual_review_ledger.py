from pathlib import Path
from scripts.visual_review_ledger import validate_ledger

def test_ledger_basic_and_domain_complete():
    r=Path(__file__).parents[1]/'fixtures'
    assert validate_ledger(r/'visual_review_complete.csv',2,True)['pass']
    assert not validate_ledger(r/'visual_review_incomplete.csv',2,True)['pass']
    assert validate_ledger(r/'visual_review_complete_domains.csv',2,True,True)['pass']


def test_visual_ledger_rejects_duplicate_and_out_of_range(tmp_path):
    import csv
    from scripts.visual_review_ledger import DOMAIN_COLUMNS
    cols=['slide','status','reviewer']+DOMAIN_COLUMNS
    rows=[]
    for s in [1,1,3]:
        row={'slide':s,'status':'PASS','reviewer':'r'}
        row.update({c:'PASS' for c in DOMAIN_COLUMNS})
        rows.append(row)
    f=tmp_path/'ledger.csv'
    with f.open('w',newline='',encoding='utf-8') as fh:
        w=csv.DictWriter(fh,fieldnames=cols); w.writeheader(); w.writerows(rows)
    r=validate_ledger(f,2,require_final_pass=True,require_domain_columns=True)
    assert not r['pass']
    txt=str(r['issues'])
    assert 'duplicate slide row' in txt
    assert 'out of range' in txt
