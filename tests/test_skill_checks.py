"""Exercise standalone creator checks and deployment verification independently."""
from contextlib import contextmanager
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest


ROOT = Path(__file__).resolve().parents[1]
LOCAL_CHECK = ROOT / 'scripts/check_static_html.py'
REMOTE_CHECK = ROOT / 'scripts/verify_deployment.py'
HTML = b'<!doctype html><html><head><title>Example</title><meta name="viewport" content="width=device-width"></head><body><h1 id="main">Example</h1></body></html>'


def sha(content):
    return hashlib.sha256(content).hexdigest()


def command(script, *args):
    return subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True)


@contextmanager
def deployed_site():
    files = {}
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            value = files.get(self.path)
            if value is None:
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header('Content-Type', 'application/json' if self.path.endswith('.json') else 'text/html')
            self.end_headers()
            self.wfile.write(value)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/nested/', files, requests
    finally:
        server.shutdown()
        server.server_close()


class LocalArtifactChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'arbitrary-output'
        self.root.mkdir()
        self.index = self.root / 'index.html'
        self.index.write_bytes(HTML)

    def check(self, *extra):
        return command(LOCAL_CHECK, '--root', str(self.root), *extra)

    def test_independent_output_directory_and_source_hash(self):
        result = self.check('--require-single-file')
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data['pages'][0]['sha256'], sha(HTML))
        self.assertNotIn('remote', data['pages'][0])
        self.assertFalse((self.root / '.git').exists())

    def test_external_citation_allowed_but_external_runtime_resource_fails(self):
        self.index.write_bytes(HTML.replace(b'</body>', b'<a href="https://example.invalid/source">Source</a></body>'))
        self.assertEqual(self.check('--require-single-file').returncode, 0)
        self.index.write_bytes(HTML.replace(b'</head>', b'<script src="https://example.invalid/runtime.js"></script></head>'))
        self.assertEqual(self.check('--require-single-file').returncode, 1)

    def test_duplicate_id_and_missing_anchor_fail(self):
        self.index.write_bytes(HTML.replace(b'</body>', b'<p id="main">Duplicate</p><a href="#missing">Missing</a></body>'))
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(len(json.loads(result.stdout)['pages'][0]['issues']), 2)

    def test_nested_base_path_and_homepage_entry(self):
        target = self.root / 'pages/example/index.html'
        target.parent.mkdir(parents=True)
        target.write_bytes(HTML)
        self.index.write_bytes(HTML.replace(b'</body>', b'<a href="/project/pages/example/">Page</a></body>'))
        result = self.check('--page', 'pages/example', '--base-path', '/project/', '--require-homepage-link')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.check('--base-path', '/wrong/').returncode, 1)

    def test_multifile_resources_and_path_escape(self):
        (self.root / 'style.css').write_text('body{}')
        self.index.write_bytes(HTML.replace(b'</head>', b'<link rel="stylesheet" href="style.css"></head>'))
        self.assertEqual(self.check().returncode, 0)
        self.assertEqual(self.check('--require-single-file').returncode, 1)
        self.assertEqual(self.check('--page', '../outside.html').returncode, 1)
        self.assertEqual(self.check('--output', str(self.index)).returncode, 2)


class DeploymentChecks(unittest.TestCase):
    def production(self, files, body=HTML):
        files['/nested/deployment.json'] = json.dumps({
            'main_sha': 'a' * 40, 'production_sha256': {'index.html': sha(HTML)}, 'previews': []
        }).encode()
        files['/nested/'] = body

    def test_formal_sha_hash_and_optional_local_copy(self):
        with deployed_site() as (base, files, requests), tempfile.TemporaryDirectory() as local:
            self.production(files)
            Path(local, 'index.html').write_bytes(HTML)
            result = command(REMOTE_CHECK, '--base-url', base, '--main-sha', 'a' * 40,
                             '--local-root', local)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(json.loads(result.stdout)['files'][0]['content_matches_local'])
            self.assertEqual(requests, ['/nested/deployment.json', '/nested/'])

    def test_stale_main_fails_before_page_download(self):
        with deployed_site() as (base, files, requests):
            self.production(files)
            result = command(REMOTE_CHECK, '--base-url', base, '--main-sha', 'b' * 40)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(requests, ['/nested/deployment.json'])

    def test_http_200_wrong_html_is_not_a_success(self):
        with deployed_site() as (base, files, _):
            self.production(files, b'<h1>Old page</h1>')
            result = command(REMOTE_CHECK, '--base-url', base, '--main-sha', 'a' * 40)
            self.assertEqual(result.returncode, 1)
            self.assertFalse(json.loads(result.stdout)['files'][0]['content_matches_manifest'])

    def test_preview_uses_generated_hash_and_exact_head(self):
        with deployed_site() as (base, files, _):
            generated = HTML.replace(b'<body>', b'<body><aside>Preview banner</aside>')
            files['/nested/deployment.json'] = json.dumps({
                'main_sha': 'a' * 40, 'production_sha256': {}, 'previews': [{
                    'pr': 7, 'task': 'example', 'head_sha': 'b' * 40,
                    'url': base + 'previews/pr-7/example/',
                    'sha256': {'index.html': sha(generated)}}]}).encode()
            files['/nested/previews/pr-7/example/'] = generated
            args = ('--base-url', base, '--preview-pr', '7', '--task', 'example')
            result = command(REMOTE_CHECK, *args, '--preview-sha', 'b' * 40)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotEqual(sha(HTML), json.loads(result.stdout)['files'][0]['sha256'])
            self.assertEqual(command(REMOTE_CHECK, *args, '--preview-sha', 'c' * 40).returncode, 1)
            self.assertEqual(command(REMOTE_CHECK, *args, '--preview-sha', 'b' * 40,
                                     '--local-root', str(ROOT / 'docs')).returncode, 2)

    def test_missing_preview_and_unsafe_manifest_path_fail(self):
        with deployed_site() as (base, files, _):
            self.production(files)
            result = command(REMOTE_CHECK, '--base-url', base, '--preview-pr', '7', '--preview-sha', 'b' * 40)
            self.assertEqual(result.returncode, 1)
            manifest = json.loads(files['/nested/deployment.json'])
            manifest['previews'] = [{'pr': 7, 'task': 'example', 'head_sha': 'b' * 40,
                                    'url': base + 'previews/pr-7/example/',
                                    'sha256': {'index.html': sha(HTML), '../outside.html': sha(HTML)}}]
            files['/nested/deployment.json'] = json.dumps(manifest).encode()
            result = command(REMOTE_CHECK, '--base-url', base, '--preview-pr', '7', '--preview-sha', 'b' * 40)
            self.assertEqual(result.returncode, 1)


if __name__ == '__main__':
    unittest.main()
