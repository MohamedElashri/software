# software

Source for [melashri.net/software](https://melashri.net/software/), the index of
desktop apps, command-line tools and browser extensions I build and maintain.

The site is built with [Nida](https://github.com/MohamedElashri/nida) and makes
no third-party requests: fonts are self-hosted and there is no CDN JavaScript.

## How download links stay current

- `data/projects.toml` is the hand-curated list: names, taglines, install
  commands, and one regular-expression rule per downloadable file.
- `scripts/sync-releases.py` fetches the latest release of every repository in a
  single GitHub GraphQL query (Firefox Add-ons for AMO-listed extensions),
  applies the rules, and writes `data/releases.json` with URLs, sizes and SHA-256
  digests.
- A scheduled workflow runs the sync, commits `releases.json` only when it
  changes, and redeploys the site. Project release workflows can trigger it
  directly with a `repository_dispatch` event.

If a rule stops matching (for example after an asset is renamed), the previous
links for that project are kept and the failure is reported, so the site never
publishes a broken download.

```sh
python3 scripts/sync-releases.py            # refresh data/releases.json and static/releases.xml
python3 scripts/sync-releases.py --strict   # exit 1 if any project failed
python3 scripts/sync-releases.py --check    # validate projects.toml and the feed, offline
```

Requires Python 3.11+ and a GitHub token (`GITHUB_TOKEN`, or a logged-in `gh`).

## Updating on release

The sync also runs within minutes of a release when a project's release workflow
sends a `repository_dispatch` event. Create a fine-grained token with
**Contents: read and write** on `MohamedElashri/software` only, store it in the
project repository as `SOFTWARE_SITE_TOKEN`, and add this step after the release
is published:

```yaml
- name: Update melashri.net/software
  env:
    GH_TOKEN: ${{ secrets.SOFTWARE_SITE_TOKEN }}
  run: gh api repos/MohamedElashri/software/dispatches -f event_type=release-published
```

Without it, new releases still appear within six hours.

## Building

```sh
nida serve                   # http://127.0.0.1:1717/software/ with live reload
nida build && nida check     # writes public/
python3 -m unittest discover -s tests   # data, content, build and accessibility checks
scripts/build-images.sh      # after adding or replacing a screenshot in assets/shots/
```

`scripts/build-images.sh` turns the PNG sources in `assets/shots/` into AVIF and
WebP files in `static/shots/` and records their sizes in `data/shots.json`. It
needs ImageMagick, `avifenc` and `cwebp`, so its output is committed and the
deploy doesn't need those tools.

## Adding a project

1. Add a `[[project]]` block to `data/projects.toml`.
2. Run the sync script and check that every rule resolves.
3. Add a screenshot to `assets/shots/` (`<name>.png`, or `<name>-light.png` and
   `<name>-dark.png`), run `scripts/build-images.sh`, and set `screenshot` in the
   project block.
4. Add `content/<id>.md` with `template = "project"` and `extra.id`.
