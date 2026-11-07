#!/usr/bin/env python3
"""Render social cards (Open Graph images, 1200x630) into static/og/.

One card per project from data/projects.toml, plus static/og/index.jpg for the
home page. Each card is laid out as HTML with the site's fonts and the project's
light screenshot, then rendered with a headless Firefox-family browser. Set
FIREFOX to the browser binary if it is not one of the defaults below.

Cards are saved as JPEG with ImageMagick (magick). Run after changing a tagline
or a screenshot; the images are committed so the deploy needs neither tool.
"""

from __future__ import annotations

import html
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "static" / "og"
BROWSERS = [
    "/Applications/Firefox.app/Contents/MacOS/firefox",
    "/Applications/Waterfox.app/Contents/MacOS/waterfox",
    "firefox",
]
OS_NAMES = {"macos": "macOS", "linux": "Linux", "windows": "Windows", "firefox": "Firefox"}
SECTION_NAMES = {"apps": "Desktop app", "cli": "Command-line tool", "extensions": "Browser extension"}

STYLE = """
@font-face { font-family: CM; font-weight: 400; src: url("{fonts}/commit-mono-400-regular.woff2"); }
@font-face { font-family: CM; font-weight: 700; src: url("{fonts}/commit-mono-700-regular.woff2"); }
html, body { margin: 0; width: 1200px; height: 630px; overflow: hidden; background: #f3f4f1; color: #1b1d1f; font-family: CM, monospace; }
.card { position: relative; width: 1200px; height: 630px; box-sizing: border-box; padding: 64px 64px 56px; }
.site { font-size: 24px; color: #575c60; }
.site b { color: #1b1d1f; }
h1 { margin: 40px 0 0; font-size: 76px; line-height: 1.05; letter-spacing: -0.03em; max-width: 560px; }
.tag { margin-top: 24px; font-size: 28px; line-height: 1.4; color: #575c60; max-width: 520px; }
.meta { position: absolute; left: 64px; bottom: 56px; font-size: 22px; color: #575c60; }
.meta span { color: #2347d6; font-weight: 700; }
.shot { position: absolute; left: 640px; top: 96px; width: 760px; height: 475px; border-radius: 18px; border: 2px solid #d6d9d4; overflow: hidden; background: #e8eae6; box-shadow: 0 24px 60px rgba(27, 29, 31, 0.18); }
.shot img { width: 100%; height: 100%; object-fit: cover; object-position: left top; display: block; }
.grid { position: absolute; left: 600px; top: 64px; display: grid; grid-template-columns: 300px 300px; gap: 20px; }
.grid div { width: 300px; height: 188px; border-radius: 12px; border: 2px solid #d6d9d4; overflow: hidden; background: #e8eae6; }
.grid img { width: 100%; height: 100%; object-fit: cover; object-position: left top; display: block; }
"""


def browser() -> str:
    for candidate in [os.environ.get("FIREFOX")] + BROWSERS:
        if candidate and (Path(candidate).exists() or shutil.which(candidate)):
            return candidate
    sys.exit("error: no Firefox-family browser found; set FIREFOX")


def shot_file(name: str | None, shots: dict) -> str | None:
    if not name:
        return None
    for variant in (f"{name}-light", name):
        if variant in shots:
            width = next((w for w in shots[variant]["widths"] if w >= 1280), shots[variant]["widths"][-1])
            return (ROOT / "static" / "shots" / f"{variant}-{width}.webp").as_uri()
    return None


def page(body: str) -> str:
    fonts = (ROOT / "static" / "fonts").as_uri()
    return f'<!doctype html><html><head><meta charset="utf-8"><style>{STYLE.replace("{fonts}", fonts)}</style></head><body>{body}</body></html>'


def project_card(project: dict, shots: dict) -> str:
    platforms = ", ".join(OS_NAMES[p] for p in project.get("platforms", []))
    image = shot_file(project.get("screenshot"), shots)
    shot = f'<div class="shot"><img src="{image}" alt=""></div>' if image else ""
    return page(
        '<div class="card">'
        '<div class="site">melashri.net/<b>software</b></div>'
        f'<h1>{html.escape(project["name"])}</h1>'
        f'<p class="tag">{html.escape(project["tagline"])}</p>'
        f'<p class="meta"><span>{SECTION_NAMES[project["section"]]}</span> for {html.escape(platforms)}</p>'
        f"{shot}</div>"
    )


def index_card(projects: list[dict], shots: dict) -> str:
    images = [shot_file(p.get("screenshot"), shots) for p in projects if p["section"] == "apps"]
    tiles = "".join(f'<div><img src="{uri}" alt=""></div>' for uri in [u for u in images if u][:4])
    return page(
        '<div class="card">'
        '<div class="site">melashri.net/<b>software</b></div>'
        "<h1>Software by Mohamed Elashri</h1>"
        '<p class="tag">Desktop apps, command-line tools and browser extensions.</p>'
        f'<p class="meta"><span>{len(projects)} projects</span> with downloads for every platform</p>'
        f'<div class="grid">{tiles}</div></div>'
    )


def render(exe: str, profile: str, source: Path, target: Path) -> None:
    png = source.with_suffix(".png")
    subprocess.run(
        [exe, "--headless", "-no-remote", "-profile", profile, "--window-size=1200,630",
         "--screenshot", str(png), source.as_uri()],
        check=True, capture_output=True, timeout=120,
    )
    if not png.exists():
        sys.exit(f"error: browser did not write {png}")
    subprocess.run(["magick", str(png), "-strip", "-quality", "86", str(target)],
                   check=True, capture_output=True)


def main() -> int:
    with (ROOT / "data" / "projects.toml").open("rb") as fh:
        projects = tomllib.load(fh)["project"]
    shots = json.loads((ROOT / "data" / "shots.json").read_text())
    exe = browser()
    if not shutil.which("magick"):
        sys.exit("error: ImageMagick (magick) not found")
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True)
    with tempfile.TemporaryDirectory() as tmp:
        profile = Path(tmp, "profile")
        profile.mkdir()
        cards = [("index", index_card(projects, shots))]
        cards += [(p["id"], project_card(p, shots)) for p in projects]
        for name, markup in cards:
            source = Path(tmp, f"{name}.html")
            source.write_text(markup)
            render(exe, str(profile), source, OUT / f"{name}.jpg")
            print(f"static/og/{name}.jpg")
    return 0


if __name__ == "__main__":
    sys.exit(main())
