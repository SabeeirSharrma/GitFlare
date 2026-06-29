# GitFlare — Architecture & Project Spec
**The Cinder Project** | License: GPLv3 | Language: Python

---

## Overview

GitFlare is a self-hosted Git repository hosting server built in Python. It sits as a thin, opinionated layer on top of Git's own tooling — delegating all actual object storage and protocol handling to Git itself, while providing auth, repo management, and (eventually) a web UI on top.

**Target:** Personal/small-team use. Designed to be lean, auditable, and free of unnecessary infra.

---

## Versioning Roadmap

| Version | Scope |
|---------|-------|
| v0.1 | HTTP clone/fetch (read-only), repo init, basic config |
| v0.2 | HTTP push with token auth + `git-credential-gitflare` helper + `gitflare-admin login` |
| v0.3 | SSH key auth, per-repo auth mode selection, admin API, branch listing, commit history |
| v0.4 | Stable core — structured logging, git hooks, ref management, health check |
| v0.5 | Web UI for ease of access (EOA) |
| v1.0 | Production-ready release |

---

## Project Structure

```
gitflare/
├── gitflare/
│   ├── __init__.py
│   ├── main.py               # FastAPI app entrypoint
│   ├── config.py             # Loads gitflare.toml
│   ├── logging.py            # Structured logging + request middleware
│   ├── models.py             # Pydantic models
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── tokens.py         # HTTP token auth
│   │   └── ssh.py            # SSH key management
│   ├── git/
│   │   ├── __init__.py
│   │   ├── backend.py        # Wraps git http-backend via subprocess
│   │   ├── repo.py           # Repo init, delete, list
│   │   ├── hooks.py          # Git hooks (pre-receive, post-receive, update)
│   │   └── ssh_handler.py    # git-shell integration
│   └── routes/
│       ├── __init__.py
│       ├── git_http.py       # Smart HTTP protocol routes
│       └── admin.py          # Admin API (repos, branches, commits, hooks, tokens, ssh-keys)
├── gitflare-admin             # CLI tool (thin wrapper around admin API)
├── git-credential-gitflare    # Git credential helper binary (installed to PATH)
├── gitflare.toml              # Main config file
├── pyproject.toml
├── README.md
└── SPEC.md                    # This file (lives in repo)
```

---

## Core Architecture

```
                        ┌─────────────────────────────┐
  git push/pull/clone   │         GitFlare             │
─────────────────────▶  │        (FastAPI)             │
  over HTTP or SSH       │                             │
                        │  ┌──────────┐  ┌─────────┐  │
                        │  │ Auth     │  │  Admin  │  │
                        │  │ Layer    │  │  API    │  │
                        │  └────┬─────┘  └────┬────┘  │
                        │       │              │       │
                        │  ┌────▼─────────────▼────┐  │
                        │  │     git http-backend   │  │
                        │  │     (subprocess/CGI)   │  │
                        │  └────────────┬───────────┘  │
                        │               │              │
                        │  ┌────────────▼───────────┐  │
                        │  │   /repos/<name>.git    │  │
                        │  │   (bare git repos)     │  │
                        │  └────────────────────────┘  │
                        └─────────────────────────────┘

SSH path:
  git@host:repo.git  ──▶  sshd  ──▶  git-shell  ──▶  /repos/<name>.git
```

**Key principle:** GitFlare never touches Git objects directly. All protocol handling is delegated to `git http-backend` (for HTTP) and `git-shell` (for SSH). GitFlare only handles auth, routing, and repo lifecycle.

---

## Config — `gitflare.toml`

```toml
[server]
host = "0.0.0.0"
port = 3000
repos_path = "/srv/gitflare/repos"

# Optional — only set if you want GitFlare to emit full clone URLs
# (e.g. in admin API responses or future web UI)
# If unset, GitFlare works purely locally with no absolute URL generation
# base_url = "https://git.yourdomain.com"

[auth]
admin_token = "your-secret-admin-token"   # SHA256 hashed in practice

[ssh]
enabled = true
port = 2222
authorized_keys_path = "/srv/gitflare/authorized_keys"
```

---

## Auth Model

Per-repo auth mode is set at creation time. SSH is the recommended default; HTTP token is available for users who prefer it, but the token is never handled manually — the credential helper takes care of it transparently.

### SSH Key Auth (recommended)
- User submits public key via `gitflare-admin ssh-key add`
- GitFlare appends it to `authorized_keys` with `command="git-shell -c"` restriction
- Standard `git clone git@host:repo.git` flow — no credential prompts ever

