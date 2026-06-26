# GitFlare

**Self-hosted Git repository hosting server** | The Cinder Project | GPLv3

GitFlare is a lean, self-hosted Git server built in Python. It sits as a thin layer on top of Git's own tooling — delegating all object storage and protocol handling to Git itself, while providing auth, repo management, and (eventually) a web UI on top.

**Target:** Personal/small-team use. Designed to be auditable, free of unnecessary infra, and easy to deploy.

---

## Features

- **HTTP Smart Protocol** — full clone/fetch/push over HTTP
- **Token-based auth** — per-repo access tokens with bcrypt hashing
- **Credential helper** — `git-credential-gitflare` stores tokens in your system keychain (no plaintext)
- **Admin CLI** — create repos, manage tokens, list repos
- **Bare repos** — standard Git bare repos, nothing proprietary
- **Lightweight** — FastAPI + uvicorn, no database, no ORM, flat JSON metadata

## Quick Start

### Install

```bash
git clone https://github.com/TheCinderProject/gitflare.git
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

## Admin CLI

```bash
# Repo management
gitflare-admin repo create <name> [--auth ssh|token|both]
gitflare-admin repo list
gitflare-admin repo delete <name>

# Token management
gitflare-admin token generate <repo>
gitflare-admin token revoke <repo>
```

## Project Structure

```
gitflare/
├── gitflare/
│   ├── main.py               # FastAPI app entrypoint
│   ├── config.py             # Loads gitflare.toml
│   ├── models.py             # Pydantic models
│   ├── auth/
│   │   ├── tokens.py         # Token generation & bcrypt hashing
│   │   └── ssh.py            # SSH key management (v0.3)
│   ├── git/
│   │   ├── backend.py        # Wraps git http-backend via subprocess
│   │   └── repo.py           # Repo init, delete, list, metadata
│   └── routes/
│       ├── git_http.py       # Smart HTTP protocol routes
│       └── admin.py          # Admin API (v0.4+)
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
| v0.3 | SSH key auth, per-repo auth mode selection |
| v0.4 | Branch listing, multi-repo support, admin API |
| v0.5 | Stable core — full push/pull/branch over HTTP + SSH |
| v1.0 | Web UI — file browser, commit log, branch switcher |

## License

GPLv3 — see [LICENSE](LICENSE) for details.

## Made By

Made under The CInder Project with intent to make the internet a safer place.

- **Owner/Maintainer/Main Developer:** [Sabeeir Sharrma](https://github.com/sabeeirsharrma)
- **Maintainer/Assistant Developer:** [trigered02](https://github.com/trigered02)
- **Discord:** [Join us](https://discord.com/invite/3ZMtEgJjFT)
