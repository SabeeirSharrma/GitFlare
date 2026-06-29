---
title: Authentication
description: Token and SSH authentication in GitFlare.
order: 4
---

# Authentication

GitFlare supports two authentication methods: HTTP tokens and SSH keys. Each repository can be configured with one of three auth modes.

## Auth Modes

| Mode | Clone/Fetch | Push (HTTP) | Push (SSH) |
|------|-------------|-------------|------------|
| `ssh` | Public | 403 (use SSH) | Key required |
| `token` | Public | Token required | N/A |
| `both` | Public | Token required | Key required |

Set the auth mode when creating a repo:

```bash
gitflare-admin repo create myproject --auth ssh
gitflare-admin repo create myproject --auth token
gitflare-admin repo create myproject --auth both
```

## Token Authentication

### How It Works

1. Admin generates a token for a repo: `gitflare-admin token generate myproject`
2. Token is shown once — store it securely
3. User runs `gitflare-admin login http://yourhost:3000` — stores token in system keychain
4. From then on, every `git clone/push/pull` just works — Git calls the credential helper automatically

### Token Flow

```
git clone http://yourhost/myproject.git
  └─▶ git asks credential helper for http://yourhost
        └─▶ git-credential-gitflare get
              └─▶ keyring.get_password("gitflare:yourhost", username)
                    └─▶ returns token silently
                          └─▶ clone proceeds, no prompt
```

### HTTP Basic Auth

GitFlare receives the token as HTTP Basic auth:

```
Authorization: Basic base64(gitflare:<token>)
```

The token is bcrypt-verified against the repo's stored hash in `gitflare.json`.

### Per-Repo Token Storage

Each repo stores its tokens in `gitflare.json`:

```json
{
  "name": "myproject",
  "auth_mode": "token",
  "tokens": ["bcrypt_hashed_token_1", "bcrypt_hashed_token_2"],
  "ssh_keys": []
}
```

Tokens are bcrypt-hashed — the plaintext is never stored.

## SSH Key Authentication

### How It Works

1. User submits public key: `gitflare-admin ssh-key add "ssh-ed25519 AAAA..."`
2. Key is appended to `authorized_keys` with `git-shell` restriction
3. Standard `git clone git@host:repo.git` flow — no credential prompts

### SSH Key Management

```bash
# Add a key
gitflare-admin ssh-key add "ssh-ed25519 AAAA..."

# List keys
gitflare-admin ssh-key list

# Remove a key
gitflare-admin ssh-key remove <key_id>
```

### authorized_keys Format

Each key is added with command restriction:

```
command="git-shell -c \"$SSH_ORIGINAL_COMMAND\"",no-port-forwarding,no-X11-forwarding,no-agent-forwarding ssh-ed25519 AAAA...
```

This ensures:
- The key can only execute git commands via `git-shell`
- No port forwarding, X11 forwarding, or agent forwarding
- The original command (e.g., `git-upload-pack '/repo.git'`) is passed to git-shell

### SSH Handler

`git/ssh_handler.py` validates SSH access and delegates to `git-shell`:

1. Parses the `SSH_ORIGINAL_COMMAND` to extract the repo name
2. Checks if the repo exists
3. Validates the command is allowed (`git-upload-pack`, `git-receive-pack`)
4. Delegates to `git-shell` for execution

## Credential Helper

### `git-credential-gitflare`

The credential helper stores tokens in your system keychain:

- **Linux:** libsecret (GNOME Keyring, KWallet)
- **macOS:** Keychain
- **Windows:** Windows Credential Manager

### How It Works

Git calls the helper as a subprocess with three actions:

| Action | Description |
|--------|-------------|
| `get` | Retrieve token from keychain |
| `store` | Save token to keychain |
| `erase` | Delete token from keychain |

### Manual Setup

The helper can be registered manually in `~/.gitconfig`:

```ini
[credential "http://yourhost:3000"]
    helper = gitflare
```

### Login/Logout

Use the admin CLI for one-time setup:

```bash
# Store token in keychain + register helper
gitflare-admin login http://yourhost:3000

# Remove from keychain + unregister helper
gitflare-admin logout http://yourhost:3000
```

## Per-Repo Metadata

Each repo stores its configuration in `gitflare.json`:

```json
{
  "name": "myproject",
  "auth_mode": "ssh",
  "tokens": ["bcrypt_hashed_token"],
  "ssh_keys": ["ssh-ed25519 AAAA..."]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Repository name |
| `auth_mode` | string | `"ssh"`, `"token"`, or `"both"` |
| `tokens` | list | bcrypt-hashed access tokens |
| `ssh_keys` | list | Authorized SSH public keys |
