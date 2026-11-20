#!/usr/bin/env python3
"""Store the assembled site in generated gh-pages; deploy in the same workflow.

The workflow uses upload-pages-artifact + deploy-pages, so it does not depend on
a GITHUB_TOKEN push triggering a second Pages build.
"""
import argparse
import os
from pathlib import Path
import subprocess


def run(*args, cwd):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', type=Path, required=True)
    args = parser.parse_args()
    site = args.site.resolve()
    if not (site / 'deployment.json').is_file() or not (site / 'index.html').is_file():
        parser.error('Expected a complete assembled site')
    repository = os.environ['GITHUB_REPOSITORY']
    # Git invokes gh's credential helper; never print or persist a token.
    remote = 'https://github.com/' + repository + '.git'
    run('git', 'init', '-b', 'gh-pages', cwd=site)
    run('git', 'remote', 'add', 'origin', remote, cwd=site)
    probe = subprocess.run(
        ['git', '-c', 'credential.helper=', '-c', 'credential.helper=!gh auth git-credential',
         'ls-remote', '--exit-code', 'origin', 'refs/heads/gh-pages'], cwd=site,
        capture_output=True)
    if probe.returncode == 0:
        run('git', '-c', 'credential.helper=', '-c', 'credential.helper=!gh auth git-credential',
            'fetch', '--depth=1', 'origin', 'gh-pages', cwd=site)
    elif probe.returncode != 2:
        raise RuntimeError('Could not inspect the generated deployment branch')
    fetched = subprocess.run(['git', 'rev-parse', '--verify', 'FETCH_HEAD'], cwd=site,
                             capture_output=True, text=True)
    if fetched.returncode == 0:
        # Reuse its parent while keeping exactly the newly assembled working tree.
        run('git', 'reset', '--mixed', fetched.stdout.strip(), cwd=site)
    run('git', 'add', '--all', cwd=site)
    diff = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=site)
    if diff.returncode != 0:
        run('git', '-c', 'user.name=github-actions[bot]', '-c',
            'user.email=41898282+github-actions[bot]@users.noreply.github.com',
            'commit', '-m', 'Update production and open PR previews', cwd=site)
        run('git', '-c', 'credential.helper=', '-c', 'credential.helper=!gh auth git-credential',
            'push', 'origin', 'HEAD:gh-pages', cwd=site)
    # Never put the staging Git database into the Pages artifact.
    import shutil
    shutil.rmtree(site / '.git')


if __name__ == '__main__':
    main()
