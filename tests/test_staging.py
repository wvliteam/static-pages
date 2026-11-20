"""Exercise generated-branch updates against a local bare Git repository."""
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/stage_pages.py'


class GeneratedBranchTests(unittest.TestCase):
    @unittest.skipIf(shutil.which('andronix'),
                     'Local bare Git transport fails on this Andronix runtime; exercised on Linux CI')
    def test_repeated_snapshot_updates_and_preview_cleanup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            remote = root / 'site.git'
            subprocess.run(['git', 'init', '--bare', str(remote)], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            env = os.environ.copy()
            env.update(GITHUB_REPOSITORY='publisher/test-site', GIT_CONFIG_COUNT='1',
                       GIT_CONFIG_KEY_0=f'url.{remote.as_uri()}.insteadOf',
                       GIT_CONFIG_VALUE_0='https://github.com/publisher/test-site.git')

            def stage(number, preview):
                site = root / f'output-{number}'
                site.mkdir()
                (site / 'index.html').write_text('<h1>Formal site</h1>')
                (site / 'deployment.json').write_text(json.dumps({'main_sha': 'a' * 40}))
                if preview:
                    (site / 'previews/pr-1').mkdir(parents=True)
                    (site / 'previews/pr-1/index.html').write_text('<h1>Draft</h1>')
                result = subprocess.run([sys.executable, str(SCRIPT), '--site', str(site)],
                                        env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertFalse((site / '.git').exists())
                return subprocess.run(['git', '--git-dir', str(remote), 'rev-parse', 'gh-pages'],
                                      check=True, capture_output=True, text=True).stdout.strip()

            first = stage(1, True)
            unchanged = stage(2, True)
            self.assertEqual(first, unchanged, 'Identical snapshots should not create commits')
            cleaned = stage(3, False)
            self.assertNotEqual(first, cleaned)
            tree = subprocess.run(['git', '--git-dir', str(remote), 'ls-tree', '-r',
                                   '--name-only', 'gh-pages'], check=True, capture_output=True,
                                  text=True).stdout
            self.assertIn('index.html', tree)
            self.assertNotIn('previews/', tree)
            formal = subprocess.run(['git', '--git-dir', str(remote), 'show',
                                     'gh-pages:index.html'], check=True, capture_output=True,
                                    text=True).stdout
            self.assertEqual(formal, '<h1>Formal site</h1>')


if __name__ == '__main__':
    unittest.main()
