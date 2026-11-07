"""Unit tests for scripts/sync-releases.py. No network access."""

import copy
import importlib.util
import tomllib
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("sync", ROOT / "scripts" / "sync-releases.py")
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)

ATOM = "{http://www.w3.org/2005/Atom}"


def asset(name, size=1_000_000):
    return {
        "name": name,
        "size": size,
        "digest": "sha256:" + "ab" * 32,
        "downloadUrl": f"https://github.com/o/r/releases/download/v1.2.0/{name}",
    }


def repo(*names, tag="v1.2.0"):
    return {
        "url": "https://github.com/o/r",
        "description": "",
        "licenseInfo": {"spdxId": "MIT"},
        "latestRelease": {
            "tagName": tag,
            "publishedAt": "2026-11-05T14:38:14Z",
            "url": f"https://github.com/o/r/releases/tag/{tag}",
            "releaseAssets": {"nodes": [asset(n) for n in names]},
        },
    }


PROJECT = {
    "id": "tool",
    "name": "Tool",
    "section": "cli",
    "repo": "o/r",
    "tagline": "Does a thing.",
    "checksums": r"^checksums\.txt$",
    "asset": [
        {"os": "macos", "arch": "arm64", "kind": "tar.gz", "match": r"_darwin_arm64\.tar\.gz$"},
        {"os": "macos", "arch": "x64", "kind": "tar.gz", "match": r"_darwin_x86_64\.tar\.gz$"},
        {"os": "linux", "arch": "x64", "kind": "tar.gz", "match": r"_linux_x86_64\.tar\.gz$"},
        {"group": "Extras", "os": "linux", "arch": "arm64", "kind": "deb", "match": r"_arm64\.deb$"},
    ],
}
NAMES = [
    "checksums.txt",
    "tool_1.2.0_darwin_arm64.tar.gz",
    "tool_1.2.0_darwin_x86_64.tar.gz",
    "tool_1.2.0_linux_x86_64.tar.gz",
    "tool_1.2.0_arm64.deb",
]


class ResolveGithubTest(unittest.TestCase):
    def test_resolves_every_rule(self):
        entry = sync.resolve_github(PROJECT, repo(*NAMES))
        self.assertEqual(entry["version"], "1.2.0")
        self.assertEqual(entry["tag"], "v1.2.0")
        self.assertEqual(entry["published"], "2026-11-05")
        self.assertEqual(entry["published_at"], "2026-11-05T14:38:14Z")
        self.assertEqual(entry["license"], "MIT")
        self.assertTrue(entry["checksums_url"].endswith("/checksums.txt"))
        self.assertEqual([a["name"] for a in entry["assets"]], NAMES[1:])
        self.assertEqual(entry["assets"][0]["sha256"], "ab" * 32)
        self.assertEqual(entry["assets"][0]["size_label"], "1.0 MB")

    def test_labels(self):
        assets = sync.resolve_github(PROJECT, repo(*NAMES))["assets"]
        self.assertEqual(assets[0]["arch_label"], "Apple silicon")
        self.assertEqual(assets[1]["arch_label"], "Intel")
        self.assertEqual(assets[2]["os_label"], "Linux")
        self.assertEqual(assets[3]["kind_label"], "Debian package (.deb)")

    def test_one_primary_per_os_and_never_grouped(self):
        assets = sync.resolve_github(PROJECT, repo(*NAMES))["assets"]
        self.assertEqual([a["primary"] for a in assets], [True, False, True, False])

    def test_variant_is_shown_with_arch(self):
        project = copy.deepcopy(PROJECT)
        project["asset"][2]["variant"] = "musl"
        assets = sync.resolve_github(project, repo(*NAMES))["assets"]
        self.assertEqual(assets[2]["arch_label"], "x64 (musl)")

    def test_rule_matching_nothing_fails(self):
        with self.assertRaisesRegex(sync.SyncError, "matched nothing"):
            sync.resolve_github(PROJECT, repo(*NAMES[:-1]))

    def test_rule_matching_twice_fails(self):
        with self.assertRaisesRegex(sync.SyncError, "expected exactly one"):
            sync.resolve_github(PROJECT, repo(*NAMES, "tool_1.2.0_linux_x86_64.tar.gz"))

    def test_missing_release_fails_when_assets_expected(self):
        data = repo(*NAMES)
        data["latestRelease"] = None
        with self.assertRaisesRegex(sync.SyncError, "no published release"):
            sync.resolve_github(PROJECT, data)

    def test_project_without_assets_needs_no_release(self):
        data = repo()
        data["latestRelease"] = None
        project = dict(PROJECT, asset=[], checksums=None)
        entry = sync.resolve_github(project, data)
        self.assertEqual(entry["repo_url"], "https://github.com/o/r")
        self.assertNotIn("assets", entry)

    def test_repository_error_is_reported(self):
        with self.assertRaisesRegex(sync.SyncError, "not found"):
            sync.resolve_github(PROJECT, {"error": "repository not found"})


class ValidateTest(unittest.TestCase):
    def test_projects_toml_is_valid(self):
        with (ROOT / "data" / "projects.toml").open("rb") as fh:
            projects = tomllib.load(fh)["project"]
        self.assertEqual(sync.validate_projects(projects), [])

    def test_catches_mistakes(self):
        bad = copy.deepcopy(PROJECT)
        bad["section"] = "games"
        bad["asset"][0]["os"] = "plan9"
        bad["asset"][1]["match"] = "("
        amo = dict(PROJECT, id="ext", source="amo", asset=[])
        errors = "\n".join(sync.validate_projects([bad, dict(PROJECT), amo]))
        self.assertIn("section must be one of", errors)
        self.assertIn("'plan9'", errors)
        self.assertIn("bad regex", errors)
        self.assertIn("duplicate id", errors)
        self.assertIn("needs an amo slug", errors)


class FeedTest(unittest.TestCase):
    def test_feed_is_valid_atom_newest_first(self):
        projects = [
            dict(PROJECT, id="old", name="Old & Tired"),
            dict(PROJECT, id="new", name="New"),
            dict(PROJECT, id="none", name="Unreleased"),
        ]
        resolved = {
            "old": {"version": "1.0", "published_at": "2025-01-01T00:00:00Z", "release_url": "https://x/1"},
            "new": {"version": "2.0", "published_at": "2026-02-02T00:00:00Z", "store_url": "https://x/2"},
            "none": {},
        }
        root = ET.fromstring(sync.build_feed(projects, resolved, "https://example.com/software/"))
        self.assertEqual(root.findtext(f"{ATOM}updated"), "2026-02-02T00:00:00Z")
        titles = [e.findtext(f"{ATOM}title") for e in root.findall(f"{ATOM}entry")]
        self.assertEqual(titles, ["New 2.0", "Old & Tired 1.0"])
        first = root.find(f"{ATOM}entry")
        self.assertEqual(first.findtext(f"{ATOM}id"), "tag:example.com,2026:software/new/2.0")
        self.assertEqual(first.find(f"{ATOM}link").get("href"), "https://example.com/software/new/")


class HelpersTest(unittest.TestCase):
    def test_human_size(self):
        self.assertEqual(sync.human_size(512), "512 B")
        self.assertEqual(sync.human_size(12_400), "12 KB")
        self.assertEqual(sync.human_size(16_242_370), "16.2 MB")
        self.assertEqual(sync.human_size(1_500_000_000), "1.5 GB")

    def test_iso_utc(self):
        self.assertEqual(sync.iso_utc("2026-10-17T10:00:00+02:00"), "2026-10-17T08:00:00Z")


if __name__ == "__main__":
    unittest.main()
