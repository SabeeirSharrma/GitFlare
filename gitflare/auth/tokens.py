"""Token generation and validation for GitFlare."""

import secrets
import bcrypt


def generate_token(length: int = 32) -> str:
    """Generate a random hex token."""
    return secrets.token_hex(length)


def hash_token(token: str) -> str:
    """Hash a token using bcrypt."""
    return bcrypt.hashpw(token.encode(), bcrypt.gensalt()).decode()


def verify_token(token: str, hashed: str) -> bool:
    """Verify a token against its bcrypt hash."""
    return bcrypt.checkpw(token.encode(), hashed.encode())
