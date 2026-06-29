---
title: Port Forwarding
description: Exposing GitFlare through NAT, tunnels, and reverse proxies.
order: 8
---

# Port Forwarding

If your GitFlare instance runs behind NAT (home server, VPS without public IP, etc.), you need a way to expose it to the internet. This guide covers several approaches.

## Quick Reference

| Method | Best For | Requires Public IP | Difficulty |
|--------|----------|-------------------|------------|
| Router Port Forwarding | Home servers with static IP | Yes | Easy |
| Cloudflare Tunnel | Anyone with a domain | No | Easy |
| FRP | Self-hosted reverse proxy | Yes (on server) | Medium |
| Reverse SSH Tunnel | Quick temporary access | Yes (on server) | Medium |
| Tailscale | Private networks, dev | No | Easy |
| ngrok | Testing only | No | Easy |

---

## 1. Router Port Forwarding

The simplest method if you have a public IP and can configure your router.

### Setup

1. Log into your router (usually `192.168.1.1` or `192.168.0.1`)
2. Find "Port Forwarding" or "Virtual Server" settings
3. Add rules:

| Service | External Port | Internal IP | Internal Port | Protocol |
|---------|---------------|-------------|---------------|----------|
| GitFlare HTTP | 443 (or 80) | 192.168.1.x | 3000 | TCP |
| GitFlare SSH | 2222 | 192.168.1.x | 2222 | TCP |

4. Save and apply

### DNS

Point your domain to your public IP:

```
git.yourdomain.com  →  YOUR_PUBLIC_IP
```

### Behind CGNAT?

If your ISP uses CGNAT (you get a `10.x.x.x` or `100.x.x.x` public IP), port forwarding won't work. Use one of the tunnel methods below.

---

## 2. Cloudflare Tunnel

Recommended. Free, secure, no public IP needed. Works behind NAT/CGNAT.

### Prerequisites

- A Cloudflare account
- A domain added to Cloudflare
- `cloudflared` installed

### Install cloudflared

```bash
# Debian/Ubuntu
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb

# Arch
sudo pacman -S cloudflared

# macOS
brew install cloudflare/cloudflare/cloudflared
```

### Authenticate

```bash
cloudflared tunnel login
```

This opens a browser. Select your domain.

### Create a tunnel

```bash
cloudflared tunnel create gitflare
```

Note the tunnel ID from the output.

### Configure

Create `~/.cloudflared/config.yml`:

```yaml
tunnel: <TUNNEL_ID>
credentials-file: /home/user/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: git.yourdomain.com
    service: http://localhost:3000
  - service: http_status:404
```

### Route DNS

```bash
cloudflared tunnel route dns gitflare git.yourdomain.com
```

### Run the tunnel

```bash
cloudflared tunnel run gitflare
```

### Run as service

```bash
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

### SSH over Cloudflare Tunnel

Cloudflare Tunnels can also proxy SSH. Add to your config:

```yaml
ingress:
  - hostname: git.yourdomain.com
    service: http://localhost:3000
  - hostname: ssh.yourdomain.com
    service: ssh://localhost:2222
  - service: http_status:404
```

Then configure your SSH client (`~/.ssh/config`):

```
Host gitflare
    HostName ssh.yourdomain.com
    User git
    ProxyCommand cloudflared access ssh --hostname %h
```

---

## 3. FRP (Fast Reverse Proxy)

Self-hosted reverse proxy. Requires a VPS with a public IP.

### Architecture

```
Home Server (NAT)  ──▶  frpc  ──▶  VPS (public IP)  ──▶  Internet
                                    frps
```

### Setup on VPS (server)

Install frps:

```bash
# Download
wget https://github.com/fatedier/frp/releases/download/v0.61.1/frp_0.61.1_linux_amd64.tar.gz
tar xzf frp_0.61.1_linux_amd64.tar.gz
cd frp_0.61.1_linux_amd64

# Install
sudo cp frps /usr/local/bin/
sudo mkdir -p /etc/frp
```

Create `/etc/frp/frps.toml`:

```toml
bindPort = 7000
auth.token = "your-secret-token"
```

Create systemd service `/etc/systemd/system/frps.service`:

```ini
[Unit]
Description=FRP Server
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/frps -c /etc/frp/frps.toml
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Start:

```bash
sudo systemctl enable frps
sudo systemctl start frps
```

### Setup on Home Server (client)

Install frpc:

```bash
# Same download as above, but use frpc binary
sudo cp frpc /usr/local/bin/
```

Create `/etc/frp/frpc.toml`:

```toml
serverAddr = "your-vps-ip.com"
serverPort = 7000
auth.token = "your-secret-token"

[[proxies]]
name = "gitflare-http"
type = "tcp"
localIP = "127.0.0.1"
localPort = 3000
remotePort = 80

[[proxies]]
name = "gitflare-ssh"
type = "tcp"
localIP = "127.0.0.1"
localPort = 2222
remotePort = 2222
```

Start:

```bash
frpc -c /etc/frp/frpc.toml
```

### DNS

Point your domain to the VPS:

```
git.yourdomain.com  →  VPS_PUBLIC_IP
```

---

## 4. Reverse SSH Tunnel

Quick and temporary. Requires a VPS with a public IP.

### Setup

On your home server, run:

```bash
ssh -R 0.0.0.0:80:localhost:3000 -R 0.0.0.0:2222:localhost:2222 user@your-vps.com -N
```

This forwards:
- VPS port 80 → Home server port 3000 (GitFlare HTTP)
- VPS port 2222 → Home server port 2222 (GitFlare SSH)

### Make it persistent

Use `autossh` for automatic reconnection:

```bash
sudo apt install autossh

autossh -M 0 -f -N -R 0.0.0.0:80:localhost:3000 -R 0.0.0.0:2222:localhost:2222 user@your-vps.com
```

### Systemd service

Create `/etc/systemd/system/gitflare-tunnel.service`:

```ini
[Unit]
Description=GitFlare Reverse SSH Tunnel
After=network.target

[Service]
Type=simple
User=gitflare
ExecStart=/usr/bin/autossh -M 0 -N -R 0.0.0.0:80:localhost:3000 -R 0.0.0.0:2222:localhost:2222 user@your-vps.com
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### VPS sshd config

On the VPS, ensure `/etc/ssh/sshd_config` allows binding to privileged ports:

```
GatewayPorts yes
```

---

## 5. Tailscale

Mesh VPN. Best for private networks or development. No public IP needed.

### Install Tailscale

```bash
# Debian/Ubuntu
curl -fsSL https://tailscale.com/install.sh | sh

# Arch
sudo pacman -S tailscale

# macOS
brew install tailscale
```

### Start Tailscale

```bash
sudo tailscale up
```

Follow the auth URL to log in.

### Install on all devices

Install Tailscale on both the server running GitFlare and your client machines.

### Access GitFlare

Get the Tailscale IP of your GitFlare server:

```bash
tailscale ip -4
# Example output: 100.64.0.1
```

Clone using the Tailscale IP:

```bash
git clone http://100.64.0.1:3000/myproject.git
```

### Custom DNS (optional)

In the Tailscale admin console, you can set a custom domain name for your device. Then use:

```bash
git clone http://gitflare:3000/myproject.git
```

### Tailscale Funnel (public access)

To expose GitFlare publicly through Tailscale:

```bash
sudo tailscale funnel --bg 3000
```

This gives you a public URL like `https://your-device.tail12345.ts.net`.

---

## 6. ngrok

Quick testing only. Not recommended for production.

### Install ngrok

```bash
# Debian/Ubuntu
curl -s https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz | sudo tar -xz -C /usr/local/bin

# Arch
sudo pacman -S ngrok
```

### Authenticate

```bash
ngrok config add-authtoken YOUR_TOKEN
```

### Run

```bash
ngrok http 3000
```

ngrok gives you a public URL like `https://abc123.ngrok-free.app`.

### Use with GitFlare

```bash
git clone https://abc123.ngrok-free.app/myproject.git
```

---

## Recommended Setup

For production with a domain:

1. **Cloudflare Tunnel** — easiest, free, no public IP needed
2. **Router port forwarding** — if you have a static public IP
3. **FRP** — if you want full control and have a VPS

For development/testing:

1. **Tailscale** — private, secure, zero config
2. **ngrok** — quick and dirty for testing

---

## Troubleshooting

### Connection refused

- Check if GitFlare is running: `curl http://localhost:3000/`
- Check firewall: `sudo ufw status` or `sudo iptables -L`
- Check tunnel status (if using)

### DNS not resolving

- Check DNS propagation: `dig git.yourdomain.com`
- Wait for DNS TTL (usually 5-15 minutes)

### SSH connection fails

- Ensure port 2222 is open on all firewalls
- Check SSH config: `ssh -vvv -p 2222 git@yourdomain.com`
- Verify `authorized_keys` has the correct key

### Cloudflare Tunnel 502 error

- Ensure GitFlare is running and responding on localhost:3000
- Check cloudflared logs: `journalctl -u cloudflared -f`
- Verify the tunnel config points to the correct port