### HTTP Token Auth + Credential Helper
Tokens exist under the hood but users never touch them directly. The flow:

1. Admin generates a token for a repo: `gitflare-admin token generate cpac`
2. User runs `gitflare-admin login http://yourhost` — prompts once for the token, stores it in the **system keychain** via `keyring`, and registers `git-credential-gitflare` as the credential helper for that host in `~/.gitconfig`
3. From that point on, every `git clone/push/pull http://yourhost/repo.git` just works — Git calls the helper automatically, the helper retrieves the token from the keychain, done

```
git clone http://yourhost/cpac.git
  └─▶ git asks credential helper for http://yourhost
        └─▶ git-credential-gitflare get
              └─▶ keyring.get_password("gitflare:yourhost", username)
                    └─▶ returns token silently
                          └─▶ clone proceeds, no prompt
```

### `git-credential-gitflare` — How it works

Git's credential helper protocol is dead simple — Git calls the helper as a subprocess with one of three actions: `get`, `store`, `erase`. Each action reads/writes key=value pairs on stdin/stdout.

```python
#!/usr/bin/env python3
# git-credential-gitflare
# Installed to PATH so Git can find it as "gitflare" helper

import sys
import keyring

SERVICE_PREFIX = "gitflare"

def parse_input() -> dict:
    data = {}
    for line in sys.stdin:
        line = line.strip()
        if not line:
            break
        key, _, value = line.partition("=")
        data[key] = value
    return data

def main():
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    data = parse_input()
    host = data.get("host", "")
    service = f"{SERVICE_PREFIX}:{host}"

    if action == "get":
        token = keyring.get_password(service, "gitflare")
        if token:
            print(f"username=gitflare")
            print(f"password={token}")

    elif action == "store":
        token = data.get("password", "")
        if token:
            keyring.set_password(service, "gitflare", token)

    elif action == "erase":
        keyring.delete_password(service, "gitflare")

if __name__ == "__main__":
    main()
```

### `gitflare-admin login` — one-time setup

```bash
$ gitflare-admin login http://yourhost
Token: ████████████████   # prompted once, not echoed
✓ Token stored in system keychain
✓ Registered git-credential-gitflare for http://yourhost in ~/.gitconfig
```

What it does under the hood:
1. Validates the token against `GET /admin/auth/verify`
2. Stores it via `keyring.set_password("gitflare:yourhost", "gitflare", token)`
3. Writes to `~/.gitconfig`:
   ```ini
   [credential "http://yourhost"]
       helper = gitflare
   ```

### `gitflare-admin logout`

```bash
gitflare-admin logout http://yourhost
# Erases from keychain, removes the gitconfig entry
```

### Per-repo metadata
```json
// stored in /repos/<name>.git/gitflare.json
{
  "name": "cinderOS",
  "auth_mode": "ssh",     // "token", "ssh", or "both"
  "tokens": ["bcrypt_hashed_token"],
  "ssh_keys": []
}
```

### Server-side token validation
GitFlare receives the token as HTTP Basic auth (`Authorization: Basic base64(gitflare:token)`), bcrypt-verifies it against the repo's stored hash, and either passes the request through to `git http-backend` or returns 401.

---

## HTTP Smart Protocol — How it works

Git's smart HTTP protocol uses two endpoints:

```
GET  /repo.git/info/refs?service=git-upload-pack   # fetch/clone
POST /repo.git/git-upload-pack                      # fetch/clone data
GET  /repo.git/info/refs?service=git-receive-pack  # push
POST /repo.git/git-receive-pack                    # push data
```

GitFlare intercepts these, runs auth, then pipes the request/response straight through to `git http-backend` via subprocess:

```python
# Rough sketch of backend.py
import subprocess, os

def run_git_backend(repo_path: str, request: Request) -> Response:
    env = {
        "GIT_PROJECT_ROOT": REPOS_PATH,
        "GIT_HTTP_EXPORT_ALL": "1",
        "PATH_INFO": f"/{repo_path}",
        "REQUEST_METHOD": request.method,
        "QUERY_STRING": str(request.url.query),
        "CONTENT_TYPE": request.headers.get("content-type", ""),
        **os.environ
    }
    proc = subprocess.Popen(
        ["git", "http-backend"],
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    body = await request.body()
    stdout, stderr = proc.communicate(input=body)
    # Parse CGI response headers + body and return as FastAPI Response
    return parse_cgi_response(stdout)
```

