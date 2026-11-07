+++
title = "txm"
description = "Persistent terminals and supervised jobs across projects and SSH hosts."
template = "project"

[extra]
id = "txm"
+++

A command-line tool for keeping shells and background work running across projects and SSH hosts, mainly on Linux and macOS. It has its own native backend with Ghostty terminal emulation, or it can work with your existing tmux, Zellij or GNU Screen setup.

- Persistent sessions you can detach from and reconnect to
- Workspace profiles in TOML that recreate commands, working directories and tmux pane layouts
- Supervise any command, including coding agents, and record its exit result
- A keyboard dashboard to search sessions, preview output and attach
- Isolated tasks in Git worktrees, reviewed before you apply a fast-forward merge
- Versioned JSON output, live event streams and a scoped MCP server for scripts and local clients
