+++
title = "Sanad"
description = "Generate, review and update GitHub's native Actions lockfiles."
template = "project"

[extra]
id = "sanad"
+++

A command-line tool and GitHub Action for GitHub's native workflow lockfile, `actions.lock`. It generates the lockfile, explains dependency changes, applies update policies and verifies the result in CI, while GitHub enforces the locked commits when workflows run. It needs a repository with native lockfile support, which GitHub currently offers as a public preview.

- `sanad init` previews and writes the initial lockfile
- `sanad sync` reconciles the lockfile after workflow edits without advancing existing pins
- `sanad plan` and `sanad update` review and apply stable updates, within the current major version by default
- Optional constraints and waiting periods for direct and transitive dependencies
- `sanad check` verifies the lockfile online, or offline for local coverage and graph checks
- A GitHub Action for pull request checks, and a skill for coding agents such as Claude Code, Codex and Cursor
