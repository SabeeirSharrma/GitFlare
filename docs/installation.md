---
title: Installation
description: How to install GitFlare.
order: 2
---

# Installation

GitFlare runs on any system with Python 3.11+ and Git installed.

## Building from Source (Recommended)

GitFlare is built transparently from source. No pre-compiled code is embedded in this repository.

### Prerequisites

- Python 3.11 or later
- Git
- pip

### Install

```bash
git clone https://github.com/TheCinderProject/gitflare.git
cd gitflare
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

This installs GitFlare in editable mode, so changes to the source code take effect immediately.

### Verify Installation

```bash
gitflare --help
gitflare-admin --help
```

## Pre-built Artifacts

Pre-built wheels and source distributions are available on the [Releases](https://github.com/TheCinderProject/gitflare/releases) page. While functional, **building from source is the recommended and preferred method** — it ensures full transparency and allows you to inspect the code before installation.

### Install from wheel

```bash
pip install gitflare-0.3.0-py3-none-any.whl
```

### Verify checksums

Every release includes `sha256sums.txt` for verification:

```bash
sha256sum -c sha256sums.txt
```

## System Dependencies

GitFlare requires Git to be installed on the system. The `git http-backend` and `git-shell` commands must be available on `PATH`.

### Debian/Ubuntu

```bash
sudo apt install git
```

### Arch Linux

```bash
sudo pacman -S git
```

### macOS

```bash
brew install git
```

## Credential Helper (Optional)

The credential helper `git-credential-gitflare` is included in the repository. To make it available system-wide, copy it to a directory on your `PATH`:

```bash
cp git-credential-gitflare /usr/local/bin/
chmod +x /usr/local/bin/git-credential-gitflare
```

Or install via the package:

```bash
pip install -e .
# The helper is available as git-credential-gitflare in the venv
```

## Next Steps

- [Configuration](configuration.md) — configure `gitflare.toml`
- [Authentication](authentication.md) — set up token or SSH auth
- [Deployment](deployment.md) — deploy to a VPS
