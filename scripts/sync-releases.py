#!/usr/bin/env python3
"""Resolve download links for every project in data/projects.toml.

Fetches the latest GitHub release of every repository in a single GraphQL
query (and Firefox Add-ons listings for AMO-sourced extensions), applies the
asset rules from projects.toml, and writes data/releases.json.

The output holds no timestamps of its own and no download counts, so it only
changes when a release does; the sync workflow commits it only on change.

When a project fails to resolve (no release, a rule matching zero or several
assets, an API error), its previous entry is kept so the site never publishes
a broken link, and the failure is written to --report for the workflow to file
as an issue.

Standard library only. Needs Python 3.11+ (tomllib).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tomllib
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "data" / "projects.toml"
RELEASES = ROOT / "data" / "releases.json"
FEED = ROOT / "static" / "releases.xml"
CONFIG = ROOT / "config.toml"

GRAPHQL_URL = "https://api.github.com/graphql"
AMO_URL = "https://addons.mozilla.org/api/v5/addons/addon/{slug}/"
USER_AGENT = "melashri-software-sync (+https://github.com/MohamedElashri/software)"

OS_LABELS = {
    "macos": "macOS",
    "linux": "Linux",
    "windows": "Windows",
    "firefox": "Firefox",
    "chrome": "Chrome",
    "vscode": "VS Code",
}
ARCH_LABELS = {
    "arm64": "ARM64",
    "x64": "x64",
    "universal": "Universal",
    "any": "",
}
MACOS_ARCH_LABELS = {"arm64": "Apple silicon", "x64": "Intel"}
KIND_SHORT = {
    "dmg": ".dmg", "zip": ".zip", "tar.gz": ".tar.gz", "appimage": "AppImage", "deb": ".deb",
    "rpm": ".rpm", "msi": ".msi", "exe": ".exe", "xpi": ".xpi", "vsix": ".vsix",
}
KIND_LABELS = {
    "dmg": "Disk image (.dmg)",
    "zip": "Archive (.zip)",
    "tar.gz": "Archive (.tar.gz)",
    "appimage": "AppImage",
    "deb": "Debian package (.deb)",
    "rpm": "RPM package (.rpm)",
    "msi": "Installer (.msi)",
    "exe": "Installer (.exe)",
    "xpi": "Add-on (.xpi)",
    "vsix": "Extension (.vsix)",
}


SECTIONS = {"apps", "cli", "extensions"}
SOURCES = {"github", "amo"}


class SyncError(Exception):
    pass


def validate_projects(projects: list[dict]) -> list[str]:
    """Return problems in projects.toml; an empty list means it is usable."""
    errors = []
    seen = set()
    for i, project in enumerate(projects):
        where = f"project {project.get('id', f'#{i + 1}')}"
        for key in ("id", "name", "section", "repo", "tagline"):
            if not isinstance(project.get(key), str) or not project[key].strip():
                errors.append(f"{where}: missing {key}")
        pid = project.get("id")
        if pid in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(pid)
        if pid and not re.fullmatch(r"[a-z0-9][a-z0-9-]*", pid):
            errors.append(f"{where}: id must be lowercase letters, digits and hyphens")
        if project.get("section") not in SECTIONS:
            errors.append(f"{where}: section must be one of {sorted(SECTIONS)}")
        if not re.fullmatch(r"[\w.-]+/[\w.-]+", project.get("repo", "")):
            errors.append(f"{where}: repo must be owner/name")
        source = project.get("source", "github")
        if source not in SOURCES:
            errors.append(f"{where}: source must be one of {sorted(SOURCES)}")
        if source == "amo" and not project.get("amo"):
            errors.append(f"{where}: source = amo needs an amo slug")
        for os_name in project.get("platforms", []):
            if os_name not in OS_LABELS:
                errors.append(f"{where}: unknown platform {os_name!r}")
        for method in project.get("install", []):
            if not method.get("label") or not method.get("cmd"):
                errors.append(f"{where}: install entries need label and cmd")
        for pattern in [project.get("checksums")] + [r.get("match") for r in project.get("asset", [])]:
            if pattern is None:
                continue
            try:
                re.compile(pattern)
            except re.error as err:
                errors.append(f"{where}: bad regex {pattern!r}: {err}")
        groups = {rule.get("group", "") for rule in project.get("asset", [])}
        if project.get("primary_group") and project["primary_group"] not in groups:
            errors.append(f"{where}: primary_group {project['primary_group']!r} matches no asset group")
        for rule in project.get("asset", []):
            if not rule.get("match"):
                errors.append(f"{where}: asset rule without match")
            if rule.get("os") not in OS_LABELS:
                errors.append(f"{where}: asset os {rule.get('os')!r} is not one of {sorted(OS_LABELS)}")
            if rule.get("arch") not in ARCH_LABELS:
                errors.append(f"{where}: asset arch {rule.get('arch')!r} is not one of {sorted(ARCH_LABELS)}")
            if rule.get("kind") not in KIND_LABELS:
                errors.append(f"{where}: asset kind {rule.get('kind')!r} is not one of {sorted(KIND_LABELS)}")
    return errors


def iso_utc(value: str) -> str:
    when = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    return when.strftime("%Y-%m-%dT%H:%M:%SZ")


def build_feed(projects: list[dict], resolved: dict[str, dict], site_url: str) -> str:
    """Atom feed with the latest release of every project, newest first."""
    entries = []
    for project in projects:
        entry = resolved.get(project["id"], {})
        if entry.get("version") and entry.get("published_at"):
            entries.append((entry["published_at"], project, entry))
    entries.sort(key=lambda item: (item[0], item[1]["id"]), reverse=True)
    updated = entries[0][0] if entries else "1970-01-01T00:00:00Z"
    host = re.sub(r"^https?://", "", site_url).split("/")[0]
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        "  <title>Software releases by Mohamed Elashri</title>",
        "  <subtitle>The latest release of each project on melashri.net/software</subtitle>",
        f'  <link rel="self" type="application/atom+xml" href="{escape(site_url)}releases.xml"/>',
        f'  <link rel="alternate" type="text/html" href="{escape(site_url)}"/>',
        f"  <id>{escape(site_url)}</id>",
        f"  <updated>{updated}</updated>",
        "  <author><name>Mohamed Elashri</name></author>",
    ]
    for published, project, entry in entries:
        page = f"{site_url}{project['id']}/"
        notes = entry.get("release_url") or entry.get("store_url") or page
        lines += [
            "  <entry>",
            f"    <title>{escape(project['name'])} {escape(entry['version'])}</title>",
            f'    <link rel="alternate" type="text/html" href="{escape(page)}"/>',
            f'    <link rel="related" type="text/html" href="{escape(notes)}"/>',
            f"    <id>tag:{host},{published[:4]}:software/{project['id']}/{escape(entry['version'])}</id>",
            f"    <published>{published}</published>",
            f"    <updated>{published}</updated>",
            f"    <summary>{escape(project['tagline'])}</summary>",
            "  </entry>",
        ]
    lines.append("</feed>")
    return "\n".join(lines) + "\n"


def write_if_changed(path: Path, text: str) -> bool:
    if path.exists() and path.read_text() == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    print(f"wrote {path.relative_to(ROOT)}")
    return True


def token() -> str:
    for var in ("GITHUB_TOKEN", "GH_TOKEN"):
        if os.environ.get(var):
            return os.environ[var]
    try:
        out = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, check=True
        )
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        sys.exit("error: set GITHUB_TOKEN or log in with `gh auth login`")


def http_json(url: str, data: dict | None = None, headers: dict | None = None) -> dict:
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method="POST" if body else "GET")
    req.add_header("User-Agent", USER_AGENT)
    req.add_header("Accept", "application/json")
    if body:
        req.add_header("Content-Type", "application/json")
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as err:
        raise SyncError(f"{url}: HTTP {err.code}") from err
    except urllib.error.URLError as err:
        raise SyncError(f"{url}: {err.reason}") from err


def fetch_github(projects: list[dict], gh_token: str) -> dict[str, dict]:
    """Return repository data keyed by project id, from one GraphQL query."""
    fields = """
      url
      description
      licenseInfo { spdxId }
      latestRelease {
        tagName
        publishedAt
        url
        releaseAssets(first: 100) { nodes { name size digest downloadUrl } }
      }
    """
    parts = []
    for i, project in enumerate(projects):
        owner, name = project["repo"].split("/", 1)
        parts.append(f'p{i}: repository(owner: "{owner}", name: "{name}") {{ {fields} }}')
    query = "query {\n" + "\n".join(parts) + "\n}"
    resp = http_json(
        GRAPHQL_URL, {"query": query}, {"Authorization": f"bearer {gh_token}"}
    )
    data = resp.get("data") or {}
    errors = {
        e.get("path", [None])[0]: e.get("message", "unknown error")
        for e in resp.get("errors", [])
    }
    result = {}
    for i, project in enumerate(projects):
        key = f"p{i}"
        if data.get(key) is None:
            result[project["id"]] = {"error": errors.get(key, "repository not found")}
        else:
            result[project["id"]] = data[key]
    return result


def human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1000 or unit == "GB":
            return f"{value:.0f} {unit}" if unit in ("B", "KB") else f"{value:.1f} {unit}"
        value /= 1000
    return f"{size} B"


def date_label(iso: str) -> tuple[str, str]:
    when = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return when.date().isoformat(), f"{when:%b} {when.day}, {when.year}"


def asset_labels(rule: dict) -> dict:
    os_name, arch = rule["os"], rule["arch"]
    if os_name == "macos" and arch in MACOS_ARCH_LABELS:
        arch_text = MACOS_ARCH_LABELS[arch]
    else:
        arch_text = ARCH_LABELS[arch]
    if rule.get("variant"):
        arch_text += f" ({rule['variant']})"
    return {
        "os_label": OS_LABELS[os_name],
        "arch_label": arch_text,
        "kind_label": KIND_LABELS[rule["kind"]],
        "kind_short": KIND_SHORT[rule["kind"]],
    }


def strip_digest(digest: str | None) -> str | None:
    if digest and digest.startswith("sha256:"):
        return digest.removeprefix("sha256:")
    return None


def resolve_github(project: dict, repo: dict) -> dict:
    if "error" in repo:
        raise SyncError(repo["error"])
    release = repo.get("latestRelease")
    if not release:
        if project.get("asset"):
            raise SyncError("no published release")
        entry = {"source": "github", "repo_url": repo["url"]}
        if repo.get("licenseInfo"):
            entry["license"] = repo["licenseInfo"]["spdxId"]
        return entry

    nodes = release["releaseAssets"]["nodes"]
    names = [n["name"] for n in nodes]
    assets = []
    for rule in project.get("asset", []):
        hits = [n for n in nodes if re.search(rule["match"], n["name"])]
        if len(hits) != 1:
            found = ", ".join(h["name"] for h in hits) or "nothing"
            raise SyncError(
                f"rule {rule['match']!r} matched {found} (expected exactly one); "
                f"assets: {', '.join(names) or 'none'}"
            )
        hit = hits[0]
        assets.append(
            {
                "os": rule["os"],
                "arch": rule["arch"],
                "kind": rule["kind"],
                "group": rule.get("group", ""),
                **asset_labels(rule),
                "name": hit["name"],
                "url": hit["downloadUrl"],
                "size": hit["size"],
                "size_label": human_size(hit["size"]),
                "sha256": strip_digest(hit.get("digest")),
            }
        )

    # The first asset per OS in the primary group (ungrouped by default) is the one
    # offered as the quick download; rule order in projects.toml sets the preference.
    seen = set()
    primary_group = project.get("primary_group", "")
    for asset in assets:
        asset["primary"] = asset["group"] == primary_group and asset["os"] not in seen
        if asset["primary"]:
            seen.add(asset["os"])

    tag = release["tagName"]
    date, date_text = date_label(release["publishedAt"])
    entry = {
        "source": "github",
        "tag": tag,
        "version": re.sub(r"^[^\d]*", "", tag) or tag,
        "published": date,
        "published_at": iso_utc(release["publishedAt"]),
        "published_label": date_text,
        "release_url": release["url"],
        "repo_url": repo["url"],
    }
    if repo.get("licenseInfo") and repo["licenseInfo"]["spdxId"] != "NOASSERTION":
        entry["license"] = repo["licenseInfo"]["spdxId"]
    if project.get("checksums"):
        sums = [n for n in nodes if re.search(project["checksums"], n["name"])]
        if len(sums) != 1:
            raise SyncError(f"checksums rule {project['checksums']!r} matched {len(sums)} assets")
        entry["checksums_url"] = sums[0]["downloadUrl"]
    entry["assets"] = assets
    return entry


def resolve_amo(project: dict, repo: dict) -> dict:
    addon = http_json(AMO_URL.format(slug=project["amo"]))
    if addon.get("status") != "public":
        raise SyncError(f"AMO listing {project['amo']!r} is {addon.get('status')!r}")
    version = addon["current_version"]
    file = version["file"]
    created = file.get("created") or addon["last_updated"]
    date, date_text = date_label(created)
    entry = {
        "source": "amo",
        "version": version["version"],
        "published": date,
        "published_at": iso_utc(created),
        "published_label": date_text,
        "store_url": addon["url"],
        "repo_url": repo.get("url") or f"https://github.com/{project['repo']}",
    }
    spdx = ((repo.get("licenseInfo") or {}).get("spdxId")) if "error" not in repo else None
    if spdx and spdx != "NOASSERTION":
        entry["license"] = spdx
    entry["assets"] = [
        {
            "os": "firefox",
            "arch": "any",
            "kind": "xpi",
            "group": "",
            **asset_labels({"os": "firefox", "arch": "any", "kind": "xpi"}),
            "name": file["url"].rsplit("/", 1)[-1],
            "url": file["url"],
            "size": file["size"],
            "size_label": human_size(file["size"]),
            "sha256": strip_digest(file.get("hash")),
            "primary": True,
        }
    ]
    return entry


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--report", type=Path, help="write failures as Markdown here")
    parser.add_argument("--strict", action="store_true", help="exit 1 on any failure")
    parser.add_argument("--check", action="store_true",
                        help="only validate projects.toml and the feed; no network")
    args = parser.parse_args()

    with PROJECTS.open("rb") as fh:
        projects = tomllib.load(fh)["project"]
    problems = validate_projects(projects)
    if problems:
        for problem in problems:
            print(f"error: {problem}", file=sys.stderr)
        return 1
    with CONFIG.open("rb") as fh:
        site_url = tomllib.load(fh)["base_url"].rstrip("/") + "/"

    previous = {}
    if RELEASES.exists():
        previous = json.loads(RELEASES.read_text()).get("projects", {})

    if args.check:
        feed = build_feed(projects, previous, site_url)
        stale = not FEED.exists() or FEED.read_text() != feed
        print(f"projects.toml ok ({len(projects)} projects)")
        if stale:
            print("error: static/releases.xml is out of date; run the sync", file=sys.stderr)
        return 1 if stale else 0

    repos = fetch_github(projects, token())
    resolved: dict[str, dict] = {}
    failures: list[tuple[str, str]] = []
    for project in projects:
        pid = project["id"]
        try:
            if project.get("source") == "amo":
                resolved[pid] = resolve_amo(project, repos[pid])
            else:
                resolved[pid] = resolve_github(project, repos[pid])
        except (SyncError, KeyError) as err:
            failures.append((pid, str(err)))
            if pid in previous:
                resolved[pid] = previous[pid]
        status = "FAIL" if failures and failures[-1][0] == pid else "ok"
        entry = resolved.get(pid, {})
        print(f"{status:4}  {pid:16} {entry.get('version', '-'):10} {len(entry.get('assets', []))} assets")

    out = json.dumps({"projects": resolved}, indent=2, ensure_ascii=False) + "\n"
    changed = write_if_changed(RELEASES, out)
    changed |= write_if_changed(FEED, build_feed(projects, resolved, site_url))
    if not changed:
        print("no changes")

    if args.report:
        if failures:
            lines = ["The release sync could not resolve these projects.",
                     "Their previous download links were kept.", ""]
            lines += [f"- **{pid}**: {msg}" for pid, msg in failures]
            args.report.write_text("\n".join(lines) + "\n")
        elif args.report.exists():
            args.report.unlink()

    for pid, msg in failures:
        print(f"error: {pid}: {msg}", file=sys.stderr)
    return 1 if failures and args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
