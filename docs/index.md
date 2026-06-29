---
title: Introduction
description: Overview of GitFlare — self-hosted Git repository hosting.
order: 1
---

# GitFlare

**Self-hosted Git repository hosting server** — The Cinder Project | GPLv3

GitFlare is a lean, self-hosted Git server built in Python. It sits as a thin layer on top of Git's own tooling — delegating all object storage and protocol handling to Git itself, while providing auth, repo management, and (eventually) a web UI on top.

## What is GitFlare?

GitFlare is a self-hosted Git repository hosting server designed for personal and small-team use. It handles HTTP clone, fetch, and push via Git's smart HTTP protocol, and provides SSH key authentication for secure access.

It is **not** a GitHub/GitLab replacement. GitFlare is a **minimal, auditable Git server** — no databases, no ORM, no unnecessary infrastructure. Just Git, Python, and your bare repos.

## Philosophy

- GitFlare never touches Git objects directly — all protocol handling is delegated to `git http-backend` and `git-shell`
- Every line of code is auditable — no pre-compiled binaries, build from source recommended
- Per-repo auth modes let you choose between SSH-only, token-only, or both
- Tokens are never handled manually — the credential helper stores them in your system keychain
- Designed to be lean, transparent, and free of unnecessary infrastructure

## Features

### HTTP Smart Protocol

Full clone, fetch, and push over HTTP using Git's own `http-backend`. No proprietary protocols — just standard Git.

### Token-Based Authentication

Per-repo access tokens with bcrypt hashing. Tokens are stored in your system keychain via the credential helper — no plaintext, no manual entry.

### SSH Key Authentication

SSH key management via the admin CLI. Keys are added to `authorized_keys` with `git-shell` restriction for secure, passwordless access.

### Per-Repo Auth Modes

Choose the auth mode for each repository:
- **`ssh`** — SSH key auth only (recommended default)
- **`token`** — HTTP token auth required for push
- **`both`** — SSH or token auth accepted

### Credential Helper

`git-credential-gitflare` stores tokens in your system keychain (libsecret on Linux, Keychain on macOS, Windows Credential Manager on Windows). Once logged in, every `git clone/push/pull` just works — no prompts.

### Admin CLI

Full repo and token management from the command line:
- Create, list, delete repos
- Generate and revoke access tokens
- Manage SSH keys

### Lightweight

FastAPI + uvicorn, no database, no ORM, flat JSON metadata. Just bare Git repos with a `gitflare.json` file for auth configuration.

## Quick Start

```bash
# Clone and install
git clone https://github.com/TheCinderProject/gitflare.git
cd gitflare
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Start the server
uvicorn gitflare.main:app --host 0.0.0.0 --port 3000

# Create a repo
gitflare-admin repo create myproject --auth ssh

# Clone it
git clone http://localhost:3000/myproject.git
```

## Requirements

- Python 3.11+
- Git installed on the system
- pip for package installation

## Roadmap

| Version | Scope |
|---------|-------|
| v0.1 | HTTP clone/fetch/push, repo init, basic config, token infra |
| v0.2 | HTTP push with token auth + credential helper + `gitflare-admin login` |
| v0.3 | SSH key auth, per-repo auth mode selection |
| v0.4 | Branch listing, multi-repo support, admin API |
| v0.5 | Stable core — full push/pull/branch over HTTP + SSH |
| v1.0 | Web UI — file browser, commit log, branch switcher |

## Made By

**Owner/Main Developer:** [Sabeeir Sharrma](https://github.com/sabeeirsharrma)

**Maintainer/Assistant Developer:** [trigered02](https://github.com/trigered02)

**Made under [The Cinder Project](https://thecinderproject.qd.je/)** — *Making a safer internet*
