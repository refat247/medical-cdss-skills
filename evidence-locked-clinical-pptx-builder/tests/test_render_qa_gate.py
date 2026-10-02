from pathlib import Path
from PIL import Image
from scripts.render_qa_gate import gate

def test_render_gate_requires_ledger_when_requested(tmp_path):
    root=Path(__file__).parents[1]; pptx=root/'fixtures/pptx/clean.pptx'
    for i in [1,2]: Image.new('RGB',(1280,720),'white').save(tmp_path/f'slide-{i}.png')
    r=gate(pptx,tmp_path,require_ledger=True)
    assert not r['pass']
    assert r['ledger']['status']=='RENDER-UNCERTIFIED'

def test_render_gate_with_domain_ledger_passes(tmp_path):
    root=Path(__file__).parents[1]; pptx=root/'fixtures/pptx/clean.pptx'
    for i in [1,2]: Image.new('RGB',(1280,720),'white').save(tmp_path/f'slide-{i}.png')
    assert gate(pptx,tmp_path,root/'fixtures/visual_review_complete_domains.csv',require_ledger=True)['pass']
