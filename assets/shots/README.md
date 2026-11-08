# Screenshots

Each project's own repository is the first source. When it has no screenshot,
the app is captured on macOS with demo data, never real hosts or files.
Compositions and terminal-output renders are identified below.
Terminal tools run in isolated demo sessions with a throwaway `$HOME`.
Every project has matching light and dark variants; cards and project pages
select the variant for the active site theme.

| File | Source |
|---|---|
| `mdiff-{light,dark}.png` | Native mdiff app reviewing the same demo `tally` repository and refund changes, with its built-in light/dark theme switch; cropped below the macOS title bar |
| `hession-{light,dark}.png` | hession repo, `docs/screenshots/` |
| `hedit-{light,dark}.png` | hedit repo, `docs/images/` |
| `snipo-{light,dark}.png` | snipo repo, `docs/demo*.png` |
| `snippy-{light,dark}.png` | Snippy 2.2.1 release binary in Rex Beta, captured directly from the native terminal against a throwaway local Snipo database; cropped to the terminal content at native resolution (1408×880), with the complete sample snippet, file tabs and keyboard hints visible |
| `snipo-extension-{light,dark}.png` | Composition in `assets/compose/`: sample documentation beside the extension 2.2.1 save page, using its actual HTML, CSS and JavaScript with fixture draft/folder/tag responses; the save form retains its native dark appearance in both variants |
| `zirq-{light,dark}.png` | Native Zirq demo window showing multilingual text and ANSI colors, captured with Breeze / Black on White terminal palettes and cropped to the demo tab and content |
| `sivro-{light,dark}.png` | sivro repo, `docs/images/` (demo `sales.parquet`) |
| `ternway-{light,dark}.png` | Ternway 0.3.0, launched with a throwaway `$HOME` and demo SSH hosts on documentation IP ranges |
| `json-formatter-{light,dark}.png` | JSON Formatter 1.0.1 content script on a local page of `releases.json`, cropped to the page |
| `imgblock-{light,dark}.png` | ImgBlock 1.0.1 before and after on a local demo article, composed from `assets/compose/` |
| `devtab-{light,dark}.png` | DevTab 1.3.0 from Firefox Add-ons in a throwaway profile, cropped to the new-tab page |
| `txm-{light,dark}.png` | txm 2.1.0 in Rex Beta: real session listing and bounded output capture from three private native sessions; session contents are sample API, test and documentation logs. The CLI view supports both terminal themes; the dashboard has a fixed dark palette |
| `sanad-{light,dark}.png` | Sanad 1.0.2's real `sanad check && sanad plan` output in Rex Beta, run in an isolated clone of this repository; both commands verify online, with the current formatted update table; native terminal capture cropped to 1408×880 |
| `agrep-{light,dark}.png` | Official agrep 0.1.1 binary in Zirq, on the same six-line Arabic corpus, demonstrating tashkil, tatweel, ta marbuta and Buckwalter queries; Zirq preserves Arabic shaping and bidirectional text in both terminal palettes |
| `free-mac-{light,dark}.png` | Real `free -h -t && free -m -s 1 -c 2` output (free-mac 0.4) in Rex Beta, captured unchanged in its light and dark terminal themes |
| `nida-{light,dark}.png` | The Nida documentation site (built with Nida), headless Waterfox at 1440 px |
