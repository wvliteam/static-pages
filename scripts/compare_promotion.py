#!/usr/bin/env python3
"""Compare an approved static artifact directory with its promotion target."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile
from pathlib import PurePosixPath

from verify_artifact_manifest import bundle_digest, file_rows, validate_rows


def compare(source: Path, target: Path) -> dict:
    source, target = source.resolve(), target.resolve()
    if not source.is_dir() or not target.is_dir():
        raise ValueError('Both --source-root and --target-root must be existing directories')
    source_rows, target_rows = file_rows(source), file_rows(target)
    source_by_path = {row['path']: row for row in source_rows}
    target_by_path = {row['path']: row for row in target_rows}
    files = []
    for name in sorted(source_by_path.keys() | target_by_path.keys()):
        left, right = source_by_path.get(name), target_by_path.get(name)
        status = ('added_to_target' if left is None else
                  'missing_from_target' if right is None else
                  'same' if left == right else 'modified')
        files.append({'path': name, 'status': status, 'source': left, 'target': right})
    source_bundle, target_bundle = bundle_digest(source_rows), bundle_digest(target_rows)
    return {'ok': source_rows == target_rows, 'source_root': str(source),
            'target_root': str(target), 'source_bundle_sha256': source_bundle,
            'target_bundle_sha256': target_bundle, 'files': files}


def preview_rows(repo_root: Path, preview_sha: str, task: str) -> list[dict]:
    if not re.fullmatch('[0-9a-f]{40}', preview_sha):
        raise ValueError('--preview-sha must be a full 40-character SHA')
    if not re.fullmatch('[a-z0-9][a-z0-9-]{0,79}', task):
        raise ValueError('--task must be a lowercase slug')
    prefix = PurePosixPath('artifacts', task, 'public')
    archive = subprocess.run(
        ['git', 'archive', '--format=tar', preview_sha, str(prefix)], cwd=repo_root,
        check=True, capture_output=True).stdout
    rows = []
    seen = set()
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:') as tar:
        for member in tar:
            parts = PurePosixPath(member.name).parts
            if (member.isdir() and len(parts) <= len(prefix.parts)
                    and prefix.parts[:len(parts)] == parts):
                continue
            if parts[:len(prefix.parts)] != prefix.parts:
                raise ValueError('Git archive contains a path outside the selected task')
            relative = PurePosixPath(*parts[len(prefix.parts):])
            if not relative.parts:
                continue
            if (any(part in {'.', '..'} or part.startswith('.') or '\\' in part
                    for part in relative.parts)):
                raise ValueError(f'Unsafe preview artifact path: {relative}')
            if member.isdir():
                continue
            if not member.isfile() or member.issym() or member.islnk():
                raise ValueError(f'Only regular preview files are accepted: {relative}')
            name = relative.as_posix()
            if name in seen:
                raise ValueError(f'Duplicate preview artifact path: {name}')
            seen.add(name)
            stream = tar.extractfile(member)
            if stream is None:
                raise ValueError(f'Missing preview artifact bytes: {name}')
            body = stream.read()
            rows.append({'path': name, 'bytes': len(body),
                         'sha256': hashlib.sha256(body).hexdigest()})
    return sorted(rows, key=lambda item: item['path'])


def compare_rows(source_rows: list[dict], target: Path) -> dict:
    target = target.resolve()
    if not target.is_dir():
        raise ValueError('--target-root must be an existing directory')
    target_rows = file_rows(target)
    source_by_path = {row['path']: row for row in source_rows}
    target_by_path = {row['path']: row for row in target_rows}
    files = []
    for name in sorted(source_by_path.keys() | target_by_path.keys()):
        left, right = source_by_path.get(name), target_by_path.get(name)
        status = ('added_to_target' if left is None else
                  'missing_from_target' if right is None else
                  'same' if left == right else 'modified')
        files.append({'path': name, 'status': status, 'source': left, 'target': right})
    source_bundle, target_bundle = bundle_digest(source_rows), bundle_digest(target_rows)
    return {'ok': source_rows == target_rows, 'target_root': str(target),
            'source_bundle_sha256': source_bundle,
            'target_bundle_sha256': target_bundle, 'files': files}


def verify_manifest(rows: list[dict], manifest_path: Path) -> str:
    data = json.loads(manifest_path.read_text(encoding='utf-8'))
    artifact_manifest = data.get('artifact_manifest') if isinstance(data, dict) else None
    if not isinstance(artifact_manifest, dict):
        raise ValueError('Manifest lacks artifact_manifest')
    expected_rows = validate_rows(artifact_manifest.get('files'))
    expected_bundle = artifact_manifest.get('bundle_sha256')
    if expected_bundle != bundle_digest(expected_rows):
        raise ValueError('Artifact manifest bundle digest is inconsistent')
    if rows != expected_rows:
        raise ValueError('Approved preview files differ from the builder-checked artifact')
    return expected_bundle


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--source-root', type=Path,
                        help='Clean artifact tree extracted from the approved preview SHA')
    source.add_argument('--repo-root', type=Path,
                        help='Repository containing the approved preview commit')
    parser.add_argument('--preview-sha', help='Approved full PR head SHA (requires --repo-root)')
    parser.add_argument('--task', help='Preview task slug (requires --repo-root)')
    parser.add_argument('--manifest', type=Path,
                        help='Builder check JSON to bind the comparison to the checked bundle')
    parser.add_argument('--target-root', required=True, type=Path,
                        help='Prepared formal directory before commit')
    parser.add_argument('--output', type=Path,
                        help='Optional JSON report outside the source and target trees')
    args = parser.parse_args(argv)
    if args.output:
        output = args.output.resolve()
        protected_roots = [args.target_root]
        if args.source_root:
            protected_roots.append(args.source_root)
        if args.repo_root and args.task:
            protected_roots.append(args.repo_root / 'artifacts' / args.task / 'public')
        if any(output.is_relative_to(root.resolve()) for root in protected_roots):
            parser.error('--output must be outside the source and target trees')
        if args.manifest and output == args.manifest.resolve():
            parser.error('--output must not overwrite --manifest')
    try:
        if args.repo_root:
            if not args.preview_sha or not args.task:
                parser.error('--repo-root requires --preview-sha and --task')
            rows = preview_rows(args.repo_root.resolve(), args.preview_sha, args.task)
            if args.manifest:
                checked_bundle = verify_manifest(rows, args.manifest)
            else:
                parser.error('--repo-root mode requires --manifest from the builder check')
            result = compare_rows(rows, args.target_root)
            result.update(source_sha=args.preview_sha, task=args.task,
                          source_repository=str(args.repo_root.resolve()),
                          checked_bundle_sha256=checked_bundle)
        else:
            if args.preview_sha or args.task or args.manifest:
                parser.error('--preview-sha, --task, and --manifest require --repo-root')
            result = compare(args.source_root, args.target_root)
    except (ValueError, OSError, subprocess.CalledProcessError, tarfile.TarError) as exc:
        result = {'ok': False, 'error': str(exc)}
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding='utf-8')
    sys.stdout.write(encoded)
    return 0 if result.get('ok') else 1


if __name__ == '__main__':
    raise SystemExit(main())
