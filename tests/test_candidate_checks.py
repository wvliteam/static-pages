import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CHECKER = Path(__file__).resolve().parents[1] / "scripts/check_candidate.py"
HTML = ('<!doctype html><html><head><title>Page</title>'
        '<meta name="viewport" content="width=device-width"></head><body>{}</body></html>')
PREVIEW = "artifacts/demo/public/index.html"


class CandidateTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        self.write("docs/index.html", HTML.format('<img src="./cover.svg" alt="">'))
        self.write("docs/cover.svg", "<svg/>")
        self.base = self.commit("Base")
        self.git("switch", "-q", "-c", "topic")

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True,
                              capture_output=True, text=True).stdout.strip()

    def write(self, name, text):
        file = self.root / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text, encoding="utf-8")

    def commit(self, message):
        self.git("add", "--all")
        self.git("commit", "-q", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD")

    def merge(self):
        head = self.git("rev-parse", "HEAD")
        self.git("switch", "-q", "main")
        self.git("merge", "-q", "--no-ff", "-m", "Test merge", head)
        self.candidate = self.git("rev-parse", "HEAD")
        self.event = {"pull_request": {"number": 12, "base": {"ref": "main", "sha": self.base},
                                       "head": {"sha": head}}}

    def check(self, mode="candidate", expected=0):
        self.write("event.json", json.dumps(self.event))
        command = [sys.executable, str(CHECKER), mode, "--event-path", "event.json",
                   "--candidate-sha", self.candidate]
        run = subprocess.run(command, cwd=self.root, capture_output=True, text=True)
        self.assertEqual(run.returncode, expected, run.stdout + run.stderr)
        return json.loads(run.stdout)

    def test_valid_preview_and_merge_readiness_have_independent_results(self):
        self.write(PREVIEW, HTML.format('<a href="/static-pages/previews/pr-12/demo/#x" id="x">Anchor</a>'))
        head = self.commit("Stage preview on a regular branch")
        self.merge()
        result = self.check()
        self.assertEqual(result["head_sha"], head)
        self.assertEqual(result["base_sha"], self.base)
        self.assertEqual(result["tested_merge_sha"], self.candidate)
        self.assertIn("demo", result["previews"])
        self.assertEqual(self.check("main-ready", 1)["tracked_artifacts"], [PREVIEW])

    def test_promoted_candidate_ignores_untracked_drafts(self):
        self.write(PREVIEW, HTML.format("Preview"))
        self.commit("Stage preview")
        self.git("mv", PREVIEW, "docs/promoted.html")
        self.commit("Promote clean source")
        self.merge()
        self.write(PREVIEW, "untracked local draft")
        self.assertIn("promoted.html", self.check()["production_pages"])
        self.assertEqual(self.check("main-ready")["tracked_artifacts"], [])

    def test_previews_are_checked_at_head_even_if_base_supplies_entry(self):
        self.write("artifacts/demo/public/image.svg", "<svg/>")
        self.commit("Preview without entry at head")
        self.git("switch", "-q", "main")
        self.write(PREVIEW, HTML.format("Entry only on base branch"))
        self.base = self.commit("Added independently to base")
        self.git("switch", "-q", "topic")
        self.merge()
        issues = self.check(expected=1)["issues"]
        self.assertIn("index.html is missing", "\n".join(issues))

    def test_checks_html_beyond_preview_entry_and_all_tasks(self):
        self.write(PREVIEW, HTML.format("Valid entry"))
        self.write("artifacts/demo/public/详情.html", HTML.format('<a href="./missing.html">Broken</a>'))
        self.write("artifacts/second/public/index.html", '<title>Not a complete document</title>')
        self.commit("Add two preview tasks")
        self.merge()
        issues = "\n".join(self.check(expected=1)["issues"])
        self.assertIn("详情.html", issues)
        self.assertIn("missing.html", issues)
        self.assertIn("html, head and body", issues)

    def test_resource_deletion_is_reported_from_formal_html_that_references_it(self):
        (self.root / "docs/cover.svg").unlink()
        self.commit("Remove a resource used by the unchanged homepage")
        self.merge()
        issues = "\n".join(self.check(expected=1)["issues"])
        self.assertIn("docs/index.html", issues)
        self.assertIn("cover.svg", issues)

    def assert_archive_failure(self, attribute, message):
        self.write(PREVIEW, HTML.format("$Format:%H$"))
        self.write(".gitattributes", f"{PREVIEW} {attribute}\n")
        self.commit(f"Configure {attribute}")
        self.merge()
        self.assertIn(message, "\n".join(self.check(expected=1)["issues"]))

    def test_git_archive_cannot_silently_drop_preview_files(self):
        self.assert_archive_failure("export-ignore", "different set of files")

    def test_git_archive_cannot_silently_change_preview_files(self):
        self.assert_archive_failure("export-subst", "changed the Git blob")

    def test_wrong_event_version_fails_instead_of_checking_another_commit(self):
        self.commit("No static changes")
        self.merge()
        self.event["pull_request"]["head"]["sha"] = self.base
        for mode in ("candidate", "main-ready"):
            with self.subTest(mode=mode):
                self.assertIn("does not match", "\n".join(self.check(mode, 1)["issues"]))


if __name__ == "__main__":
    unittest.main()
