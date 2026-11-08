+++
title = "Snipo"
description = "A self-hosted snippet manager for code fragments, commands and notes."
template = "project"

[extra]
id = "snipo"
+++

A snippet manager you run yourself, built for a single user: one master password protects the whole instance and there are no accounts to manage. The server includes a web app for your code fragments, commands and notes. Run it with Docker Compose or use a Linux server binary.

- Snippets with multiple named files, folders, tags, favorites, archiving, expiration and edit history
- Search and filter by text, tag, folder, language or favorite
- A choice of Ace, CodeMirror 6 or Monaco editors, plus Markdown preview and right-to-left text
- Public share links, API tokens, encrypted backups and optional sync with GitHub Gists

Use [Snippy](../snippy/) to browse, edit and copy snippets in the terminal, or [Snipo for browsers](../snipo-extension/) to save selected text from Chrome and Firefox. Both connect to your running Snipo server.
