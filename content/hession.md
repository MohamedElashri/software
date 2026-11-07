+++
title = "Hession"
description = "A searchable home for coding-agent sessions from this machine and your SSH hosts."
template = "project"

[extra]
id = "hession"
+++

A desktop app for searching, reading, analyzing and resuming your coding-agent sessions. It gathers history from this computer and from the SSH hosts you work on, for example through VS Code Remote-SSH, into one library stored on your machine.

- One library for Claude Code, Codex, OpenCode, Cline, Pi, Command Code, Muse, Hermes Agent and Antigravity sessions
- Remote sessions copied in with your own `ssh` and `rsync` on each sync, with nothing changed on the host
- Full-text search with filters for agent, host, workspace, model, branch, tool and date
- Resume a session in its agent CLI, locally or over SSH, or open its folder in VS Code
- Analytics for tokens, estimated cost, tools and failures
- Local SQLite storage and no telemetry; agent history files are read, never written
