"""Consistency checks across data, content and static files, and the built site.

The build checks run only when public/ exists (after `nida build`).
"""

import json
import re
import tomllib
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"

with (ROOT / "data" / "projects.toml").open("rb") as fh:
    PROJECTS = tomllib.load(fh)["project"]
RELEASES = json.loads((ROOT / "data" / "releases.json").read_text())["projects"]
with (ROOT / "config.toml").open("rb") as fh:
    CONFIG = tomllib.load(fh)
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
        # The only exception is the self-hosted Umami configured in config.toml.
        pattern = re.compile(
            r'<(?:script|img|source|link\b[^>]*\brel="?(?:stylesheet|icon|preload|modulepreload)"?)\b'
            r'[^>]*\b(?:src|href|srcset)="?((?:https?:)?//[^"\s>]+)', re.I)
        umami = CONFIG.get("extra", {}).get("umami", {}).get("host", "")
        for path in PUBLIC.rglob("*.html"):
            with self.subTest(path.relative_to(PUBLIC).as_posix()):
                external = [u for u in pattern.findall(path.read_text()) if not (umami and u.startswith(umami + "/"))]
                self.assertEqual(external, [])

    def test_feed_is_published(self):
        self.assertTrue((PUBLIC / "releases.xml").exists())

    def test_every_card_links_to_github(self):
        html = (PUBLIC / "index.html").read_text()
        for project in PROJECTS:
            with self.subTest(project["id"]):
                self.assertIn(f'https://github.com/{project["repo"]}"', html)

    def test_index_offers_quick_downloads(self):
        html = (PUBLIC / "index.html").read_text()
        for project in PROJECTS:
            entry = RELEASES[project["id"]]
            for item in entry.get("assets", []):
                if item["primary"]:
                    url = entry["store_url"] if entry["source"] == "amo" else item["url"]
                    with self.subTest(project["id"], os=item["os"]):
                        self.assertIn(url, html)

    def test_pages_have_theme_toggle(self):
        for path in PUBLIC.rglob("index.html"):
            if "<title>Redirect</title>" in path.read_text()[:300]:
                continue  # Nida's pagination and legacy URL redirects.
            with self.subTest(path.relative_to(PUBLIC).as_posix()):
                self.assertIn("theme-toggle", path.read_text())

    def test_chrome_store_install_links(self):
        index = (PUBLIC / "index.html").read_text()
        for project in PROJECTS:
            if not project.get("chrome_store"):
                continue
            with self.subTest(project["id"]):
                page = (PUBLIC / project["id"] / "index.html").read_text()
                for html in (index, page):
                    self.assertRegex(
                        html,
                        r'<a class="?dl-row"? href="?' + re.escape(project["chrome_store"])
                        + r'"? aria-label="Add ' + re.escape(project["name"])
                        + r' to Chrome from Chrome Web Store">',
                    )
                    self.assertIn(RELEASES[project["id"]]["store_url"], html)


