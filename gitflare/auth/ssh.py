"""SSH key management for GitFlare."""

import hashlib
from pathlib import Path

from ..config import load_config

KEY_TYPES = ("ssh-ed25519", "ssh-rsa", "ecdsa-sha2-nistp256", "ecdsa-sha2-nistp384", "ecdsa-sha2-nistp521")


def _key_id(pubkey: str) -> str:
    """Generate a short ID from a public key."""
    return hashlib.sha256(pubkey.encode()).hexdigest()[:12]


def add_key(pubkey: str) -> str:
    """Add an SSH public key to authorized_keys.

    Returns the key ID.
    """
    config = load_config()
    key_path = Path(config.ssh.authorized_keys_path)
    key_path.parent.mkdir(parents=True, exist_ok=True)

    key_id = _key_id(pubkey)

    # Validate key format
    parts = pubkey.strip().split()
    if len(parts) < 2 or parts[0] not in KEY_TYPES:
        raise ValueError(f"Invalid public key format. Expected one of: {', '.join(KEY_TYPES)}")

    # Build the command restriction
    # This restricts the key to git-shell for git operations only
    command = (
        f'command="git-shell -c \\"$SSH_ORIGINAL_COMMAND\\"",'
        f'no-port-forwarding,no-X11-forwarding,no-agent-forwarding '
        f"{pubkey.strip()}"
    )

    # Check if key already exists
    if key_path.exists():
        existing = key_path.read_text()
        if pubkey.strip() in existing:
            raise ValueError("Key already exists")

    with open(key_path, "a") as f:
        f.write(command + "\n")

    return key_id


def list_keys() -> list[dict[str, str]]:
    """List all SSH public keys.

    Returns list of dicts with 'id', 'key_type', 'comment'.
    """
    config = load_config()
    key_path = Path(config.ssh.authorized_keys_path)

    if not key_path.exists():
        return []

    keys = []
    for line in key_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Extract the actual key from the command-restricted line
        # Format: command="..." ssh-ed25519 AAAA... comment
        parts = line.split()
        # Find the key type
        for i, part in enumerate(parts):
            if part in KEY_TYPES and i + 1 < len(parts):
                pubkey_parts = parts[i:]
                key_type = pubkey_parts[0]
                comment = pubkey_parts[2] if len(pubkey_parts) > 2 else ""
                key_id = _key_id(" ".join(pubkey_parts))
                keys.append({
                    "id": key_id,
                    "key_type": key_type,
                    "comment": comment,
                })
                break

    return keys


def remove_key(key_id: str) -> bool:
    """Remove an SSH public key by ID.

    Returns True if removed, False if not found.
    """
    config = load_config()
    key_path = Path(config.ssh.authorized_keys_path)

    if not key_path.exists():
        return False

    lines = key_path.read_text().splitlines()
    new_lines = []
    removed = False

    for line in lines:
        if not line.strip() or line.strip().startswith("#"):
            new_lines.append(line)
            continue

        # Check if this line contains the key we want to remove
        parts = line.split()
        for i, part in enumerate(parts):
            if part in KEY_TYPES and i + 1 < len(parts):
                pubkey_parts = parts[i:]
                if _key_id(" ".join(pubkey_parts)) == key_id:
                    removed = True
                    continue
        new_lines.append(line)

    if removed:
        key_path.write_text("\n".join(new_lines) + "\n")

    return removed
