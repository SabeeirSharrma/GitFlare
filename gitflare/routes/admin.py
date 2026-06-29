"""Admin API routes for GitFlare."""

import subprocess

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response

from ..auth.ssh import add_key, list_keys, remove_key
from ..auth.tokens import generate_token, hash_token, verify_token
from ..config import load_config
from ..git.repo import (
    delete_repo,
    get_metadata,
    init_bare,
    list_repos,
    save_metadata,
)
from ..models import AdminResponse, TokenResponse

router = APIRouter(prefix="/admin")


# --- Auth dependency ---

def _verify_admin_auth(authorization: str = Header(None)) -> None:
    """Verify Bearer token matches admin_token from config."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization[7:]
    config = load_config()

    if not config.auth.admin_token:
        raise HTTPException(status_code=500, detail="Admin token not configured")

    if not verify_token(token, config.auth.admin_token):
        raise HTTPException(status_code=403, detail="Invalid admin token")


# --- Existing route (no auth for login flow) ---

@router.get("/auth/verify")
def verify_auth(repo: str = Query(...), token: str = Query(...)) -> Response:
    """Verify a token against a repo's stored hashes.

    Used by `gitflare-admin login` to validate credentials before storing.
    """
    config = load_config()
    meta = get_metadata(config.server.repos_path, repo)

    if not meta:
        return Response(status_code=404, content="Repository not found")

    for hashed in meta.tokens:
        if verify_token(token, hashed):
            return Response(status_code=200, content="OK")

    return Response(status_code=401, content="Invalid token")


# --- Repo endpoints ---

@router.get("/repos")
def get_repos(_: None = Depends(_verify_admin_auth)) -> list[dict]:
    """List all repositories."""
    config = load_config()
    repos = list_repos(config.server.repos_path)
    result = []
    for name in repos:
        meta = get_metadata(config.server.repos_path, name)
        result.append({
            "name": name,
            "auth_mode": meta.auth_mode if meta else "unknown",
        })
    return result


@router.post("/repos")
def create_repo(
    name: str = Query(...),
    auth_mode: str = Query("ssh", pattern="^(ssh|token|both)$"),
    _: None = Depends(_verify_admin_auth),
) -> AdminResponse:
    """Create a new repository."""
    config = load_config()
    try:
        init_bare(config.server.repos_path, name, auth_mode=auth_mode)
        return AdminResponse(success=True, message=f"Repository '{name}' created")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/repos/{name}")
def delete_repo_endpoint(name: str, _: None = Depends(_verify_admin_auth)) -> AdminResponse:
    """Delete a repository."""
    config = load_config()
    if delete_repo(config.server.repos_path, name):
        return AdminResponse(success=True, message=f"Repository '{name}' deleted")
    raise HTTPException(status_code=404, detail="Repository not found")


@router.get("/repos/{name}/branches")
def list_branches(name: str, _: None = Depends(_verify_admin_auth)) -> list[dict]:
    """List branches in a repository."""
    config = load_config()
    repo_path = f"{config.server.repos_path}/{name}.git"

    try:
        result = subprocess.run(
            ["git", "-C", repo_path, "branch", "-a", "--format=%(refname:short)"],
            capture_output=True,
            text=True,
            check=True,
        )
        branches = [b.strip() for b in result.stdout.splitlines() if b.strip()]
        return [{"name": b} for b in branches]
    except subprocess.CalledProcessError:
        raise HTTPException(status_code=404, detail="Repository not found or empty")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Git not available")


@router.get("/repos/{name}/commits")
def list_commits(
    name: str,
    branch: str = Query("HEAD"),
    limit: int = Query(20, ge=1, le=100),
    _: None = Depends(_verify_admin_auth),
) -> list[dict]:
    """List recent commits in a repository."""
    config = load_config()
    repo_path = f"{config.server.repos_path}/{name}.git"

    try:
        result = subprocess.run(
            [
                "git", "-C", repo_path, "log",
                branch,
                f"-{limit}",
                "--format=%H|%s|%an|%ai",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        commits = []
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            parts = line.split("|", 3)
            if len(parts) == 4:
                commits.append({
                    "hash": parts[0],
                    "message": parts[1],
                    "author": parts[2],
                    "date": parts[3],
                })
        return commits
    except subprocess.CalledProcessError:
        raise HTTPException(status_code=404, detail="Repository not found or empty")


# --- Token endpoints ---

@router.post("/repos/{name}/token")
def generate_repo_token(name: str, _: None = Depends(_verify_admin_auth)) -> TokenResponse:
    """Generate an access token for a repository."""
    config = load_config()
    meta = get_metadata(config.server.repos_path, name)
    if not meta:
        raise HTTPException(status_code=404, detail="Repository not found")

    token = generate_token()
    hashed = hash_token(token)
    meta.tokens.append(hashed)
    save_metadata(config.server.repos_path, name, meta)

    return TokenResponse(repo=name, token=token)


@router.delete("/repos/{name}/token")
def revoke_repo_tokens(name: str, _: None = Depends(_verify_admin_auth)) -> AdminResponse:
    """Revoke all tokens for a repository."""
    config = load_config()
    meta = get_metadata(config.server.repos_path, name)
    if not meta:
        raise HTTPException(status_code=404, detail="Repository not found")

    count = len(meta.tokens)
    meta.tokens = []
    save_metadata(config.server.repos_path, name, meta)

    return AdminResponse(success=True, message=f"Revoked {count} token(s)")


# --- SSH key endpoints ---

@router.get("/ssh-keys")
def get_ssh_keys(_: None = Depends(_verify_admin_auth)) -> list[dict]:
    """List all SSH keys."""
    return list_keys()


@router.post("/ssh-keys")
def add_ssh_key(key: str = Query(...), _: None = Depends(_verify_admin_auth)) -> AdminResponse:
    """Add an SSH public key."""
    try:
        key_id = add_key(key)
        return AdminResponse(success=True, message=f"SSH key added (ID: {key_id})")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/ssh-keys/{key_id}")
def remove_ssh_key(key_id: str, _: None = Depends(_verify_admin_auth)) -> AdminResponse:
    """Remove an SSH key by ID."""
    if remove_key(key_id):
        return AdminResponse(success=True, message=f"SSH key {key_id} removed")
    raise HTTPException(status_code=404, detail="Key not found")
