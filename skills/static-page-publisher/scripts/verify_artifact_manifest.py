#!/usr/bin/env python3
"""Verify a builder-produced artifact manifest against its current directory."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys


def file_rows(root: Path) -> list[dict]:
    rows = []
    for path in sorted(root.rglob('*'), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise ValueError(f'Symlinks are not allowed in an artifact: {relative}')
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError(f'Only regular files are allowed in an artifact: {relative}')
        content = path.read_bytes()
        rows.append({'path': relative, 'bytes': len(content),
                     'sha256': hashlib.sha256(content).hexdigest()})
    return rows


def bundle_digest(rows: list[dict]) -> str:
    canonical = json.dumps(rows, ensure_ascii=False, sort_keys=True,
                           separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(canonical).hexdigest()


def validate_rows(value) -> list[dict]:
    if not isinstance(value, list):
        raise ValueError('artifact_manifest.files must be a list')
    rows, seen = [], set()
    for item in value:
        if not isinstance(item, dict):
            raise ValueError('Each artifact file entry must be an object')
        name, size, digest = item.get('path'), item.get('bytes'), item.get('sha256')
        path = PurePosixPath(name) if isinstance(name, str) else None
        if (path is None or not name or name.startswith('/') or str(path) != name
                or '\\' in name or '..' in path.parts or '.' in path.parts
                or any(part.startswith('.') for part in path.parts)):
            raise ValueError(f'Unsafe artifact path: {name!r}')
        if name in seen:
            raise ValueError(f'Duplicate artifact path: {name}')
        if type(size) is not int or size < 0:
            raise ValueError(f'Invalid artifact byte size: {name}')
        if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
            raise ValueError(f'Invalid artifact SHA-256: {name}')
        seen.add(name)
        rows.append({'path': name, 'bytes': size, 'sha256': digest})
    if rows != sorted(rows, key=lambda item: item['path']):
        raise ValueError('artifact_manifest.files must be sorted by relative path')
    return rows


def verify(root: Path, manifest_path: Path) -> dict:
    root = root.resolve()
    manifest_path = manifest_path.resolve()
    if not root.is_dir():
        raise ValueError('--root must be an existing directory')
    if manifest_path.is_relative_to(root):
        raise ValueError('--manifest must be outside --root')
    source = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest = source.get('artifact_manifest') if isinstance(source, dict) else None
    if not isinstance(manifest, dict):
        raise ValueError('Manifest lacks artifact_manifest')
    expected_rows = validate_rows(manifest.get('files'))
    expected_bundle = manifest.get('bundle_sha256')
    if not isinstance(expected_bundle, str) or not re.fullmatch('[0-9a-f]{64}', expected_bundle):
        raise ValueError('Invalid artifact bundle SHA-256')
    computed_expected = bundle_digest(expected_rows)
    if expected_bundle != computed_expected:
        raise ValueError('Artifact manifest bundle digest is inconsistent')

    actual_rows = file_rows(root)
    actual_by_path = {row['path']: row for row in actual_rows}
    expected_by_path = {row['path']: row for row in expected_rows}
    records = []
    for name in sorted(expected_by_path.keys() | actual_by_path.keys()):
        expected, actual = expected_by_path.get(name), actual_by_path.get(name)
        records.append({'path': name, 'status': ('added' if expected is None else
                        'missing' if actual is None else
                        'matched' if expected == actual else 'changed'),
                        'expected': expected, 'actual': actual})
    actual_bundle = bundle_digest(actual_rows)
    ok = expected_rows == actual_rows and expected_bundle == actual_bundle
    return {'ok': ok, 'root': str(root), 'manifest': str(manifest_path),
            'expected_bundle_sha256': expected_bundle,
            'actual_bundle_sha256': actual_bundle, 'files': records}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--manifest', required=True, type=Path,
                        help='JSON output from check_static_html.py')
    args = parser.parse_args(argv)
    try:
        result = verify(args.root, args.manifest)
    except (ValueError, TypeError, KeyError, OSError, json.JSONDecodeError) as exc:
        result = {'ok': False, 'error': str(exc)}
    sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return 0 if result.get('ok') else 1


if __name__ == '__main__':
    raise SystemExit(main())
