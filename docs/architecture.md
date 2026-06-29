---
title: Architecture
description: How GitFlare works internally.
order: 6
---

# Architecture

GitFlare is designed as a thin layer on top of Git's own tooling. It never touches Git objects directly — all protocol handling is delegated to `git http-backend` (for HTTP) and `git-shell` (for SSH).

## Overview

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

## HTTP Protocol

### Smart HTTP Endpoints

Git's smart HTTP protocol uses four endpoints:

```
GET  /repo.git/info/refs?service=git-upload-pack   # clone/fetch
POST /repo.git/git-upload-pack                      # clone/fetch data
GET  /repo.git/info/refs?service=git-receive-pack  # push
POST /repo.git/git-receive-pack                    # push data
```

### Request Flow

1. Git client sends request to GitFlare
2. GitFlare extracts the repo name from the path
3. Auth check:
   - For push: verify token if `auth_mode` is `"token"` or `"both"`
   - For push: return 403 if `auth_mode` is `"ssh"`
   - For clone/fetch: always allowed (public read)
4. GitFlare pipes the request to `git http-backend` via subprocess
5. `git http-backend` processes the request and returns a CGI response
6. GitFlare parses the CGI response and returns it to the client

### Git HTTP Backend Wrapper

`gitflare/git/backend.py` handles the subprocess communication:

```python
env = {
    "GIT_PROJECT_ROOT": repos_path,
    "GIT_HTTP_EXPORT_ALL": "1",
    "PATH_INFO": f"/{repo_path}",
    "REQUEST_METHOD": request.method,
    "QUERY_STRING": str(request.url.query),
    "CONTENT_TYPE": request.headers.get("content-type", ""),
}

proc = subprocess.Popen(
    ["git", "http-backend"],
    env=env,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

stdout, stderr = proc.communicate(input=body)
return parse_cgi_response(stdout)
```

### CGI Response Parsing

`git http-backend` outputs CGI format:

```
Status: 200 OK
Content-Type: application/x-git-upload-pack-advertisement

<binary data>
```

GitFlare splits on `\r\n\r\n` to separate headers from the binary body.

## SSH Protocol

### How SSH Works

```
git@host:repo.git  ──▶  sshd  ──▶  git-shell  ──▶  /repos/<name>.git
```

1. SSH client connects to the server
2. `sshd` matches the key against `authorized_keys`
3. The forced command (`git-shell -c "$SSH_ORIGINAL_COMMAND"`) is executed
4. `git-shell` receives the original command (e.g., `git-upload-pack '/repo.git'`)
5. `git-shell` validates and executes the git command on the bare repo

### authorized_keys Format

Each key is added with command restriction:

```
command="git-shell -c \"$SSH_ORIGINAL_COMMAND\"",no-port-forwarding,no-X11-forwarding,no-agent-forwarding ssh-ed25519 AAAA...
```

This ensures:
- The key can only execute git commands
- No port forwarding, X11 forwarding, or agent forwarding
- The original command is passed to git-shell

### SSH Handler

`gitflare/git/ssh_handler.py` validates SSH access:

1. Parses `SSH_ORIGINAL_COMMAND` to extract the repo name
2. Checks if the repo exists
3. Validates the command is allowed
4. Delegates to `git-shell`

## Project Structure

```
gitflare/
├── gitflare/
│   ├── main.py               # FastAPI app entrypoint
│   ├── config.py             # Loads gitflare.toml
│   ├── models.py             # Pydantic models
│   ├── auth/
│   │   ├── tokens.py         # Token generation & bcrypt hashing
│   │   └── ssh.py            # SSH key management
│   ├── git/
│   │   ├── backend.py        # Wraps git http-backend via subprocess
│   │   ├── repo.py           # Repo init, delete, list, metadata
│   │   └── ssh_handler.py    # git-shell integration
│   └── routes/
│       ├── git_http.py       # Smart HTTP protocol routes + token auth
│       └── admin.py          # Admin API (/admin/auth/verify)
├── git-credential-gitflare    # Git credential helper
├── gitflare.toml              # Config file
├── pyproject.toml
└── SPEC.md
```

## Key Principles

1. **No Git object manipulation** — GitFlare delegates to `git http-backend` and `git-shell`
2. **Minimal dependencies** — FastAPI, uvicorn, bcrypt, keyring. No ORM, no database.
3. **Flat file storage** — Each repo has a `gitflare.json` for metadata. No SQLite until v0.3 if needed.
4. **Transparent** — Every line of code is auditable. Build from source recommended.
