+++
title = "JSON Formatter"
description = "Readable, collapsible JSON in Firefox."
template = "project"

[extra]
id = "json-formatter"
+++

A Firefox extension that shows JSON as a highlighted, collapsible tree instead of a wall of text. It turns on for pages served as `application/json`, URLs ending in `.json` and pages that contain valid JSON, and it is written in plain JavaScript with no dependencies.

- Tree, formatted and raw views
- Expand or collapse nodes, or open the tree to a chosen depth
- Hover a key to see its JSON path, click to pin it, then copy it
- Copy the whole document to the clipboard
- Parsed data available as `window.data` in the browser console
- Light, dark and system themes
