+++
title = "Ternway"
description = "A desktop terminal for local shells and agentless Linux server management over SSH."
template = "project"

[extra]
id = "ternway"
+++

A terminal app for macOS and Linux that opens straight into your local shell and keeps your servers next to it. For each server you connect to over SSH, you get terminals alongside views for files, services, containers and logs, with nothing installed on the remote side.

- SSH with passwords or keys, OpenSSH config import, bastion routes and local, remote or SOCKS5 tunnels, with secrets kept in an encrypted local vault
- Server views for CPU, memory, disks, processes, systemd services, logs and listening ports
- File browsing and editing over SFTP, or open a remote file in your own local editor
- Docker and Podman containers, images, volumes and Compose projects
- Crontabs, APT packages, users and groups, authorized keys and UFW or firewalld rules
- Shell integration with exit status marks and prompt jumping, plus session restore and a drop-down quick terminal
