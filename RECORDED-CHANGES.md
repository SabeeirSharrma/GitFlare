# GitFlare — Recorded Changes

All notable changes to GitFlare will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [1.0.0] — 2026-07-17

### Changed

- Version bumped to 1.0.0 — production-ready release
- All documentation finalized and consistent

---

## [0.5.0] — 2026-07-17

### Added

- **Web UI** — static SPA for browsing repositories in a browser:
  - Repository listing with latest commit info
  - Repository overview with branches, tags, and recent commits
  - File browser with breadcrumb navigation
  - File content viewer with line count and binary detection
  - Commit log per branch
  - Dark theme with ember orange `#FF4500` accent
- **UI API endpoints** (read-only, no auth required):
  - `GET /ui/api/repos` — list repos with metadata
  - `GET /ui/api/repos/{name}` — repo detail (branches, tags, commits)
  - `GET /ui/api/repos/{name}/tree/{ref}` — file tree at ref
  - `GET /ui/api/repos/{name}/blob/{ref}/{path}` — file content
  - `GET /ui/api/repos/{name}/commits/{ref}` — commit log
- **Static file serving** — `static/` directory with `index.html`, `style.css`, `app.js`
- **Health check moved** — `GET /health` (was `GET /`)

### Changed

- Health check endpoint moved from `GET /` to `GET /health` to serve Web UI at root
- Web UI served at `GET /` via the new UI router

---

## [0.4.0] — 2026-06-29

### Added

- **Structured logging** — `logging.py` with `setup_logging()` and `RequestLogMiddleware` for request timing
- **Request logging middleware** — every HTTP request logged with method, path, status, and response time
- **Git hooks support** — `git/hooks.py` with `install_hooks()`, `list_hooks()`, `remove_hook()`, `run_hook()`
  - Default hooks: `pre-receive` (rejects force push to main/master), `post-receive`, `update`
- **Ref management API** — branch and tag management endpoints:
  - `POST /admin/repos/{name}/branches` — create branch
  - `DELETE /admin/repos/{name}/branches/{branch}` — delete branch
  - `GET /admin/repos/{name}/tags` — list tags
- **Hooks API** — hook management endpoints:
  - `GET /admin/repos/{name}/hooks` — list installed hooks
  - `POST /admin/repos/{name}/hooks/{hook}/test` — test a hook manually
- **Health check** — enhanced `GET /` with version, repo count, disk usage stats
- **Lifecycle events** — startup/shutdown logging via FastAPI events

### Changed

- Admin API now includes all endpoints from v0.3.0 plus ref and hook management
- New repos automatically get default hooks installed on creation
- Request logging includes timing in milliseconds

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