---

## Admin API (v0.4+)

All routes require `Authorization: Bearer <admin_token>`.

```
POST   /admin/repos              # Create repo
DELETE /admin/repos/{name}       # Delete repo
GET    /admin/repos              # List repos
POST   /admin/repos/{name}/token # Generate access token for repo
DELETE /admin/repos/{name}/token # Revoke token
GET    /admin/repos/{name}/branches   # List branches
POST   /admin/repos/{name}/branches   # Create branch
DELETE /admin/repos/{name}/branches/{branch}  # Delete branch
GET    /admin/repos/{name}/commits    # List commits
GET    /admin/repos/{name}/tags       # List tags
GET    /admin/repos/{name}/hooks      # List installed hooks
POST   /admin/repos/{name}/hooks/{hook}/test  # Test a hook
POST   /admin/ssh-keys           # Add SSH key
DELETE /admin/ssh-keys/{id}      # Remove SSH key
GET    /admin/ssh-keys           # List SSH keys
GET    /admin/auth/verify        # Validate a token (used by gitflare-admin login)
```

---

## Admin CLI — `gitflare-admin`

Thin Python script that wraps the admin API:

```bash
# Auth — one-time setup on client machine
gitflare-admin login http://yourhost        # store token in keychain, register helper
gitflare-admin logout http://yourhost       # erase from keychain, remove gitconfig entry

# Repo management
gitflare-admin repo create cinderOS --auth ssh
gitflare-admin repo create cpac --auth token
gitflare-admin repo list
gitflare-admin repo delete cinderOS

# Token management
gitflare-admin token generate cpac          # prints token once, store it safely
gitflare-admin token revoke cpac

# SSH keys
gitflare-admin ssh-key add "ssh-ed25519 AAAA..."
gitflare-admin ssh-key list
gitflare-admin ssh-key remove <id>
```

---

## Dependencies

Kept minimal intentionally:

```toml
[project]
dependencies = [
    "fastapi",
    "uvicorn[standard]",
    "pydantic",
    "tomllib",       # stdlib in Python 3.11+
    "bcrypt",        # token hashing
    "httpx",         # for admin CLI
    "keyring",       # system keychain storage for credential helper
]
```

`keyring` uses the native keychain on every platform — libsecret/KWallet on Linux, Keychain on macOS, Windows Credential Manager on Windows. No plaintext token files anywhere.

No ORM, no database for v0.1–v0.2 — flat JSON files. SQLite added in v0.3 if needed.

---

## Deployment (VPS)

### systemd unit — `/etc/systemd/system/gitflare.service`

```ini
[Unit]
Description=GitFlare Git Server
After=network.target

[Service]
Type=simple
User=gitflare
WorkingDirectory=/opt/gitflare
ExecStart=/opt/gitflare/.venv/bin/uvicorn gitflare.main:app --host 0.0.0.0 --port 3000
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Caddy reverse proxy — `/etc/caddy/Caddyfile`

```caddy
git.yourdomain.com {
    reverse_proxy localhost:3000
}
```

Caddy handles HTTPS/Let's Encrypt automatically.

### SSH on alternate port

Since sshd is likely already on port 22 for the VPS, run GitFlare's SSH on 2222 and users do:

```bash
git clone ssh://git@yourdomain.com:2222/cpac.git
```

Or add to `~/.ssh/config`:
```
Host gitflare
    HostName yourdomain.com
    Port 2222
    User git
```

---

## v0.1 Quickstart (what to build first)

1. `gitflare/config.py` — load `gitflare.toml` (`base_url` is `Optional[str] = None`; anywhere clone URLs are generated, skip or omit the field if unset)
2. `gitflare/git/repo.py` — `git init --bare` wrapper
3. `gitflare/git/backend.py` — subprocess wrapper for `git http-backend`
4. `gitflare/routes/git_http.py` — the 4 smart HTTP routes, no auth yet
5. Wire it up in `main.py`, test with `git clone http://localhost:3000/test.git`

Token auth + `git-credential-gitflare` + `gitflare-admin login` come in v0.2 once the plumbing works.

---

## Branding

- **Name:** GitFlare
- **Org:** The Cinder Project
- **Accent color:** `#FF4500` (ember orange, consistent with CPAC/CinderOS)
- **License:** GPLv3
- **Repo:** `github.com/SabeeirSharrma/GitFlare` (ironic temporary home until it hosts itself)
