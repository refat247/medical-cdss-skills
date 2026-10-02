from pathlib import Path
from scripts.hash_manifest import build, write_manifest, verify_manifest, parse_manifest


def test_manifest_build_basic(tmp_path):
    (tmp_path/'a').write_text('x')
    rows = build(tmp_path)
    assert len(rows) == 1 and rows[0][0] == 'a'


def test_generated_manifest_excludes_itself_and_all_hashes_verify(tmp_path):
    (tmp_path/'a.txt').write_text('alpha')
    (tmp_path/'b.txt').write_text('beta')
    out = tmp_path/'PACKAGE_MANIFEST.md'
    rows = write_manifest(tmp_path, out, title='Package Manifest test')
    assert all(rel != 'PACKAGE_MANIFEST.md' for rel, _, _ in rows)
    parsed = parse_manifest(out)
    assert all(rel != 'PACKAGE_MANIFEST.md' for rel, _, _ in parsed)
    result = verify_manifest(tmp_path, out)
    assert result['pass'], result['issues']
    assert result['rows'] == 2


def test_manifest_verifier_detects_tamper(tmp_path):
    f = tmp_path/'a.txt'; f.write_text('alpha')
    out = tmp_path/'PACKAGE_MANIFEST.md'
    write_manifest(tmp_path, out)
    f.write_text('changed')
    result = verify_manifest(tmp_path, out)
    assert not result['pass']
    assert any('mismatch' in x for x in result['issues'])
