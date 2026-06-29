"""Configuration loader for GitFlare."""

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 3000
    repos_path: str = "/srv/gitflare/repos"
    base_url: Optional[str] = None


@dataclass
class AuthConfig:
    admin_token: str = ""


@dataclass
class SSHConfig:
    enabled: bool = True
    port: int = 2222
    authorized_keys_path: str = "/srv/gitflare/authorized_keys"


@dataclass
class Config:
    server: ServerConfig
    auth: AuthConfig
    ssh: SSHConfig


def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration from gitflare.toml."""
    if config_path is None:
        config_path = Path("gitflare.toml")

    if not config_path.exists():
        return Config(
            server=ServerConfig(),
            auth=AuthConfig(),
            ssh=SSHConfig(),
        )

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    server_data = data.get("server", {})
    auth_data = data.get("auth", {})
    ssh_data = data.get("ssh", {})

    return Config(
        server=ServerConfig(
            host=server_data.get("host", "0.0.0.0"),
            port=server_data.get("port", 3000),
            repos_path=server_data.get("repos_path", "/srv/gitflare/repos"),
            base_url=server_data.get("base_url"),
        ),
        auth=AuthConfig(
            admin_token=auth_data.get("admin_token", ""),
        ),
        ssh=SSHConfig(
            enabled=ssh_data.get("enabled", True),
            port=ssh_data.get("port", 2222),
            authorized_keys_path=ssh_data.get("authorized_keys_path", "/srv/gitflare/authorized_keys"),
        ),
    )
