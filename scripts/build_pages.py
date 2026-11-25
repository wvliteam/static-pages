#!/usr/bin/env python3
"""Assemble main/docs and static artifacts from same-repo preview PRs.

PR scripts are never executed. Archives are read at their exact head SHA, and
only regular files inside artifacts/<task>/public are eligible for previews.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tarfile
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

MAX_ARCHIVE = 50 * 1024 * 1024
MAX_PREVIEW = 20 * 1024 * 1024
MAX_FILES = 1000
PREVIEW_CSS = '''<style data-static-preview="true">
.static-preview-banner{position:relative;z-index:10000;background:#fff4d6;color:#503a10;
padding:12px 20px;font:14px/1.6 system-ui,sans-serif;border-bottom:1px solid #d5ad4d}
.static-preview-banner a{color:#503a10;text-decoration:underline}
@media print{.static-preview-banner{print-color-adjust:exact}}
</style>'''


def git(*args: str) -> str:
    return subprocess.run(['git', *args], check=True, capture_output=True, text=True).stdout.strip()


class GitHub:
    def __init__(self, repository: str, token: str):
        self.repository, self.token = repository, token

    def request(self, path: str, limit: int = MAX_ARCHIVE) -> bytes:
        request = Request('https://api.github.com/' + path, headers={
            'Authorization': 'Bearer ' + self.token,
            'Accept': 'application/vnd.github+json',
            'User-Agent': 'static-pages-publisher',
        })
        with urlopen(request, timeout=30) as response:
            content = response.read(limit + 1)
        if len(content) > limit:
            raise ValueError('GitHub response exceeds the publisher size limit')
        return content

    def pulls(self) -> list[dict]:
        result = []
        for page in range(1, 11):
            chunk = json.loads(self.request(
                f'repos/{self.repository}/pulls?state=open&base=main&per_page=100&page={page}'))
            result.extend(chunk)
            if len(chunk) < 100:
                return result
        raise ValueError('Too many open PRs; refusing an incomplete preview list')

    def archive(self, sha: str) -> bytes:
        if not re.fullmatch(r'[0-9a-f]{40}', sha):
            raise ValueError('Invalid preview commit SHA')
        return self.request(f'repos/{self.repository}/tarball/{sha}')


def eligible(pull: dict, repository: str) -> bool:
    return (pull.get('state') == 'open'
            and pull.get('base', {}).get('ref') == 'main'
            and (pull.get('head', {}).get('repo') or {}).get('full_name') == repository
            and pull['head'].get('ref', '').startswith('preview/'))


def preview_html(source: bytes, number: int, task: str, sha: str) -> bytes:
    text = source.decode('utf-8')
    if not all(re.search(r'<' + name + r'\b[^>]*>', text, re.I) for name in ('html', 'head', 'body')):
        raise ValueError('Preview HTML must contain html, head and body elements')
    if 'data-static-preview=' in text:
        raise ValueError('Store clean HTML in the source branch; banners are generated')
    # Replace existing robots instructions so a copied index directive cannot win.
    text = re.sub(r'<meta\b(?=[^>]*\bname\s*=\s*[\"\']?(?:robots|googlebot)\b)[^>]*>', '', text, flags=re.I)
    head = '<meta name="robots" content="noindex,nofollow,noarchive">' + PREVIEW_CSS
    text = re.sub(r'(<head\b[^>]*>)', lambda m: m[0] + head, text, count=1, flags=re.I)
    banner = (f'<aside class="static-preview-banner" data-static-preview="true" aria-label="预览状态">'
              f'<strong>预览稿 · 尚未正式收录</strong> · PR #{number} · '
              f'{html.escape(task)} · 版本 {sha[:7]}。'
              '<a href="https://github.com/' + os.environ.get('GITHUB_REPOSITORY', 'wvliteam/static-pages')
              + f'/pull/{number}">查看审阅记录</a></aside>')
    return re.sub(r'(<body\b[^>]*>)', lambda m: m[0] + banner, text, count=1, flags=re.I).encode('utf-8')


def archive_files(archive: bytes) -> dict[str, dict[str, bytes]]:
    tasks: dict[str, dict[str, bytes]] = {}
    total, count = 0, 0
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as tar:
        seen = set()
        for member in tar:
            parts = PurePosixPath(member.name).parts
            # Strip GitHub's one top-level archive directory.
            if len(parts) < 5 or parts[1] != 'artifacts' or parts[3] != 'public':
                continue
            task = parts[2]
            if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,79}', task):
                raise ValueError('Preview task must be a lowercase slug')
            relative = PurePosixPath(*parts[4:])
            if any(p in {'.', '..'} or p.startswith('.') or '\\' in p for p in relative.parts):
                raise ValueError('Unsafe archive path')
            if member.isdir():
                continue
            if not member.isfile() or member.issym() or member.islnk():
                raise ValueError('Only regular preview files are accepted')
            key = task + '/' + str(relative)
            if key in seen:
                raise ValueError('Duplicate preview path')
            seen.add(key)
            total += member.size
            count += 1
            if total > MAX_PREVIEW or count > MAX_FILES:
                raise ValueError('Preview exceeds size or file-count limit')
            stream = tar.extractfile(member)
            if stream is None:
                raise ValueError('Missing archive content')
            tasks.setdefault(task, {})[str(relative)] = stream.read()
    return tasks


def copy_production(source: Path, target: Path):
    if not (source / 'index.html').is_file():
        raise ValueError('main/docs/index.html is required')
    for path in source.rglob('*'):
        if path.is_symlink():
            raise ValueError('Production must not contain symbolic links')
    for reserved in ('previews', 'artifacts', 'deployment.json'):
        if (source / reserved).exists():
            raise ValueError('Reserved deployment path in main/docs: ' + reserved)
    shutil.copytree(source, target)


def assemble(root: Path, output: Path, pulls: list[dict], repository: str,
             archive_loader, main_sha: str, base_url: str) -> dict:
    if output.exists():
        raise ValueError('Output must be a new directory')
    # main may retain an empty ignored working folder, but no tracked artifacts.
    if git('ls-files', 'artifacts'):
        raise ValueError('main must not contain tracked draft artifacts')
    copy_production(root / 'docs', output)
    production = {str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in output.rglob('*') if p.is_file()}
    manifest = {'main_sha': main_sha, 'production_sha256': production, 'previews': [], 'skipped': []}
    for pull in sorted(pulls, key=lambda p: p['number']):
        if not eligible(pull, repository):
            continue
        number, sha = pull['number'], pull['head']['sha']
        tasks = archive_files(archive_loader(sha))
        for task, files in sorted(tasks.items()):
            if 'index.html' not in files:
                manifest['skipped'].append({'pr': number, 'task': task, 'reason': 'No index.html yet'})
                continue
            directory = output / 'previews' / f'pr-{number}' / task
            directory.mkdir(parents=True)
            hashes = {}
            for name, content in files.items():
                path = directory / name
                path.parent.mkdir(parents=True, exist_ok=True)
                if path.suffix.lower() == '.html':
                    content = preview_html(content, number, task, sha)
                path.write_bytes(content)
                hashes[name] = hashlib.sha256(content).hexdigest()
            manifest['previews'].append({'pr': number, 'branch': pull['head']['ref'], 'head_sha': sha,
                'task': task, 'url': base_url + f'previews/pr-{number}/{task}/', 'sha256': hashes})
    (output / '.nojekyll').touch()
    (output / 'deployment.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    return manifest


def site_base_url(root: Path, repository: str, explicit: str | None = None) -> str:
    if explicit:
        value = explicit.rstrip('/') + '/'
    elif (root / 'docs/CNAME').is_file():
        value = 'https://' + (root / 'docs/CNAME').read_text().strip() + '/'
    else:
        owner, name = repository.split('/')
        value = f'https://{owner}.github.io/' + ('' if name.lower() == f'{owner}.github.io'.lower() else quote(name) + '/')
    parsed = urlsplit(value)
    if (parsed.scheme not in {'http', 'https'} or not parsed.netloc or parsed.username
            or parsed.password or parsed.query or parsed.fragment):
        raise ValueError('Expected a credential-free HTTP(S) site base URL')
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path.cwd()
    repository = os.environ['GITHUB_REPOSITORY']
    base_url = site_base_url(root, repository, os.environ.get('STATIC_PAGES_BASE_URL'))
    client = GitHub(repository, os.environ['GH_TOKEN'])
    manifest = assemble(root, args.output, client.pulls(), repository, client.archive,
                        git('rev-parse', 'HEAD'), base_url)
    summary = ['## Pages deployment', '', f'Production: {base_url}',
               f'Main commit: `{manifest["main_sha"]}`', '', '### Open PR previews', '']
    for preview in manifest['previews']:
        summary.append(f'- PR #{preview["pr"]}: [{preview["task"]}]({preview["url"]}) '
                       f'(`{preview["head_sha"][:7]}`)')
    if not manifest['previews']:
        summary.append('No active previews.')
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as stream:
            stream.write('\n'.join(summary) + '\n')
    print(json.dumps({'main_sha': manifest['main_sha'], 'previews': manifest['previews'],
                      'skipped': manifest['skipped']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
