+++
title = "Nida"
description = "A small static site generator for blogs, personal sites and documentation."
template = "project"

[extra]
id = "nida"
+++

Nida turns Markdown files with TOML or YAML front matter into a static site using Go HTML templates, and the output can be hosted anywhere. The name (نداء) is Arabic for "call". This site is built with it.

- `nida init` creates an example site to start from
- `nida serve` previews the site locally
- `nida check` finds broken links and errors before you publish
- `nida migrate` converts a Hugo, Jekyll, Zola, Eleventy or Pelican site and reports anything left to do
- Sections, shortcodes, math and diagrams in content, with themes, layouts and partials for templates
- Right-to-left layouts, shown in the bundled Arabic example blog
