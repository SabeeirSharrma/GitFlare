"""Pydantic models for GitFlare."""

from typing import Optional
from pydantic import BaseModel


class RepoMetadata(BaseModel):
    """Metadata stored in gitflare.json inside each bare repo."""
    name: str
    auth_mode: str = "ssh"  # "token", "ssh", or "both"
    tokens: list[str] = []  # bcrypt hashed tokens
    ssh_keys: list[str] = []


class TokenResponse(BaseModel):
    """Response when generating a token."""
    repo: str
    token: str  # plaintext, shown once
    message: str = "Store this token securely. It will not be shown again."


class AdminResponse(BaseModel):
    """Generic admin API response."""
    success: bool
    message: str