@unittest.skipUnless((PUBLIC / "index.html").exists(), "run `nida build` first")
class SeoTest(unittest.TestCase):
    SITE = "https://melashri.net/software/"

    def head(self, rel):
        html = (PUBLIC / rel).read_text()
        return html[: html.index("</head>")]

    def meta(self, head, key):
        match = re.search(r'<meta (?:name|property)="?%s"? content="([^"]*)"' % re.escape(key), head)
        return match.group(1) if match else None

    def jsonld(self, head):
        blocks = re.findall(r'<script type="?application/ld\+json"?>(.*?)</script>', head, re.S)
        return [json.loads(b) for b in blocks]

    def test_every_page_has_metadata(self):
        titles = set()
        pages = ["index.html"] + [f'{p["id"]}/index.html' for p in PROJECTS]
        for rel in pages:
            with self.subTest(rel):
                head = self.head(rel)
                title = re.search(r"<title>(.+?)</title>", head).group(1)
                self.assertNotIn(title, titles, "duplicate title")
                titles.add(title)
                self.assertTrue(self.meta(head, "description"))
                self.assertRegex(head, r'<link rel="?canonical"? href="?https://melashri\.net/software/')
                image = self.meta(head, "og:image")
                self.assertTrue(image.startswith(self.SITE + "og/"), image)
                self.assertTrue((PUBLIC / image[len(self.SITE):]).exists(), image)
                self.assertEqual(self.meta(head, "twitter:card"), "summary_large_image")
                self.assertTrue(self.jsonld(head))

    def test_project_pages_describe_the_software(self):
        for project in PROJECTS:
            with self.subTest(project["id"]):
                apps = [d for d in self.jsonld(self.head(f'{project["id"]}/index.html'))
                        if d.get("@type") == "SoftwareApplication"]
                self.assertEqual(len(apps), 1)
                app = apps[0]
                self.assertEqual(app["name"], project["name"])
                self.assertEqual(app["url"], f'{self.SITE}{project["id"]}/')
                self.assertEqual(app.get("softwareVersion"), RELEASES[project["id"]].get("version"))
                self.assertEqual(app["offers"]["price"], "0")

    def test_index_lists_every_project(self):
        lists = [d for d in self.jsonld(self.head("index.html")) if d.get("@type") == "ItemList"]
        urls = [item["url"] for item in lists[0]["itemListElement"]]
        self.assertEqual(urls, [f'{self.SITE}{p["id"]}/' for p in PROJECTS])

    def test_chrome_store_metadata(self):
        for project in PROJECTS:
            if not project.get("chrome_store"):
                continue
            with self.subTest(project["id"]):
                head = self.head(f'{project["id"]}/index.html')
                app = next(d for d in self.jsonld(head) if d.get("@type") == "SoftwareApplication")
                self.assertIn("Chrome", app["operatingSystem"])
                self.assertIn("Chrome", self.meta(head, "description"))
                self.assertIn(project["chrome_store"], app["installUrl"])
                self.assertIn(RELEASES[project["id"]]["store_url"], app["installUrl"])


class Audit(HTMLParser):
    """Collects what the structural accessibility checks need from one page."""

    VOID = {"img", "input", "br", "hr", "meta", "link", "source", "path", "circle"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.problems, self.headings, self.ids = [], [], []
        self.lang = self.main = self.skip = False
        self.stack = []  # open link/button elements: [tag, attrs, text]

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = bool(a.get("lang"))
        if tag == "main":
            self.main = True
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "img" and "alt" not in a:
            self.problems.append(f"img without alt: {a.get('src')}")
        if re.fullmatch(r"h[1-6]", tag):
            self.headings.append(int(tag[1]))
        if tag == "a" and a.get("href") == "#main":
            self.skip = True
        if tag in ("a", "button"):
            self.stack.append([tag, a, ""])

    def handle_data(self, data):
        for item in self.stack:
            item[2] += data

    def handle_endtag(self, tag):
        if tag in ("a", "button") and self.stack and self.stack[-1][0] == tag:
            _, a, text = self.stack.pop()
            hidden = a.get("aria-hidden") == "true"
            if not hidden and not text.strip() and not a.get("aria-label"):
                self.problems.append(f"<{tag}> without an accessible name: {a.get('href') or a.get('class')}")


@unittest.skipUnless((PUBLIC / "index.html").exists(), "run `nida build` first")
class AccessibilityTest(unittest.TestCase):
    def pages(self):
        for path in sorted(PUBLIC.rglob("*.html")):
            if "Redirect" in path.read_text()[:300]:
                continue
            yield path

    def test_structure(self):
        for path in self.pages():
            with self.subTest(path.relative_to(PUBLIC).as_posix()):
                audit = Audit()
                audit.feed(path.read_text())
                self.assertEqual(audit.problems, [])
                self.assertTrue(audit.lang, "html has no lang")
                self.assertTrue(audit.main, "no <main> landmark")
                self.assertTrue(audit.skip, "no skip link to #main")
                self.assertEqual(audit.headings.count(1), 1, "expected exactly one h1")
                for before, after in zip(audit.headings, audit.headings[1:]):
                    self.assertLessEqual(after - before, 1, f"heading level jumps {before} to {after}")
                duplicates = {i for i in audit.ids if audit.ids.count(i) > 1}
                self.assertEqual(duplicates, set(), "duplicate ids")


if __name__ == "__main__":
    unittest.main()
