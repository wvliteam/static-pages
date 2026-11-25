import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "skills/static-page-builder/scripts/check_static_html.py"
HTML = (
    '<!doctype html><html><head><title>Example</title>'
    '<meta name="viewport" content="width=device-width"></head><body></body></html>'
)


class ArtifactManifestTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.temp = Path(temporary.name)
        self.root = self.temp / "artifact"
        self.root.mkdir()
        (self.root / "index.html").write_text(HTML, encoding="utf-8")

    def run_check(self, *args):
        return subprocess.run(
            [sys.executable, str(CHECKER), "--root", str(self.root), *args],
            capture_output=True, text=True, check=False,
        )

    def test_manifest_is_sorted_complete_and_has_canonical_bundle_digest(self):
        (self.root / "assets").mkdir()
        (self.root / "assets" / "图标.svg").write_bytes(b"<svg/>")
        (self.root / "style.css").write_text("body{}", encoding="utf-8")

        result = self.run_check()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = json.loads(result.stdout)["artifact_manifest"]
        files = manifest["files"]
        self.assertEqual([item["path"] for item in files], ["assets/图标.svg", "index.html", "style.css"])
        for item in files:
            content = (self.root / item["path"]).read_bytes()
            self.assertEqual(item["bytes"], len(content))
            self.assertEqual(item["sha256"], hashlib.sha256(content).hexdigest())
        canonical = json.dumps(
            files, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        self.assertEqual(manifest["bundle_sha256"], hashlib.sha256(canonical).hexdigest())

    def test_output_record_outside_root_is_not_in_manifest(self):
        output = self.temp / "check.json"

        result = self.run_check("--output", str(output))

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = json.loads(result.stdout)["artifact_manifest"]
        self.assertEqual([item["path"] for item in manifest["files"]], ["index.html"])
        self.assertTrue(output.is_file())
        result = self.run_check("--output", str(self.root / "check.json"))
        self.assertEqual(result.returncode, 2)

    def test_css_imports_and_urls_report_missing_transitive_resources(self):
        (self.root / "css" / "nested").mkdir(parents=True)
        (self.root / "css" / "site.css").write_text(
            '@import "nested/theme.css";\n.hero { background: url("../images/hero.png"); }',
            encoding="utf-8",
        )
        (self.root / "css" / "nested" / "theme.css").write_text(
            '@font-face { src: url("../../fonts/site.woff2"); }', encoding="utf-8"
        )
        (self.root / "index.html").write_text(
            HTML.replace("</head>", '<link rel="stylesheet" href="css/site.css"></head>'),
            encoding="utf-8",
        )

        result = self.run_check()

        self.assertEqual(result.returncode, 1)
        issues = json.loads(result.stdout)["pages"][0]["issues"]
        self.assertTrue(any("../images/hero.png" in issue for issue in issues), issues)
        self.assertTrue(any("../../fonts/site.woff2" in issue for issue in issues), issues)

    def test_css_import_cycle_is_reported_and_terminates(self):
        (self.root / "a.css").write_text('@import "b.css";', encoding="utf-8")
        (self.root / "b.css").write_text('@import url("a.css");', encoding="utf-8")
        (self.root / "index.html").write_text(
            HTML.replace("</head>", '<link rel="stylesheet" href="a.css"></head>'),
            encoding="utf-8",
        )

        result = self.run_check()

        self.assertEqual(result.returncode, 1)
        issues = json.loads(result.stdout)["pages"][0]["issues"]
        self.assertTrue(any("CSS @import 循环" in issue for issue in issues), issues)

    def test_symlinks_and_special_files_are_issues_not_manifest_entries(self):
        if os.name == "nt":
            self.skipTest("symlink and FIFO creation requires POSIX behavior")
        external = self.temp / "external.txt"
        external.write_text("outside artifact", encoding="utf-8")
        (self.root / "linked.txt").symlink_to(external)
        if hasattr(os, "mkfifo"):
            os.mkfifo(self.root / "pipe")

        result = self.run_check()

        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stdout)
        self.assertNotIn("linked.txt", [item["path"] for item in data["artifact_manifest"]["files"]])
        self.assertTrue(any("符号链接" in issue and "linked.txt" in issue for issue in data["issues"]))
        if hasattr(os, "mkfifo"):
            self.assertTrue(any("特殊文件" in issue and "pipe" in issue for issue in data["issues"]))


if __name__ == "__main__":
    unittest.main()
