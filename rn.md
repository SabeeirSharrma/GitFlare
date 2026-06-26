# Release Notes — GitFlare

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

### What's next (v0.2)

- Token auth enforcement on HTTP endpoints
- `gitflare-admin login` / `logout` commands
- Full credential helper flow with `keyring`
- HTTP push auth with bcrypt token verification

### Known limitations

- No auth enforcement yet — all repos are publicly readable/writable over HTTP
- No SSH support (v0.3)
- No web UI (v1.0)
