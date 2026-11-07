"""Consistency checks across data, content and static files, and the built site.

The build checks run only when public/ exists (after `nida build`).
"""

import json
import re
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"

with (ROOT / "data" / "projects.toml").open("rb") as fh:
    PROJECTS = tomllib.load(fh)["project"]
RELEASES = json.loads((ROOT / "data" / "releases.json").read_text())["projects"]
SHOTS = json.loads((ROOT / "data" / "shots.json").read_text())


def front_matter(path):
    text = path.read_text()
    match = re.match(r"\+\+\+\n(.*?)\n\+\+\+\n", text, re.S)
    if not match:
        raise AssertionError(f"{path} has no TOML front matter")
    return tomllib.loads(match.group(1)), text[match.end():]


class DataTest(unittest.TestCase):
    def test_every_project_has_release_data(self):
        for project in PROJECTS:
            with self.subTest(project["id"]):
                self.assertIn(project["id"], RELEASES)
                entry = RELEASES[project["id"]]
                # AMO listings contribute their one .xpi without a rule.
                expected = 1 if project.get("source") == "amo" else len(project.get("asset", []))
                self.assertEqual(len(entry.get("assets", [])), expected)

    def test_every_project_has_a_page(self):
        for project in PROJECTS:
            with self.subTest(project["id"]):
                meta, body = front_matter(ROOT / "content" / f"{project['id']}.md")
                self.assertEqual(meta["template"], "project")
                self.assertEqual(meta["extra"]["id"], project["id"])
                self.assertEqual(meta["title"], project["name"])
                self.assertEqual(meta["description"], project["tagline"])
                self.assertTrue(body.strip(), "page body is empty")

    def test_no_orphan_pages(self):
        ids = {p["id"] for p in PROJECTS}
        for path in (ROOT / "content").glob("*.md"):
            if path.name != "_index.md":
                self.assertIn(path.stem, ids, f"{path.name} has no project in projects.toml")

    def test_screenshots_exist(self):
        for project in PROJECTS:
            name = project.get("screenshot")
            if not name:
                continue
            with self.subTest(project["id"]):
                variants = [n for n in (name, f"{name}-light", f"{name}-dark") if n in SHOTS]
                self.assertTrue(variants, f"{name} is not in data/shots.json")
                for variant in variants:
                    for width in SHOTS[variant]["widths"]:
                        for ext in ("avif", "webp"):
                            path = ROOT / "static" / "shots" / f"{variant}-{width}.{ext}"
                            self.assertTrue(path.exists(), path)


@unittest.skipUnless((PUBLIC / "index.html").exists(), "run `nida build` first")
class BuildTest(unittest.TestCase):
    def test_index_lists_every_project(self):
        html = (PUBLIC / "index.html").read_text()
        for project in PROJECTS:
            with self.subTest(project["id"]):
                self.assertIn(f'href=/software/{project["id"]}/', html.replace('"', ""))

    def test_project_pages_link_every_download(self):
        for project in PROJECTS:
            with self.subTest(project["id"]):
                html = (PUBLIC / project["id"] / "index.html").read_text()
                for item in RELEASES[project["id"]].get("assets", []):
                    self.assertIn(item["url"], html)
                for method in project.get("install", []):
                    self.assertIn(method["label"], html)

    def test_no_third_party_assets(self):
        # Anything the browser loads: scripts, images, and stylesheet/icon/preload links.
        pattern = re.compile(
            r'<(?:script|img|source|link\b[^>]*\brel="?(?:stylesheet|icon|preload|modulepreload)"?)\b'
            r'[^>]*\b(?:src|href|srcset)="?(?:https?:)?//', re.I)
        for path in PUBLIC.rglob("*.html"):
            with self.subTest(path.relative_to(PUBLIC).as_posix()):
                self.assertIsNone(pattern.search(path.read_text()))

    def test_feed_is_published(self):
        self.assertTrue((PUBLIC / "releases.xml").exists())


if __name__ == "__main__":
    unittest.main()
