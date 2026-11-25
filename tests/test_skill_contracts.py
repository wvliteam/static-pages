import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / 'tests/fixtures/skill_scenarios.json'


class SkillContractTests(unittest.TestCase):
    def test_regression_scenarios_have_observable_expectations(self):
        scenarios = json.loads(SCENARIOS.read_text(encoding='utf-8'))
        self.assertGreaterEqual(len(scenarios), 5)
        ids = [item['id'] for item in scenarios]
        self.assertEqual(len(ids), len(set(ids)))
        for scenario in scenarios:
            with self.subTest(scenario=scenario.get('id')):
                self.assertTrue(scenario.get('skill'))
                self.assertTrue(scenario.get('request'))
                self.assertGreaterEqual(len(scenario.get('expected', [])), 2)

    def test_builder_and_publisher_documents_keep_handoff_contract(self):
        builder = (ROOT / 'skills/static-page-builder/SKILL.md').read_text(encoding='utf-8')
        publisher = (ROOT / 'skills/static-page-publisher/SKILL.md').read_text(encoding='utf-8')
        pages = (ROOT / 'skills/static-page-publisher/references/github-pages.md').read_text(encoding='utf-8')
        self.assertIn('artifact_manifest', builder)
        self.assertIn('verify_artifact_manifest.py', publisher)
        self.assertIn('compare_promotion.py', publisher)
        self.assertIn('static-pages-candidate', publisher)
        self.assertIn('static-pages-main-ready', publisher)
        self.assertIn('--all-production', publisher)
        self.assertIn('preview-sha', pages)


if __name__ == '__main__':
    unittest.main()
