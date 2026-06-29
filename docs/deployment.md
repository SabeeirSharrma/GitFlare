---
title: Deployment
description: Deploying GitFlare to a VPS.
order: 7
---

# Deployment

GitFlare is designed to run on a VPS with minimal setup. This guide covers systemd, Caddy reverse proxy, and SSH configuration.

## Prerequisites

- A VPS running Linux (Ubuntu, Debian, Arch, etc.)
- Python 3.11+ installed
- Git installed
- A domain name pointed at your VPS

## 1. Install GitFlare

```bash
# On the VPS
git clone https://github.com/TheCinderProject/gitflare.git /opt/gitflare
cd /opt/gitflare
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## 2. Configure

Edit `/opt/gitflare/gitflare.toml`:

```toml
[server]
host = "0.0.0.0"
port = 3000
repos_path = "/srv/gitflare/repos"
base_url = "https://git.yourdomain.com"

[auth]
admin_token = "your-secret-admin-token"

[ssh]
enabled = true
port = 2222
authorized_keys_path = "/srv/gitflare/authorized_keys"
```

Generate a secure admin token:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## 3. Create Directories

```bash
sudo mkdir -p /srv/gitflare/repos
sudo useradd -r -s /bin/false gitflare
sudo chown -R gitflare:gitflare /srv/gitflare
sudo chown -R gitflare:gitflare /opt/gitflare
```

## 4. systemd Service

Create `/etc/systemd/system/gitflare.service`:

```ini
[Unit]
Description=GitFlare Git Server
After=network.target

[Service]
Type=simple
User=gitflare
WorkingDirectory=/opt/gitflare
ExecStart=/opt/gitflare/.venv/bin/uvicorn gitflare.main:app --host 0.0.0.0 --port 3000
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable gitflare
sudo systemctl start gitflare
```

Check status:

```bash
sudo systemctl status gitflare
```

## 5. Caddy Reverse Proxy

Install Caddy:

```bash
# Debian/Ubuntu
sudo apt install caddy

# Arch
sudo pacman -S caddy
```

Edit `/etc/caddy/Caddyfile`:

```caddy
git.yourdomain.com {
    reverse_proxy localhost:3000
}
```

Caddy automatically handles HTTPS via Let's Encrypt.

Restart Caddy:

```bash
sudo systemctl restart caddy
```

## 6. SSH Configuration

Since the system SSH daemon is likely on port 22, run GitFlare's SSH on port 2222.

### Configure sshd

Edit `/etc/ssh/sshd_config`:

```bash
# Add GitFlare's authorized_keys
Match User gitflare
    AuthorizedKeysFile /srv/gitflare/authorized_keys
```

Restart sshd:

```bash
sudo systemctl restart sshd
```

### Client Configuration

Users connect via SSH on port 2222:

```bash
git clone ssh://git@yourdomain.com:2222/myproject.git
```

Or add to `~/.ssh/config`:

```
Host gitflare
    HostName yourdomain.com
    Port 2222
    User git
```

Then:

```bash
git clone gitflare:myproject.git
```

## 7. First Use

```bash
# On the server
gitflare-admin repo create myproject --auth ssh
gitflare-admin token generate myproject

# On the client
git clone https://git.yourdomain.com/myproject.git
# or
git clone ssh://git@yourdomain.com:2222/myproject.git
```

## Firewall

Ensure these ports are open:

| Port | Protocol | Service |
|------|----------|---------|
| 80 | TCP | HTTP (Caddy) |
| 443 | TCP | HTTPS (Caddy) |
| 2222 | TCP | SSH (GitFlare) |

### ufw

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 2222/tcp
sudo ufw enable
```

### firewalld

```bash
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --permanent --add-port=2222/tcp
sudo firewall-cmd --reload
```

## Troubleshooting

### Server won't start

Check logs:

```bash
sudo journalctl -u gitflare -f
```

### Can't clone via HTTP

- Check if GitFlare is running: `curl http://localhost:3000/`
- Check Caddy config: `sudo systemctl status caddy`
- Check firewall: `sudo ufw status`

### Can't clone via SSH

- Check if the key is in `authorized_keys`: `gitflare-admin ssh-key list`
- Check sshd config: `sudo systemctl status sshd`
- Test SSH: `ssh -p 2222 git@yourdomain.com`

### Permission denied

- Check repo ownership: `ls -la /srv/gitflare/repos/`
- Check `gitflare.toml` paths
- Check systemd user: `User=gitflare` in the service file
