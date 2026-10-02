from __future__ import annotations
import argparse, re, fnmatch
from pathlib import Path
try:
    from scripts.common import sha256
except ModuleNotFoundError:
    from common import sha256

ROW_RE = re.compile(r'^\| `(.+?)` \| (\d+) \| `([0-9a-fA-F]{64})` \|$')
HYGIENE_DIRS={'.pytest_cache','__pycache__'}
HYGIENE_GLOBS=('*.pyc','*.pyo')


def _runtime_artifact(rel):
    p=Path(rel)
    return any(part in HYGIENE_DIRS for part in p.parts) or any(fnmatch.fnmatch(p.name,pat) for pat in HYGIENE_GLOBS)


def build(root, exclude=(), output_path=None):
    root = Path(root).resolve()
    ex = {str(x).replace('\\', '/') for x in exclude}
    if output_path:
        op = Path(output_path).resolve()
        try: ex.add(op.relative_to(root).as_posix())
        except ValueError: pass
    rows = []
    for p in sorted(x for x in root.rglob('*') if x.is_file()):
        rel = p.relative_to(root).as_posix()
        if rel in ex or _runtime_artifact(rel): continue
        rows.append((rel, p.stat().st_size, sha256(p)))
    return rows


def write_manifest(root, output, exclude=(), title='Package Manifest'):
    root = Path(root).resolve(); output = Path(output).resolve()
    rows = build(root, exclude=exclude, output_path=output)
    lines = [f'# {title}', '', 'Generation rule: the output manifest is automatically excluded from its own contents; runtime/test cache artifacts are also excluded.', '',
             '| Path | Bytes | SHA-256 |', '|---|---:|---|']
    lines += [f'| `{p}` | {n} | `{h}` |' for p, n, h in rows]
    output.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return rows


def parse_manifest(path):
    rows = []
    for line in Path(path).read_text(encoding='utf-8', errors='ignore').splitlines():
        m = ROW_RE.match(line.strip())
        if m: rows.append((m.group(1), int(m.group(2)), m.group(3).lower()))
    return rows


def verify_manifest(root, manifest_path):
    root = Path(root).resolve(); manifest_path = Path(manifest_path).resolve(); issues = []
    try: manifest_rel = manifest_path.relative_to(root).as_posix()
    except ValueError: manifest_rel = None
    rows = parse_manifest(manifest_path); seen = set()
    for rel, size, digest in rows:
        if rel in seen: issues.append(f'duplicate manifest row: {rel}')
        seen.add(rel)
        if manifest_rel and rel == manifest_rel: issues.append('manifest illegally contains a self-reference row')
        if _runtime_artifact(rel): issues.append(f'manifest illegally lists runtime/cache artifact: {rel}')
        p = root / rel
        if not p.exists() or not p.is_file(): issues.append(f'missing listed file: {rel}'); continue
        actual_size = p.stat().st_size; actual_hash = sha256(p)
        if actual_size != size: issues.append(f'byte mismatch: {rel}: manifest={size} actual={actual_size}')
        if actual_hash.lower() != digest.lower(): issues.append(f'hash mismatch: {rel}: manifest={digest} actual={actual_hash}')
    expected = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and not _runtime_artifact(p.relative_to(root).as_posix())}
    if manifest_rel: expected.discard(manifest_rel)
    omitted = sorted(expected - seen); extras = sorted(seen - expected)
    if omitted: issues.append(f'unlisted files: {omitted}')
    if extras: issues.append(f'rows outside package file set: {extras}')
    return {'rows': len(rows), 'issues': issues, 'pass': not issues}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--output', required=True); ap.add_argument('--exclude', action='append', default=[]); ap.add_argument('--title', default='Package Manifest'); ap.add_argument('--verify', action='store_true'); args = ap.parse_args()
    rows = write_manifest(args.root, args.output, args.exclude, args.title); result = {'rows': len(rows), 'output': str(Path(args.output).resolve())}
    if args.verify: result['verification'] = verify_manifest(args.root, args.output)
    print(result)
    if args.verify and not result['verification']['pass']: raise SystemExit(1)

if __name__ == '__main__': main()
