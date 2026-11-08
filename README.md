# software

Source for [melashri.net/software](https://melashri.net/software/), my catalog of
apps, command-line tools and browser extensions. Built with
[Nida](https://github.com/MohamedElashri/nida).

## Development

Requires Nida and Python 3.11+.

```sh
nida serve                            # local preview
nida build && nida check              # build and validate
python3 -m unittest discover -s tests  # run checks after building
```

## Updating projects

Edit `data/projects.toml` and the corresponding page in `content/`. Release links
sync automatically every six hours, or refresh them manually:

```sh
python3 scripts/sync-releases.py  # requires GITHUB_TOKEN or a logged-in gh
```

For screenshots, add light/dark PNGs to `assets/shots/` and run
`scripts/build-images.sh` (requires ImageMagick, `avifenc` and `cwebp`).
