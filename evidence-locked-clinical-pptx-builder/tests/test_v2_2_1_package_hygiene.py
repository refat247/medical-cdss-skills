from pathlib import Path
import zipfile
from scripts.package_closure import create
from scripts.hash_manifest import write_manifest, verify_manifest


def test_runtime_cache_artifacts_excluded_from_packaged_zip(tmp_path):
    root=tmp_path/'r'; root.mkdir(); (root/'a.txt').write_text('x')
    (root/'.pytest_cache').mkdir(); (root/'.pytest_cache'/'README.md').write_text('cache')
    (root/'scripts').mkdir(); (root/'scripts'/'__pycache__').mkdir(); (root/'scripts'/'__pycache__'/'x.pyc').write_bytes(b'x')
    (root/'loose.pyo').write_bytes(b'x')
    out=tmp_path/'x.zip'; create(root,out)
    with zipfile.ZipFile(out) as z:
        names=z.namelist()
    assert names==['a.txt']


def test_manifest_ignores_runtime_cache_artifacts_and_self(tmp_path):
    root=tmp_path/'r'; root.mkdir(); (root/'a.txt').write_text('x')
    (root/'.pytest_cache').mkdir(); (root/'.pytest_cache'/'README.md').write_text('cache')
    manifest=root/'PACKAGE_MANIFEST.md'; write_manifest(root,manifest)
    r=verify_manifest(root,manifest)
    assert r['pass'] and r['rows']==1
