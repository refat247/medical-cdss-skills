from scripts.package_closure import create
def test_zip(tmp_path):
    root=tmp_path/'r'; root.mkdir(); (root/'a').write_text('x'); out=tmp_path/'x.zip'; r=create(root,out); assert r['entries']==1
