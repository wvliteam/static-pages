"""The site validates its pinned tools without a FlowKit checkout or network."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class VendoredChecksTests(unittest.TestCase):
    def test_snapshot_identity_and_file_bytes(self):
        record = json.loads((ROOT / 'scripts/flowkit-checks.json').read_text())
        self.assertEqual(record['schema_version'], 1)
        self.assertEqual(set(record['files']), {'check_static_html.py', 'verify_deployment.py',
                                             'verify_artifact_manifest.py', 'compare_promotion.py'})
        version = hashlib.sha256(json.dumps(record['files'], sort_keys=True).encode()).hexdigest()
        self.assertEqual(record['version'], version)
        for name, item in record['files'].items():
            with self.subTest(name=name):
                self.assertEqual(hashlib.sha256((ROOT / 'scripts' / name).read_bytes()).hexdigest(),
                                 item['sha256'])
