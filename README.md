# GitFlare

**Self-hosted Git repository hosting server** | The Cinder Project | GPLv3

GitFlare is a lean, self-hosted Git server built in Python. It sits as a thin layer on top of Git's own tooling — delegating all object storage and protocol handling to Git itself, while providing auth, repo management, and (eventually) a web UI on top.

**Target:** Personal/small-team use. Designed to be auditable, free of unnecessary infra, and easy to deploy.

---

## Features

- **HTTP Smart Protocol** — full clone/fetch/push over HTTP
- **Token-based auth** — per-repo access tokens with bcrypt hashing, enforced on push
- **SSH key auth** — manage SSH keys via the admin CLI
- **Credential helper** — `git-credential-gitflare` stores tokens in your system keychain (no plaintext)
- **Admin CLI** — `gitflare-admin login/logout`, repo, token, SSH key, branch, and hook management
- **Git hooks** — default pre-receive hook rejects force push to main/master
- **Structured logging** — every request logged with timing
- **Web UI** — browse repos, view files, commit logs, branches, and tags in your browser
- **Bare repos** — standard Git bare repos, nothing proprietary
- **Lightweight** — FastAPI + uvicorn, no database, no ORM, flat JSON metadata

## Quick Start

### Install

```bash
git clone https://github.com/SabeeirSharrma/GitFlare.git
cd gitflare
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Configure

Edit `gitflare.toml`:

```toml
[server]
host = "0.0.0.0"
port = 3000
repos_path = "/tmp/gitflare/repos"

[auth]
admin_token = "your-secret-admin-token"
```

### Run

```bash
uvicorn gitflare.main:app --host 0.0.0.0 --port 3000
```

### Create a repo and clone it

```bash
gitflare-admin repo create myproject --auth ssh
git clone http://localhost:3000/myproject.git
```

## Transparency & Installation

GitFlare is built transparently from source. **No pre-compiled code is embedded in this repository.** Every line of code is auditable before installation.

### Building from source (recommended)

```bash
git clone https://github.com/SabeeirSharrma/GitFlare.git
cd gitflare
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Pre-built artifacts

Pre-built wheels and source distributions are available on the [Releases](https://github.com/SabeeirSharrma/GitFlare/releases) page. While functional, **building from source is the recommended and preferred method** — it ensures full transparency and allows you to inspect the code before installation.

Checksums (`sha256sums.txt`) are provided with every release for verification:

```bash
sha256sum -c sha256sums.txt
```

## Admin CLI

```bash
# Auth — one-time setup on client machine
gitflare-admin login http://yourhost:3000   # store token in keychain
gitflare-admin logout http://yourhost:3000  # remove from keychain

# Repo management
gitflare-admin repo create <name> [--auth ssh|token|both]
gitflare-admin repo list
gitflare-admin repo delete <name>

# Token management
gitflare-admin token generate <repo>
gitflare-admin token revoke <repo>

# SSH key management
gitflare-admin ssh-key add "ssh-ed25519 AAAA..."
gitflare-admin ssh-key list
gitflare-admin ssh-key remove <key_id>
```

## Project Structure

```
gitflare/
├── gitflare/
│   ├── main.py               # FastAPI app entrypoint
│   ├── config.py             # Loads gitflare.toml
│   ├── logging.py            # Structured logging + request middleware
│   ├── models.py             # Pydantic models
│   ├── auth/
│   │   ├── tokens.py         # Token generation & bcrypt hashing
│   │   └── ssh.py            # SSH key management
│   ├── git/
│   │   ├── backend.py        # Wraps git http-backend via subprocess
│   │   ├── repo.py           # Repo init, delete, list, metadata
│   │   ├── hooks.py          # Git hooks (pre-receive, post-receive, update)
│   │   └── ssh_handler.py    # git-shell integration
│   └── routes/
│       ├── git_http.py       # Smart HTTP protocol routes + token auth
│       └── admin.py          # Admin API (repos, branches, commits, hooks, tokens, ssh-keys)
├── git-credential-gitflare    # Git credential helper
├── gitflare.toml              # Config file
├── pyproject.toml
├── SPEC.md                    # Architecture spec
└── README.md
```

## Roadmap

| Version | Scope |
|---------|-------|
| v0.1 | HTTP clone/fetch/push, repo init, basic config, token infra |
| v0.2 | HTTP push with token auth + credential helper + `gitflare-admin login` |
| v0.3 | SSH key auth, per-repo auth mode selection, admin API, branch listing |
| v0.4 | Stable core — structured logging, git hooks, ref management, health check |
| v0.5 | Web UI — repo browser, file tree, commit log, branch switcher |
| v1.0 | Production-ready release |

## License

GPLv3 — see [LICENSE](LICENSE) for details.

## Made By

Made under The CInder Project with intent to make the internet a safer place.

- **Owner/Maintainer/Main Developer:** [Sabeeir Sharrma](https://github.com/sabeeirsharrma)
- **Maintainer/Assistant Developer:** [trigered02](https://github.com/trigered02)
- **Discord:** [Join us](https://discord.com/invite/3ZMtEgJjFT)
