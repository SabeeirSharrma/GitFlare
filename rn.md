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
    