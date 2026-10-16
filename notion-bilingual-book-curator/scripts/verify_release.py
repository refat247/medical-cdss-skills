"""Verify current mirrors, package inventory and exact root-correct archive."""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]
REQUIRED=['SKILL.md','README.md','CHANGELOG.md','VERSION','VERSIONING_DECISION.md','TEST_REPORT.md',
          'MANUAL_ACTIVATION.md','ACTIVATION_SMOKE_TEST.md','agents/openai.yaml','assets/icon.svg',
          'PACKAGE_MANIFEST.json','scripts/verify_release.py','references/html-reader-handoff.md']

def verify(archive=None):
    files={p.relative_to(ROOT).as_posix():p for p in ROOT.rglob('*') if p.is_file()}
    for rel in REQUIRED:
        assert rel in files and files[rel].stat().st_size, 'missing/empty '+rel
    assert not any('__pycache__' in p or p.endswith('.pyc') for p in files), 'compiled residue'
    skill=(ROOT/'SKILL.md').read_text()
    meta=yaml.safe_load(skill.split('---',2)[1]);version=meta['metadata']['version']
    assert re.search(r'^Version: '+re.escape(version)+r'$',skill,re.M)
    assert (ROOT/'VERSION').read_text().strip()==version
    assert re.search(r'^\*\*Version:\*\* '+re.escape(version)+r'\s', (ROOT/'README.md').read_text(),re.M)
    agent=yaml.safe_load((ROOT/'agents/openai.yaml').read_text())
    assert agent['policy']['products']==['chatgpt','codex'], 'unsupported product identifiers'
    assert agent['metadata']['version']==version
    assert agent['metadata']['status']==meta['metadata']['status']=='stable'
    assert '$notion-bilingual-book-curator' in agent['interface']['default_prompt']
    for name in ['MANUAL_ACTIVATION.md','ACTIVATION_SMOKE_TEST.md']:
        assert version in (ROOT/name).read_text().splitlines()[0], 'activation mirror drift'
    assert re.search(r'^## \[?'+re.escape(version)+r'\]? (?:—|-) ',(ROOT/'CHANGELOG.md').read_text(),re.M)
    for link in re.findall(r'`(references/[^`]+\.md)`',skill):
        assert link in files and files[link].stat().st_size, 'broken reference '+link
    manifest=json.loads((ROOT/'PACKAGE_MANIFEST.json').read_text())
    assert manifest['version']==version and manifest['name']==meta['name']
    assert set(manifest['files'])==set(files)-{'PACKAGE_MANIFEST.json'}, 'inventory drift'
    for rel,record in manifest['files'].items():
        data=files[rel].read_bytes()
        assert record=={'sha256':hashlib.sha256(data).hexdigest(),'size':len(data)}, 'file drift '+rel
    if archive:
        assert 'v'+version in Path(archive).name
        with zipfile.ZipFile(archive) as z:
            names=z.namelist()
            assert len(names)==len(set(names)) and set(names)==set(files), 'archive shape drift'
            assert 'SKILL.md' in names
            for rel in files:
                assert z.read(rel)==files[rel].read_bytes(), 'archive drift '+rel
    print('RELEASE VERIFY PASS — notion-bilingual-book-curator v'+version)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--archive');args=parser.parse_args();verify(args.archive)
