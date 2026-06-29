---
title: Configuration
description: Configuring GitFlare via gitflare.toml.
order: 3
---

# Configuration

GitFlare stores its configuration at `gitflare.toml` in the project root. The file is loaded on server startup.

## Configuration File

```toml
[server]
host = "0.0.0.0"
port = 3000
repos_path = "/srv/gitflare/repos"

# Optional — only set if you want GitFlare to emit full clone URLs
# base_url = "https://git.yourdomain.com"

[auth]
admin_token = "your-secret-admin-token"

[ssh]
enabled = true
port = 2222
authorized_keys_path = "/srv/gitflare/authorized_keys"
```

## Options

### `[server]`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `host` | string | `"0.0.0.0"` | Address to bind the server to |
| `port` | integer | `3000` | Port to listen on |
| `repos_path` | string | `"/srv/gitflare/repos"` | Directory where bare Git repos are stored |
| `base_url` | string | `None` | Optional base URL for emitting full clone URLs in API responses |

### `host`

The network address to bind to. Use `"0.0.0.0"` to listen on all interfaces, or `"127.0.0.1"` for local-only access.

### `port`

The port the HTTP server listens on. Default is `3000`.

### `repos_path`

Directory where bare Git repositories are stored. Each repo is a subdirectory ending in `.git` (e.g., `myproject.git`). The directory is created automatically if it doesn't exist.

### `base_url`

Optional. If set, GitFlare will use this URL when generating clone URLs in admin API responses or the future web UI. If unset, GitFlare works purely locally with no absolute URL generation.

### `[auth]`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `admin_token` | string | `""` | Admin token for API access |

### `admin_token`

The admin token is used for Bearer authentication on admin API routes. In v0.4+, this will be required for all admin API calls.

For now, the admin token is used by `gitflare-admin login` to validate credentials before storing them.

### `[ssh]`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | boolean | `true` | Enable SSH support |
| `port` | integer | `2222` | Port for the SSH server |
| `authorized_keys_path` | string | `"/srv/gitflare/authorized_keys"` | Path to the authorized_keys file |

### `enabled`

Controls whether SSH support is enabled. When enabled, GitFlare manages the `authorized_keys` file for SSH key authentication.

### `port`

The port for the SSH server. Since port 22 is typically used by the system SSH daemon, GitFlare uses port 2222 by default.

### `authorized_keys_path`

Path to the `authorized_keys` file where SSH public keys are stored. GitFlare appends keys with `git-shell` restriction for security.

## Environment Variables

GitFlare does not use environment variables for configuration. All configuration is in `gitflare.toml`.

## Default Configuration

If no `gitflare.toml` file exists, GitFlare uses these defaults:

```toml
[server]
host = "0.0.0.0"
port = 3000
repos_path = "/srv/gitflare/repos"

[auth]
admin_token = ""

[ssh]
enabled = true
port = 2222
authorized_keys_path = "/srv/gitflare/authorized_keys"
```
