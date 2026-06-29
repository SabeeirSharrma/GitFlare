# Release Notes — GitFlare

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

### What's next (v0.3)

- SSH key auth
- Per-repo SSH key management
- `git-shell` integration

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
