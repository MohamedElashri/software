+++
title = "free for macOS"
description = "The Linux free command, for macOS memory."
template = "project"

[extra]
id = "free-mac"
+++

macOS does not ship the `free` command that Linux users rely on for a quick look at memory. This tool brings it over, printing total, used and free memory and swap usage from the terminal in the familiar table layout.

- Memory and swap usage in the same columns as Linux `free`
- Units from bytes to pebibytes, human-readable output with `-h`, and powers of 1000 with `--si`
- A totals line with `-t`
- Repeated output every few seconds with `-s`, a set number of times with `-c`
