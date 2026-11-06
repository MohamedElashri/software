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
python3 scripts/sync-releases.py            # refresh data/releases.json
python3 scripts/sync-releases.py --strict   # exit 1 if any project failed
```

Requires Python 3.11+ and a GitHub token (`GITHUB_TOKEN`, or a logged-in `gh`).

## Adding a project

1. Add a `[[project]]` block to `data/projects.toml`.
2. Run the sync script and check that every rule resolves.
3. Add a screenshot to `assets/shots/` and a page in `content/`.
