---
title: Admin CLI
description: Reference for the gitflare-admin command-line tool.
order: 5
---

# Admin CLI

`gitflare-admin` is the command-line tool for managing GitFlare repositories, tokens, and SSH keys.

## Usage

```bash
gitflare-admin <command> [subcommand] [options]
```

## Commands

### Authentication

#### `login`

Store credentials for a GitFlare host in the system keychain.

```bash
gitflare-admin login <url>
```

| Argument | Description |
|----------|-------------|
| `url` | GitFlare server URL (e.g., `http://yourhost:3000`) |

**What it does:**
1. Prompts for a token (hidden input)
2. Validates the token against the server
3. Stores the token in the system keychain
4. Registers `git-credential-gitflare` in `~/.gitconfig`

**Example:**

```bash
$ gitflare-admin login http://yourhost:3000
Token: ████████████████
✓ Token stored in system keychain for yourhost:3000
✓ Registered git-credential-gitflare for http://yourhost:3000
```

#### `logout`

Remove credentials for a GitFlare host.

```bash
gitflare-admin logout <url>
```

| Argument | Description |
|----------|-------------|
| `url` | GitFlare server URL |

**Example:**

```bash
$ gitflare-admin logout http://yourhost:3000
✓ Credentials removed from keychain for yourhost:3000
✓ Removed credential helper entry from ~/.gitconfig
```

---

### Repository Management

#### `repo create`

Create a new bare Git repository.

```bash
gitflare-admin repo create <name> [--auth ssh|token|both]
```

| Argument | Description |
|----------|-------------|
| `name` | Repository name |
| `--auth` | Auth mode (default: `ssh`) |

**Example:**

```bash
$ gitflare-admin repo create myproject --auth ssh
✓ Repository 'myproject' created at /srv/gitflare/repos/myproject.git
  Auth mode: ssh
```

#### `repo list`

List all repositories with their auth modes.

```bash
gitflare-admin repo list
```

**Example:**

```bash
$ gitflare-admin repo list
Repositories:
  - myproject (auth: ssh)
  - cpac (auth: token)
```

#### `repo delete`

Delete a repository.

```bash
gitflare-admin repo delete <name>
```

| Argument | Description |
|----------|-------------|
| `name` | Repository name |

**Example:**

```bash
$ gitflare-admin repo delete myproject
✓ Repository 'myproject' deleted
```

---

### Token Management

#### `token generate`

Generate an access token for a repository.

```bash
gitflare-admin token generate <repo>
```

| Argument | Description |
|----------|-------------|
| `repo` | Repository name |

**Example:**

```bash
$ gitflare-admin token generate myproject
✓ Token generated for 'myproject'
  Token: af539193f3331eade5f059c7d35e46255823ba613baaef27e294a132b651c8dd
  Store this securely. It will not be shown again.
```

> **Important:** The token is shown only once. Store it securely.

#### `token revoke`

Revoke all tokens for a repository.

```bash
gitflare-admin token revoke <repo>
```

| Argument | Description |
|----------|-------------|
| `repo` | Repository name |

**Example:**

```bash
$ gitflare-admin token revoke myproject
✓ Revoked 2 token(s) for 'myproject'
```

---

### SSH Key Management

#### `ssh-key add`

Add an SSH public key to the authorized_keys file.

```bash
gitflare-admin ssh-key add "<public_key>"
```

| Argument | Description |
|----------|-------------|
| `public_key` | SSH public key (e.g., `ssh-ed25519 AAAA...`) |

**Example:**

```bash
$ gitflare-admin ssh-key add "ssh-ed25519 AAAA..."
✓ SSH key added (ID: a1b2c3d4e5f6)
```

#### `ssh-key list`

List all SSH keys.

```bash
gitflare-admin ssh-key list
```

**Example:**

```bash
$ gitflare-admin ssh-key list
SSH Keys:
  [a1b2c3d4e5f6] ssh-ed25519 user@host
  [f6e5d4c3b2a1] ssh-rsa user@machine
```

#### `ssh-key remove`

Remove an SSH key by ID.

```bash
gitflare-admin ssh-key remove <key_id>
```

| Argument | Description |
|----------|-------------|
| `key_id` | Key ID (from `ssh-key list`) |

**Example:**

```bash
$ gitflare-admin ssh-key remove a1b2c3d4e5f6
✓ SSH key a1b2c3d4e5f6 removed
```

---

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | Error (invalid arguments, not found, auth failed) |

## Examples

### Complete Workflow

```bash
# 1. Create a repo with token auth
gitflare-admin repo create myproject --auth token

# 2. Generate a token
gitflare-admin token generate myproject

# 3. On the client machine, login
gitflare-admin login http://yourhost:3000

# 4. Clone and push — just works
git clone http://yourhost:3000/myproject.git
cd myproject
echo "hello" > README.md
git add . && git commit -m "init" && git push origin master
```

### SSH Workflow

```bash
# 1. Create a repo with SSH auth
gitflare-admin repo create myproject --auth ssh

# 2. Add your SSH key
gitflare-admin ssh-key add "ssh-ed25519 AAAA..."

# 3. Clone via SSH
git clone ssh://git@yourhost:2222/myproject.git
```
