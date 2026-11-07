+++
title = "hedit"
description = "A text and log editor with durable buffers and CUDA debugging."
template = "project"

[extra]
id = "hedit"
+++

A native text editor for Linux, macOS and Windows that keeps your open files and unsaved notes from one session to the next. It covers code editing and project search, and it can also page through large files and follow logs as they grow.

- Recovery checkpoints, closed-file history and undo/redo across sessions
- Multiple cursors, split panes, completions and go-to-definition
- Git workspace with file, hunk and line staging, history, branches, conflict review and stashes
- Paged large files and read-only log following
- Right-to-left Arabic and Hebrew, UTF-8, UTF-16 and legacy encodings
- CUDA editing on every platform; on Linux, a CUDA panel that debugs with `cuda-gdb` and checks programs with `compute-sanitizer`
