import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pages_builder', ROOT / 'scripts/build_pages.py')
pages = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pages)
HTML = b'<!doctype html><html><head><title>Report</title></head><body><h1>Report</h1></body></html>'


def archive(files, link=False):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as tar:
        for name, content in files.items():
            member = tarfile.TarInfo('repo-sha/' + name)
            member.size = len(content)
            if link:
                member.type = tarfile.SYMTYPE
                member.linkname = '/etc/passwd'
            tar.addfile(member, io.BytesIO(content))
    return buffer.getvalue()


def pull(number, state='open', repository='owner/site'):
    return {'number': number, 'state': state, 'base': {'ref': 'main'},
            'head': {'repo': {'full_name': repository}, 'ref': f'preview/task-{number}',
                     'sha': str(number) * 40}}


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'docs/reports/published').mkdir(parents=True)
        (self.root / 'docs/index.html').write_bytes(HTML)
        (self.root / 'docs/reports/published/index.html').write_bytes(HTML)

    def build(self, pulls, loader):
        output = self.root / ('build-' + str(len(list(self.root.glob('build-*')))))
        with patch.object(pages, 'git', return_value=''):
            manifest = pages.assemble(self.root, output, pulls, 'owner/site', loader,
                                      'a' * 40, 'https://owner.github.io/site/')
        return output, manifest

    def test_base_url_configuration_matches_preview_manifest(self):
        self.assertEqual(pages.site_base_url(self.root, 'owner/site'), 'https://owner.github.io/site/')
        self.assertEqual(pages.site_base_url(self.root, 'owner/owner.github.io'), 'https://owner.github.io/')
        (self.root / 'docs/CNAME').write_text('pages.example.test')
        base = pages.site_base_url(self.root, 'owner/site')
        self.assertEqual(base, 'https://pages.example.test/')
        self.assertEqual(pages.site_base_url(self.root, 'owner/site', 'https://test.example/prefix'),
                         'https://test.example/prefix/')
        with patch.object(pages, 'git', return_value=''):
            result = pages.assemble(self.root, self.root / 'custom-site', [pull(1)], 'owner/site',
                lambda sha: archive({'artifacts/task/public/index.html': HTML}), 'a' * 40, base)
        self.assertEqual(result['previews'][0]['url'], 'https://pages.example.test/previews/pr-1/task/')
        with self.assertRaises(ValueError):
            pages.site_base_url(self.root, 'owner/site', 'https://user:password@example.test/')

    def test_multiple_previews_leave_production_byte_identical(self):
        def load(sha):
            return archive({'artifacts/task/public/index.html': HTML,
                            'artifacts/task/public/style.css': b'body{}',
                            'artifacts/task/raw.txt': b'not public',
                            'scripts/untrusted.py': b'raise RuntimeError()'})
        output, manifest = self.build([pull(1), pull(2)], load)
        self.assertEqual((output / 'index.html').read_bytes(), HTML)
        self.assertEqual((output / 'reports/published/index.html').read_bytes(), HTML)
        self.assertEqual(len(manifest['previews']), 2)
        page = (output / 'previews/pr-1/task/index.html').read_text()
        self.assertIn('noindex,nofollow,noarchive', page)
        self.assertIn('尚未正式收录', page)
        self.assertEqual((output / 'previews/pr-1/task/style.css').read_bytes(), b'body{}')
        self.assertFalse(any(p.name == 'raw.txt' for p in output.rglob('*')))
        self.assertFalse((output / 'scripts').exists())

    def test_closed_pr_is_removed_while_other_preview_survives(self):
        loader = lambda sha: archive({'artifacts/task/public/index.html': HTML})
        output, manifest = self.build([pull(1, 'closed'), pull(2)], loader)
        self.assertFalse((output / 'previews/pr-1').exists())
        self.assertTrue((output / 'previews/pr-2/task/index.html').is_file())
        self.assertEqual([p['pr'] for p in manifest['previews']], [2])

    def test_fork_and_non_preview_branches_are_not_read(self):
        wrong = pull(2); wrong['head']['ref'] = 'feature/other'
        output, manifest = self.build([pull(1, repository='outside/fork'), wrong],
                                      lambda sha: self.fail('Unexpected archive download'))
        self.assertEqual(manifest['previews'], [])

    def test_missing_entry_waits_without_breaking_formal_site(self):
        output, manifest = self.build([pull(1)], lambda sha: archive({'artifacts/task/public/data.json': b'{}'}))
        self.assertEqual(manifest['previews'], [])
        self.assertEqual(len(manifest['skipped']), 1)
        self.assertEqual((output / 'index.html').read_bytes(), HTML)

    def test_traversal_symlink_and_duplicate_paths_rejected(self):
        for data in [archive({'artifacts/task/public/../../outside.html': HTML}),
                     archive({'artifacts/task/public/index.html': b''}, link=True)]:
            with self.subTest(data=data[:20]), self.assertRaises(ValueError):
                pages.archive_files(data)

    def test_reserved_production_paths_and_symlinks_rejected(self):
        (self.root / 'docs/previews').mkdir()
        with self.assertRaises(ValueError): self.build([], lambda sha: b'')
        (self.root / 'docs/previews').rmdir()
        (self.root / 'docs/link').symlink_to(self.root / 'docs/index.html')
        with self.assertRaises(ValueError): self.build([], lambda sha: b'')

    def test_branch_head_change_updates_preview_version(self):
        preview = pull(1)
        _, old = self.build([preview], lambda sha: archive({'artifacts/task/public/index.html': HTML}))
        preview['head']['sha'] = 'b' * 40
        _, new = self.build([preview], lambda sha: archive({'artifacts/task/public/index.html': HTML}))
        self.assertNotEqual(old['previews'][0]['sha256'], new['previews'][0]['sha256'])
        self.assertEqual(new['previews'][0]['head_sha'], 'b' * 40)

    def test_approved_move_does_not_publish_artifacts_from_main(self):
        (self.root / 'docs/reports/new').mkdir()
        (self.root / 'docs/reports/new/index.html').write_bytes(HTML)
        output, manifest = self.build([], lambda sha: b'')
        self.assertEqual((output / 'reports/new/index.html').read_bytes(), HTML)
        self.assertFalse((output / 'artifacts').exists())
        self.assertEqual(manifest['previews'], [])

    def test_size_limit(self):
        with patch.object(pages, 'MAX_PREVIEW', 2), self.assertRaises(ValueError):
            pages.archive_files(archive({'artifacts/task/public/index.html': HTML}))


if __name__ == '__main__':
    unittest.main()
