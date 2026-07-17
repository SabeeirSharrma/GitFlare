# Release Notes — GitFlare

---

## v0.5.0 — Web UI

**Date:** 2026-07-17

GitFlare v0.5 adds a web interface for browsing repositories. Browse your repos, view files, check commit logs, and switch branches — all from your browser.

### What's included

- **Web UI** — static SPA served at `/` with dark theme
  - Repository listing with latest commit info
  - Repository overview (branches, tags, recent commits)
  - File browser with breadcrumb navigation
  - File content viewer with line count
  - Commit log per branch
  - Binary file detection
- **UI API endpoints** — read-only, no auth required
- **Clone URL copy** — one-click copy for clone URLs

### New API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/ui/api/repos` | List repos with metadata |
| `GET` | `/ui/api/repos/{name}` | Repo detail (branches, tags, commits) |
| `GET` | `/ui/api/repos/{name}/tree/{ref}` | File tree at ref |
| `GET` | `/ui/api/repos/{name}/tree/{ref}/{path}` | File tree at path |
| `GET` | `/ui/api/repos/{name}/blob/{ref}/{path}` | File content |
| `GET` | `/ui/api/repos/{name}/commits/{ref}` | Commit log |

### Changed

- Health check moved from `GET /` to `GET /health`
- Web UI now served at `GET /`

### Quick start

```bash
# Start the server
uvicorn gitflare.main:app --host 0.0.0.0 --port 3000

# Open in browser
open http://localhost:3000/

# Health check (moved)
curl http://localhost:3000/health
```

### What's next (v1.0)

- Production-ready release

---

## v0.4.0 — Stable Core

**Date:** 2026-06-29

GitFlare v0.4 adds structured logging, request timing, git hooks support, branch/tag management, and an enhanced health check endpoint. This release focuses on production hardening and a stable core.

### What's included

- **Structured logging** — `RequestLogMiddleware` logs every HTTP request with method, path, status, and response time in milliseconds
- **Git hooks** — new repos get `pre-receive`, `post-receive`, and `update` hooks by default
  - `pre-receive` rejects force pushes and branch deletion on `main`/`master`
- **Branch management** — create and delete branches via the admin API
- **Tags listing** — list tags for any repo
- **Hooks API** — list installed hooks and test them manually
- **Health check** — `GET /` now returns version, repo count, and disk usage stats
- **Lifecycle logging** — startup and shutdown events are logged

### New API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/admin/repos/{name}/branches` | Create branch |
| `DELETE` | `/admin/repos/{name}/branches/{branch}` | Delete branch |
| `GET` | `/admin/repos/{name}/tags` | List tags |
| `GET` | `/admin/repos/{name}/hooks` | List installed hooks |
| `POST` | `/admin/repos/{name}/hooks/{hook}/test` | Test a hook |

### Quick start

```bash
# Start the server
uvicorn gitflare.main:app --host 0.0.0.0 --port 3000

# Health check
curl http://localhost:3000/

# Create a branch
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:3000/admin/repos/myproject/branches?branch=dev&ref=master"

# Test pre-receive hook
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:3000/admin/repos/myproject/hooks/pre-receive/test"
```

### What's next (v0.5)

- Web UI — repo browser, file tree, commit log, branch switcher

---

## v0.3.0 — SSH, Admin API & Branch Listing

**Date:** 2026-06-26

GitFlare v0.3 adds SSH key authentication, a full REST admin API with Bearer auth, branch listing, and commit history endpoints. This release consolidates SSH support, the admin API, and repository management into a single stable release.

### What's included

- **SSH key management** — `gitflare-admin ssh-key add|list|remove` for managing authorized keys
- **SSH handler** — `git/ssh_handler.py` validates SSH access and delegates to git-shell
- **Per-repo key restriction** — keys are added with `git-shell -c` command restriction
- **Admin REST API** — complete CRUD for repos, tokens, and SSH keys with Bearer auth
- **Branch listing** — `GET /admin/repos/{name}/branches`
- **Commit history** — `GET /admin/repos/{name}/commits` with pagination
- **Linting + type checking** — ruff and mypy configured for code quality

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/admin/repos` | List all repos |
| `POST` | `/admin/repos` | Create repo |
| `DELETE` | `/admin/repos/{name}` | Delete repo |
| `GET` | `/admin/repos/{name}/branches` | List branches |
| `GET` | `/admin/repos/{name}/commits` | List commits |
| `POST` | `/admin/repos/{name}/token` | Generate token |
| `DELETE` | `/admin/repos/{name}/token` | Revoke tokens |
| `GET` | `/admin/ssh-keys` | List SSH keys |
| `POST` | `/admin/ssh-keys` | Add SSH key |
| `DELETE` | `/admin/ssh-keys/{key_id}` | Remove SSH key |

### Quick start

```bash
# SSH key management
gitflare-admin ssh-key add "ssh-ed25519 AAAA..."
gitflare-admin ssh-key list

# Admin API (set ADMIN_TOKEN from gitflare.toml)
curl -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:3000/admin/repos
curl -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:3000/admin/repos/myproject/branches
```

### What's next (v0.4)

- Stable core — structured logging, git hooks, ref management
- Production hardening

---

## v0.2.0 — Token Auth

**Date:** 2026-06-26

### Added

- Token auth enforcement on push (HTTP Basic auth → bcrypt verify)
- `GET /admin/auth/verify` endpoint for token validation
- `gitflare-admin login` — stores token in system keychain + registers credential helper
- `gitflare-admin logout` — removes token from keychain + unregisters helper

### Changed

- SSH-only repos (`auth_mode: "ssh"`) now reject push over HTTP with 403
- Clone/fetch remains public for all auth modes (read-only access)

---

## v0.1.0 — Initial Release

**Date:** 2026-06-26

### Added

- Core server — FastAPI + uvicorn, config loading from `gitflare.toml`
- Git HTTP backend — subprocess wrapper for `git http-backend`, CGI response parsing
- Smart HTTP routes — catch-all handler for clone/fetch/push over HTTP
- Repo management — `git init --bare` wrapper, list, delete
- Admin CLI — `gitflare-admin repo create|list|delete`, `gitflare-admin token generate|revoke`
- Token infrastructure — per-repo `gitflare.json` metadata with `auth_mode`, `tokens[]`, `ssh_keys[]`
- Auth module — `auth/tokens.py` with `generate_token()`, `hash_token()`, `verify_token()` using bcrypt
- Credential helper — `git-credential-gitflare` for system keychain integration
- Health check — `GET /` returns service status
- SPEC.md — full architecture and project specification
