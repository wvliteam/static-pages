import argparse
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/static-page-publisher/scripts/verify_deployment.py'
SPEC = importlib.util.spec_from_file_location('verify_deployment_full', SCRIPT)
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)

BASE_URL = 'https://example.test/nested/'
MAIN_SHA = 'a' * 40


def sha(data):
    return hashlib.sha256(data).hexdigest()


def make_args(**updates):
    values = {
        'base_url': BASE_URL,
        'main_sha': MAIN_SHA,
        'page': None,
        'all_production': False,
        'local_root': None,
        'preview_pr': None,
        'preview_sha': None,
        'task': None,
        'timeout': 5,
    }
    values.update(updates)
    return argparse.Namespace(**values)


def manifest_for(files):
    return json.dumps({
        'main_sha': MAIN_SHA,
        'production_sha256': {name: sha(data) for name, data in files.items()},
        'previews': [],
    }).encode()


class FullProductionVerificationTests(unittest.TestCase):
    def test_all_production_checks_entry_and_every_dependency(self):
        bodies = {
            'index.html': b'<h1>Current</h1>',
            'assets/site.css': b'body { color: teal }',
            'assets/app.js': b'const ready = true;',
        }
        manifest = manifest_for(bodies)
        requested = []

        def fake_fetch(url, timeout, limit=verifier.MAX_FILE):
            path = urlsplit(url).path
            requested.append(path)
            if path == '/nested/deployment.json':
                return manifest, {'url': url, 'final_url': url, 'http_status': 200,
                                  'content_type': 'application/json'}
            file = 'index.html' if path == '/nested/' else path.removeprefix('/nested/')
            body = bodies[file]
            content_type = 'text/html' if file.endswith('.html') else 'text/plain'
            return body, {'url': url, 'final_url': url, 'http_status': 200,
                          'content_type': content_type}

        with patch.object(verifier, 'fetch', side_effect=fake_fetch):
            result = verifier.verify(make_args(all_production=True))

        self.assertTrue(result['ok'])
        self.assertEqual([entry['file'] for entry in result['files']], sorted(bodies))
        self.assertEqual(len(requested), 1 + len(bodies))
        self.assertEqual(set(requested[1:]), {'/nested/', '/nested/assets/site.css',
                                               '/nested/assets/app.js'})
        self.assertTrue(all(entry['errors'] == [] for entry in result['files']))

    def test_independent_network_mime_hash_and_local_errors_are_aggregated(self):
        bodies = {
            'index.html': b'<h1>Current</h1>',
            'assets/missing.css': b'expected CSS',
            'assets/app.js': b'expected JS',
            'assets/logo.svg': b'expected logo',
        }
        manifest = manifest_for(bodies)
        requested = []
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        local_root = Path(temporary.name)
        (local_root / 'assets').mkdir()
        (local_root / 'index.html').write_bytes(bodies['index.html'])
        (local_root / 'assets/app.js').write_bytes(b'expected JS')
        (local_root / 'assets/logo.svg').write_bytes(b'different local logo')

        def fake_fetch(url, timeout, limit=verifier.MAX_FILE):
            path = urlsplit(url).path
            requested.append(path)
            if path == '/nested/deployment.json':
                return manifest, {'url': url, 'final_url': url, 'http_status': 200,
                                  'content_type': 'application/json'}
            file = 'index.html' if path == '/nested/' else path.removeprefix('/nested/')
            if file == 'assets/missing.css':
                raise URLError('simulated missing asset')
            if file == 'index.html':
                return bodies[file], {'url': url, 'final_url': url, 'http_status': 200,
                                       'content_type': 'text/plain'}
            if file == 'assets/app.js':
                return b'wrong JS bytes', {'url': url, 'final_url': url, 'http_status': 200,
                                           'content_type': 'text/javascript'}
            return bodies[file], {'url': url, 'final_url': url, 'http_status': 200,
                                  'content_type': 'image/svg+xml'}

        with patch.object(verifier, 'fetch', side_effect=fake_fetch):
            result = verifier.verify(make_args(all_production=True, local_root=local_root))

        self.assertFalse(result['ok'])
        records = {entry['file']: entry for entry in result['files']}
        self.assertEqual(set(records), set(bodies))
        self.assertTrue(any('content type' in error.lower()
                            for error in records['index.html']['errors']))
        self.assertTrue(any('simulated missing asset' in error
                            for error in records['assets/missing.css']['errors']))
        self.assertTrue(any('manifest' in error.lower()
                            for error in records['assets/app.js']['errors']))
        self.assertTrue(any('local file' in error.lower()
                            for error in records['assets/logo.svg']['errors']))
        self.assertEqual(len(requested), 1 + len(bodies))
        self.assertFalse(records['assets/missing.css']['ok'])
        self.assertFalse(records['assets/logo.svg']['content_matches_local'])

    def test_page_mode_still_verifies_only_selected_entry_html(self):
        bodies = {
            'index.html': b'<h1>Home</h1>',
            'reports/daily/index.html': b'<h1>Daily</h1>',
            'assets/site.css': b'body{}',
        }
        manifest = manifest_for(bodies)
        requested = []

        def fake_fetch(url, timeout, limit=verifier.MAX_FILE):
            path = urlsplit(url).path
            requested.append(path)
            if path == '/nested/deployment.json':
                return manifest, {'url': url, 'final_url': url, 'http_status': 200,
                                  'content_type': 'application/json'}
            body = bodies['reports/daily/index.html']
            return body, {'url': url, 'final_url': url, 'http_status': 200,
                          'content_type': 'text/html'}

        with patch.object(verifier, 'fetch', side_effect=fake_fetch):
            result = verifier.verify(make_args(page=['reports/daily/']))

        self.assertTrue(result['ok'])
        self.assertEqual([entry['file'] for entry in result['files']],
                         ['reports/daily/index.html'])
        self.assertEqual(requested, ['/nested/deployment.json', '/nested/reports/daily/'])

    def test_page_and_all_production_are_mutually_exclusive(self):
        argv = ['verify_deployment.py', '--base-url', BASE_URL, '--main-sha', MAIN_SHA,
                '--page', '.', '--all-production']
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(sys, 'argv', argv), redirect_stdout(stdout), redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as raised:
                verifier.main()
        self.assertEqual(raised.exception.code, 2)
        self.assertIn('not allowed with argument', stderr.getvalue())


if __name__ == '__main__':
    unittest.main()
