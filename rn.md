# Release Notes — GitFlare

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

- Stable core — full push/pull/branch over HTTP + SSH
- Production hardening

---

## v0.2.0 — Token Auth & Credential Helper

**Date:** 2026-06-26

GitFlare v0.2 adds token-based authentication for HTTP push and a seamless credential helper flow. Repos can now enforce token auth for writes while keeping read access public.

### What's included

- **Token auth on push** — repos with `auth_mode: "token"` or `"both"` require a valid token for `git push`
- **SSH-only repos** — repos with `auth_mode: "ssh"` reject push over HTTP (403), requiring SSH
- **Admin verify endpoint** — `GET /admin/auth/verify` validates tokens against stored bcrypt hashes
- **`gitflare-admin login`** — one-time setup that stores your token in the system keychain and registers the credential helper
- **`gitflare-admin logout`** — cleans up keychain and `~/.gitconfig` entries

### Quick start

```bash
# Server side
gitflare-admin repo create myproject --auth token
gitflare-admin token generate myproject
# → shows token once, store it

# Client side
gitflare-admin login http://yourhost:3000
# → enter token when prompted, done forever

git clone http://yourhost:3000/myproject.git
git push origin master  # just works, no prompts
```

### Auth behavior

| Mode | Clone/Fetch | Push |
|------|-------------|------|
| `ssh` | Public | 403 (use SSH) |
| `token` | Public | Token required |
| `both` | Public | Token required |

---

## v0.1.0 — First Release

**Date:** 2026-06-26

GitFlare v0.1 is the initial working release. It provides a self-hosted Git server that handles HTTP clone, fetch, and push — delegating all protocol handling to Git's own `http-backend`.

### What's included

- **HTTP Smart Protocol** — `git clone`, `git push`, `git pull` over HTTP all work out of the box
- **Repo lifecycle** — create, list, and delete bare Git repos via the admin CLI
- **Token infrastructure** — each repo gets a `gitflare.json` with `auth_mode` and hashed token storage
- **Credential helper** — `git-credential-gitflare` is ready for system keychain integration (activates in v0.2)
- **Admin CLI** — `gitflare-admin` for repo and token management

### Quick start

```bash
pip install -e .
uvicorn gitflare.main:app --port 3000
gitflare-admin repo create myproject
git clone http://localhost:3000/myproject.git
```

### Known limitations

- No auth enforcement yet — all repos are publicly readable/writable over HTTP
- No SSH support (v0.3)
- No web UI (v1.0)
