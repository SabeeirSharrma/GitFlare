# GitFlare — Recorded Changes

All notable changes to GitFlare will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [0.4.0] — 2026-06-26

### Added

- **Admin REST API** — full CRUD endpoints with Bearer auth
  - `GET /admin/repos` — list repos
  - `POST /admin/repos` — create repo
  - `DELETE /admin/repos/{name}` — delete repo
  - `GET /admin/repos/{name}/branches` — list branches
  - `GET /admin/repos/{name}/commits` — list commits
  - `POST /admin/repos/{name}/token` — generate token
  - `DELETE /admin/repos/{name}/token` — revoke tokens
  - `GET /admin/ssh-keys` — list SSH keys
  - `POST /admin/ssh-keys` — add SSH key
  - `DELETE /admin/ssh-keys/{key_id}` — remove SSH key
- **Bearer auth** — admin routes require `Authorization: Bearer <admin_token>`
- **Branch listing** — list branches for any repo
- **Commit listing** — list recent commits with hash, message, author, date

---

## [0.3.0] — 2026-06-26

### Added

- **SSH key management** — `auth/ssh.py` with `add_key()`, `list_keys()`, `remove_key()`
- **SSH handler** — `git/ssh_handler.py` for git-shell integration with per-repo auth
- **Admin SSH commands** — `gitflare-admin ssh-key add|list|remove`
- **Ruff + mypy** — linting and type checking configured in `pyproject.toml`

### Changed

- Auth mode "ssh" repos now properly reject SSH push without authorized key

---

## [0.2.0] — 2026-06-26

### Added

- **Token auth enforcement** — push requests now require valid token for `auth_mode` "token" or "both"
- **Admin auth route** — `GET /admin/auth/verify` validates tokens against stored bcrypt hashes
- **`gitflare-admin login`** — stores token in system keychain and registers credential helper in `~/.gitconfig`
- **`gitflare-admin logout`** — erases token from keychain and removes gitconfig entry

### Changed

- SSH-only repos (`auth_mode: "ssh"`) reject push over HTTP with 403
- Clone/fetch remains public for all auth modes (read-only access)

---

## [0.1.0] — 2026-06-26

### Added

- **Core server** — FastAPI app with uvicorn, config loading from `gitflare.toml`
- **Git HTTP backend** — subprocess wrapper for `git http-backend`, parses CGI responses
- **Smart HTTP routes** — catch-all handler for clone/fetch/push over HTTP
- **Repo management** — `git init --bare` wrapper, list, delete
- **Admin CLI** — `gitflare-admin repo create|list|delete`, `gitflare-admin token generate|revoke`
- **Token infrastructure** — per-repo `gitflare.json` metadata with `auth_mode`, `tokens[]`, `ssh_keys[]`
- **Auth module** — `auth/tokens.py` with `generate_token()`, `hash_token()`, `verify_token()` using bcrypt
- **Credential helper** — `git-credential-gitflare` for system keychain integration (executable)
- **Health check** — `GET /` returns service status
- **SPEC.md** — full architecture and project specification

### Fixed

- Route precedence issue where catch-all `/{repo_path:path}` was intercepting `/` before the health check endpoint
