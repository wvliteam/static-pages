#!/usr/bin/env python3
"""Validate a pull request's fixed Git snapshots without publishing anything."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile

from build_pages import MAX_ARCHIVE, archive_files, preview_html

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/static-page-builder/scripts"))
sys.path.insert(0, str(ROOT / "skills/static-page-publisher/scripts"))
from check_static_html import HtmlChecker
from verify_deployment import relative_path

REGULAR_MODES = {"100644", "100755"}
RESERVED = {"previews", "artifacts", "deployment.json"}


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], check=True, stdout=subprocess.PIPE).stdout


def tree(sha: str, directory: str) -> dict[str, tuple[str, str]]:
    result = {}
    for row in git("ls-tree", "-r", "-z", "--full-tree", sha, "--", directory).split(b"\0"):
        if row:
            header, name = row.split(b"\t", 1)
            mode, _, oid = header.decode("ascii").split()
            result[name.decode("utf-8")] = mode, oid
    return result


def commit_sha(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value):
        raise ValueError("Expected a full 40-character Git commit SHA")
    return value


def versions(event: dict, candidate: str, result: dict) -> tuple[str, str, int]:
    pull = event["pull_request"]
    base, head = (commit_sha(pull[side]["sha"]) for side in ("base", "head"))
    number = pull["number"]
    result.update(base_sha=base, head_sha=head, tested_merge_sha=candidate, pr=number)
    if pull["base"]["ref"] != "main" or type(number) is not int or number < 1:
        raise ValueError("Expected a pull request targeting main with a positive PR number")
    parents = git("rev-list", "--parents", "-n", "1", candidate).decode("ascii").split()
    if parents != [candidate, base, head]:
        raise ValueError("Tested merge commit does not match the event's base and head")
    if git("rev-parse", "HEAD").decode("ascii").strip() != candidate:
        raise ValueError("Check out the event's tested merge commit before validating")
    # A shallow or missing parent must fail even when recorded in the commit header.
    for sha in (base, head):
        git("cat-file", "-e", sha + "^{commit}")
    return base, head, number


def archive_at(sha: str) -> bytes:
    # Read the Git archive, not the checkout, so export-ignore and export-subst
    # affect the snapshot just as they can affect a hosted source archive.
    with subprocess.Popen(
        ["git", "archive", "--format=tar.gz", "--prefix=candidate/", sha],
        stdout=subprocess.PIPE,
    ) as process:
        assert process.stdout is not None
        content = process.stdout.read(MAX_ARCHIVE + 1)
        if len(content) > MAX_ARCHIVE:
            process.kill()
            raise ValueError("Git archive exceeds the publisher size limit")
        if process.wait():
            raise ValueError("Could not archive the PR head")
        return content


def checked_path(path: str) -> None:
    if any(ord(char) < 32 or ord(char) == 127 for char in path):
        raise ValueError(f"Control character in path: {path!r}")
    if "?" in path or "#" in path:
        raise ValueError(f"Query or fragment delimiter in path: {path!r}")
    relative_path(path)


def check_html(root: Path, names: list[str], base: str, issues: list[str], label: str) -> None:
    checker = HtmlChecker(root, base)
    for name in names:
        try:
            issues.extend(f"{label}{name}: {message}" for message in checker.check(checker.page_file(name)))
        except (OSError, ValueError) as exc:
            issues.append(f"{label}{name}: {exc}")


def check_production(candidate: str, result: dict) -> None:
    files = tree(candidate, "docs")
    if "docs/index.html" not in files:
        raise ValueError("docs/index.html is required")
    for name, (mode, _) in files.items():
        if mode not in REGULAR_MODES:
            raise ValueError(f"Production only accepts regular files: {name}")
        if name.removeprefix("docs/").split("/", 1)[0] in RESERVED:
            raise ValueError(f"Reserved production path: {name}")
        checked_path(name.removeprefix("docs/"))
    if (git("diff", "--no-ext-diff", "--name-only", "-z", candidate, "--", "docs")
            or git("ls-files", "--others", "-z", "--", "docs")):
        raise ValueError("docs must match the tested merge checkout with no untracked files")
    names = [name.removeprefix("docs/") for name in files if name.lower().endswith(".html")]
    result["production_pages"] = names
    check_html(Path("docs"), names, "/static-pages/", result["issues"], "docs/")


def check_previews(head: str, number: int, result: dict) -> None:
    expected = tree(head, "artifacts")
    if not expected:
        return
    for name, (mode, _) in expected.items():
        parts = name.split("/")
        if len(parts) < 4 or parts[2] != "public":
            raise ValueError(f"Preview file must be under artifacts/<task>/public/: {name}")
        if mode not in REGULAR_MODES:
            raise ValueError(f"Preview only accepts regular files: {name}")
        checked_path("/".join(parts[3:]))
    tasks = archive_files(archive_at(head))
    archived = {
        f"artifacts/{task}/public/{name}": data
        for task, files in tasks.items() for name, data in files.items()
    }
    for name in sorted(expected.keys() | archived.keys()):
        if name not in expected or name not in archived:
            raise ValueError(f"Preview archive contains a different set of files: {name}")
        data = archived[name]
        if hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest() != expected[name][1]:
            raise ValueError(f"Preview archive changed the Git blob: {name}")

    issues = result["issues"]
    for task, files in sorted(tasks.items()):
        label = f"artifacts/{task}/public/"
        names = sorted(name for name in files if name.lower().endswith(".html"))
        result["previews"][task] = {"html": names, "files": len(files)}
        if "index.html" not in files:
            issues.append(f"{label}index.html is missing; this task has no online preview yet")
            continue
        with tempfile.TemporaryDirectory(prefix="static-preview-check-") as directory:
            root = Path(directory)
            for name, data in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            for name in names:
                try:
                    preview_html(files[name], number, task, head)
                except ValueError as exc:
                    issues.append(f"{label}{name}: {exc}")
            base = f"/static-pages/previews/pr-{number}/{task}/"
            check_html(root, names, base, issues, label)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("check", choices=("candidate", "main-ready"))
    parser.add_argument("--event-path", required=True, type=Path)
    parser.add_argument("--candidate-sha", required=True, type=commit_sha)
    args = parser.parse_args(argv)
    result = {"check": args.check, "issues": []}
    try:
        event = json.loads(args.event_path.read_text(encoding="utf-8"))
        _, head, number = versions(event, args.candidate_sha, result)
        if args.check == "main-ready":
            drafts = sorted(tree(args.candidate_sha, "artifacts"))
            result["tracked_artifacts"] = drafts
            if drafts:
                result["issues"].append("Tracked artifacts must be removed before merging to main")
        else:
            result.update(production_pages=[], previews={})
            check_production(args.candidate_sha, result)
            check_previews(head, number, result)
    except (KeyError, TypeError, ValueError, OSError, subprocess.CalledProcessError, tarfile.TarError) as exc:
        result["issues"].append(str(exc))
    result["ok"] = not result["issues"]
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
