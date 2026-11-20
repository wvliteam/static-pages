#!/usr/bin/env python3
"""Verify deployed source identities and file hashes; no HTML layout checking."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin, urlsplit
from urllib.request import Request, urlopen

MAX_FILE = 20 * 1024 * 1024
MAX_FILES = 1000


def relative_path(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError('Empty or invalid file path in deployment record')
    parsed = urlsplit(value)
    path = PurePosixPath(value)
    if (parsed.scheme or parsed.netloc or parsed.query or parsed.fragment
            or value.startswith('/') or '%' in value or '\\' in value
            or '..' in path.parts or str(path) != value or value.endswith('/')):
        raise ValueError('Unsafe deployment path: ' + value)
    return value


def page_path(route: str) -> str:
    if route in {'.', ''}:
        return 'index.html'
    route = route[:-1] if route.endswith('/') else route
    relative_path(route)
    return route if route.endswith('.html') else route + '/index.html'


def public_url(base_url: str, file: str) -> str:
    path = '' if file == 'index.html' else file
    if path.endswith('/index.html'):
        path = path[:-len('index.html')]
    return urljoin(base_url, quote(path, safe='/'))


def fetch(url: str, timeout: float, limit: int = MAX_FILE) -> tuple[bytes, dict]:
    request = Request(url, headers={'User-Agent': 'StaticPagePublisher-Verify/2.0',
                                    'Cache-Control': 'no-cache'})
    with urlopen(request, timeout=timeout) as response:
        data = response.read(limit + 1)
        metadata = {'url': url, 'final_url': response.geturl(), 'http_status': response.status,
                    'content_type': response.headers.get_content_type()}
    if len(data) > limit:
        raise ValueError('Response exceeds verification size limit')
    if metadata['http_status'] != 200:
        raise ValueError('Expected HTTP 200: ' + url)
    return data, metadata


def digest(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise ValueError('Invalid SHA-256 in deployment record')
    return value


def verify(args) -> dict:
    raw, _ = fetch(urljoin(args.base_url, 'deployment.json'), args.timeout, 2 * 1024 * 1024)
    manifest = json.loads(raw)
    main_sha = manifest.get('main_sha')
    if not isinstance(main_sha, str) or not re.fullmatch('[0-9a-f]{40}', main_sha):
        raise ValueError('Missing or invalid main SHA in deployment record')
    if args.main_sha and main_sha != args.main_sha:
        raise ValueError('Deployed main SHA differs from the requested version')

    targets = []
    if args.preview_pr is not None:
        previews = [p for p in manifest.get('previews', [])
                    if p.get('pr') == args.preview_pr and (not args.task or p.get('task') == args.task)]
        if not previews:
            raise ValueError('Requested PR preview is absent from this deployment')
        tasks = set()
        for preview in previews:
            task = preview.get('task', '')
            if not re.fullmatch('[a-z0-9][a-z0-9-]{0,79}', task) or task in tasks:
                raise ValueError('Invalid or duplicate preview task')
            tasks.add(task)
            if preview.get('head_sha') != args.preview_sha:
                raise ValueError('Preview head SHA differs from the reviewed version')
            prefix = f'previews/pr-{args.preview_pr}/{task}/'
            if preview.get('url') != urljoin(args.base_url, prefix):
                raise ValueError('Preview URL differs from the expected site path')
            hashes = preview.get('sha256')
            if not isinstance(hashes, dict) or 'index.html' not in hashes:
                raise ValueError('Preview record lacks an entry HTML hash')
            for file, expected in hashes.items():
                targets.append((prefix + relative_path(file), digest(expected)))
    else:
        hashes = manifest.get('production_sha256')
        if not isinstance(hashes, dict):
            raise ValueError('Production hashes are missing from deployment record')
        for route in dict.fromkeys(args.page or ['.']):
            file = page_path(route)
            if file not in hashes:
                raise ValueError('Page is absent from production record: ' + file)
            targets.append((file, digest(hashes[file])))
    if len(targets) > MAX_FILES:
        raise ValueError('Too many files in selected deployment records')

    result = {'checked_at': datetime.now(timezone.utc).isoformat(), 'base_url': args.base_url,
              'mode': 'preview' if args.preview_pr is not None else 'production',
              'main_sha': main_sha, 'files': [], 'ok': True}
    if args.preview_pr is not None:
        result.update(preview_pr=args.preview_pr, preview_sha=args.preview_sha)
    for file, expected in targets:
        body, record = fetch(public_url(args.base_url, file), args.timeout)
        actual = hashlib.sha256(body).hexdigest()
        record.update(file=file, sha256=actual, expected_sha256=expected,
                      content_matches_manifest=actual == expected)
        if file.endswith('.html') and record['content_type'] != 'text/html':
            raise ValueError('Expected HTML content type: ' + file)
        record['ok'] = actual == expected
        if args.local_root:
            target = (args.local_root / file).resolve()
            if not target.is_relative_to(args.local_root.resolve()):
                raise ValueError('Local target escapes --local-root')
            record['content_matches_local'] = target.read_bytes() == body
            record['ok'] = record['ok'] and record['content_matches_local']
        result['files'].append(record)
        result['ok'] = result['ok'] and record['ok']
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', required=True, help='HTTP(S) site URL ending in /')
    parser.add_argument('--main-sha', help='Expected production source SHA, required for formal checks')
    parser.add_argument('--page', action='append', help='Formal HTML file or directory; repeatable')
    parser.add_argument('--local-root', type=Path, help='Optional formal output directory for byte comparison')
    parser.add_argument('--preview-pr', type=int)
    parser.add_argument('--preview-sha', help='Expected PR head SHA')
    parser.add_argument('--task', help='Optional preview task to select within the PR')
    parser.add_argument('--timeout', type=float, default=15)
    parser.add_argument('--output', type=Path, help='Optional JSON check record outside the published tree')
    args = parser.parse_args(argv)
    base = urlsplit(args.base_url)
    if (base.scheme not in {'http', 'https'} or not base.netloc or base.username or base.password
            or base.query or base.fragment or not args.base_url.endswith('/')):
        parser.error('--base-url must be a credential-free HTTP(S) URL ending in /')
    if not 1 <= args.timeout <= 60:
        parser.error('--timeout must be between 1 and 60 seconds')
    for name in ('main_sha', 'preview_sha'):
        value = getattr(args, name)
        if value is not None and not re.fullmatch('[0-9a-f]{40}', value):
            parser.error('--' + name.replace('_', '-') + ' must be a full 40-character SHA')
    if args.preview_pr is not None:
        if args.preview_pr <= 0 or not args.preview_sha:
            parser.error('Preview mode requires positive --preview-pr and --preview-sha')
        if args.local_root or args.page:
            parser.error('Preview output has injected content; --local-root and --page apply to formal checks')
    elif args.preview_sha or args.task or not args.main_sha:
        parser.error('Formal mode requires --main-sha; preview options require --preview-pr')
    if args.local_root and not args.local_root.is_dir():
        parser.error('--local-root must be an existing directory')
    if args.output and args.local_root and args.output.resolve().is_relative_to(args.local_root.resolve()):
        parser.error('--output must be outside --local-root')
    try:
        result = verify(args)
    except (ValueError, TypeError, KeyError, OSError, HTTPError, URLError) as exc:
        result = {'base_url': args.base_url, 'ok': False, 'error': str(exc)}
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding='utf-8')
    sys.stdout.write(encoded)
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
