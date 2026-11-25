import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
VERIFY = ROOT / 'scripts/verify_artifact_manifest.py'
COMPARE = ROOT / 'scripts/compare_promotion.py'
spec = importlib.util.spec_from_file_location('verify_artifact_manifest', VERIFY)
manifest = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = manifest
spec.loader.exec_module(manifest)


def run(script, *args):
    return subprocess.run([sys.executable, str(script), *map(str, args)],
                          capture_output=True, text=True)


class ArtifactManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'public'
        self.root.mkdir()
        (self.root / 'index.html').write_text('<h1>ok</h1>', encoding='utf-8')
        (self.root / 'assets').mkdir()
        (self.root / 'assets/app.js').write_text('console.log(1)', encoding='utf-8')
        self.manifest_path = self.base / 'check.json'
        self.write_manifest()

    def write_manifest(self):
        rows = manifest.file_rows(self.root)
        value = {'artifact_manifest': {'files': rows,
                                       'bundle_sha256': manifest.bundle_digest(rows)}}
        self.manifest_path.write_text(json.dumps(value), encoding='utf-8')

    def test_matches_complete_multifile_snapshot(self):
        result = run(VERIFY, '--root', self.root, '--manifest', self.manifest_path)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(json.loads(result.stdout)['ok'])

    def test_detects_added_missing_changed_and_modified_manifest(self):
        cases = [
            ('changed', lambda: (self.root / 'index.html').write_text('changed')),
            ('missing', lambda: (self.root / 'assets/app.js').unlink()),
            ('added', lambda: (self.root / 'extra.txt').write_text('extra')),
        ]
        for status, mutate in cases:
            with self.subTest(status=status):
                self.write_manifest()
                mutate()
                result = run(VERIFY, '--root', self.root, '--manifest', self.manifest_path)
                self.assertEqual(result.returncode, 1)
                records = json.loads(result.stdout)['files']
                self.assertIn(status, {item['status'] for item in records})

    def test_rejects_manifest_inside_artifact_root_and_symlinks(self):
        inside = self.root / 'manifest.json'
        inside.write_text('{}')
        result = run(VERIFY, '--root', self.root, '--manifest', inside)
        self.assertEqual(result.returncode, 1)
        inside.unlink()
        (self.root / 'link').symlink_to(self.root / 'index.html')
        result = run(VERIFY, '--root', self.root, '--manifest', self.manifest_path)
        self.assertEqual(result.returncode, 1)


class PromotionComparisonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / 'source'
        self.target = self.base / 'target'
        self.source.mkdir(); self.target.mkdir()
        (self.source / 'index.html').write_text('same')
        (self.source / 'asset.css').write_text('body{}')
        (self.target / 'index.html').write_text('same')
        (self.target / 'asset.css').write_text('body{}')

    def test_clean_move_has_identical_bundle_digest(self):
        result = run(COMPARE, '--source-root', self.source, '--target-root', self.target)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        data = json.loads(result.stdout)
        self.assertTrue(data['ok'])
        self.assertEqual(data['source_bundle_sha256'], data['target_bundle_sha256'])

    def test_reports_missing_added_and_modified_paths(self):
        (self.target / 'asset.css').write_text('body{color:red}')
        (self.target / 'extra.js').write_text('')
        (self.source / 'remove.js').write_text('')
        result = run(COMPARE, '--source-root', self.source, '--target-root', self.target)
        self.assertEqual(result.returncode, 1)
        statuses = {item['status'] for item in json.loads(result.stdout)['files']}
        self.assertEqual(statuses, {'same', 'modified', 'added_to_target', 'missing_from_target'})

    def test_output_cannot_mutate_compared_trees(self):
        before = {root: manifest.file_rows(root) for root in (self.source, self.target)}
        for root in (self.source, self.target):
            for name in ('index.html', 'report.json'):
                with self.subTest(root=root, name=name):
                    result = run(COMPARE, '--source-root', self.source,
                                 '--target-root', self.target, '--output', root / name)
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn('outside the source and target trees', result.stderr)
                    for tree in (self.source, self.target):
                        self.assertEqual(manifest.file_rows(tree), before[tree])

    def test_approved_preview_sha_and_builder_manifest_are_bound(self):
        repo = self.base / 'repo'
        repo.mkdir()
        def git(*args):
            return subprocess.run(['git', *args], cwd=repo, check=True,
                                  capture_output=True, text=True).stdout.strip()
        git('init', '-q', '-b', 'preview')
        git('config', 'user.name', 'Test')
        git('config', 'user.email', 'test@example.invalid')
        source = repo / 'artifacts/demo/public'
        source.mkdir(parents=True)
        (source / 'index.html').write_text('same')
        (source / 'asset.css').write_text('body{}')
        rows = manifest.file_rows(source)
        check = repo / 'scratch/check.json'
        check.parent.mkdir()
        check.write_text(json.dumps({'artifact_manifest': {
            'files': rows, 'bundle_sha256': manifest.bundle_digest(rows)}}))
        git('add', 'artifacts/demo/public')
        git('commit', '-q', '-m', 'Preview')
        sha = git('rev-parse', 'HEAD')
        target = repo / 'docs/pages/demo'
        target.mkdir(parents=True)
        (target / 'index.html').write_text('same')
        (target / 'asset.css').write_text('body{}')

        args = ('--repo-root', repo, '--preview-sha', sha, '--task', 'demo',
                '--manifest', check, '--target-root', target)
        result = run(COMPARE, *args)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data['source_sha'], sha)
        self.assertEqual(data['checked_bundle_sha256'], manifest.bundle_digest(rows))

        for output in (source / 'index.html', target / 'report.json', check):
            with self.subTest(output=output):
                check_before = check.read_bytes()
                result = run(COMPARE, *args, '--output', output)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertEqual(manifest.file_rows(source), rows)
                self.assertEqual(manifest.file_rows(target), rows)
                self.assertEqual(check.read_bytes(), check_before)

        (target / 'asset.css').write_text('changed')
        result = run(COMPARE, *args)
        self.assertEqual(result.returncode, 1)
        self.assertIn('modified', {item['status'] for item in json.loads(result.stdout)['files']})


if __name__ == '__main__':
    unittest.main()
