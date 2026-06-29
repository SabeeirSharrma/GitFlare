"""Git repository operations."""

import json
import subprocess
from pathlib import Path

from ..models import RepoMetadata


def init_bare(repos_path: str, name: str, auth_mode: str = "ssh") -> Path:
    """Initialize a bare git repository.

    Args:
        repos_path: Base path where repos are stored
        name: Repository name (without .git extension)
        auth_mode: Auth mode ("token", "ssh", or "both")

    Returns:
        Path to the created repository
    """
    from .hooks import install_hooks

    repo_path = Path(repos_path) / f"{name}.git"
    repo_path.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        ["git", "init", "--bare", str(repo_path)],
        check=True,
        capture_output=True,
    )

    # Enable HTTP receive-pack so push works over HTTP
    subprocess.run(
        ["git", "config", "-f", str(repo_path / "config"), "http.receivepack", "true"],
        check=True,
        capture_output=True,
    )

    # Write gitflare.json metadata
    metadata = RepoMetadata(name=name, auth_mode=auth_mode)
    with open(repo_path / "gitflare.json", "w") as f:
        json.dump(metadata.model_dump(), f, indent=2)

    # Install default hooks
    install_hooks(repo_path)

    return repo_path


def delete_repo(repos_path: str, name: str) -> bool:
    """Delete a git repository.

    Args:
        repos_path: Base path where repos are stored
        name: Repository name (without .git extension)

    Returns:
        True if deleted, False if not found
    """
    import shutil

    repo_path = Path(repos_path) / f"{name}.git"
    if repo_path.exists() and repo_path.is_dir():
        shutil.rmtree(repo_path)
        return True
    return False


def list_repos(repos_path: str) -> list[str]:
    """List all repositories.

    Args:
        repos_path: Base path where repos are stored

    Returns:
        List of repository names (without .git extension)
    """
    repos_dir = Path(repos_path)
    if not repos_dir.exists():
        return []

    return [
        p.stem
        for p in repos_dir.iterdir()
        if p.is_dir() and p.suffix == ".git"
    ]


def repo_exists(repos_path: str, name: str) -> bool:
    """Check if a repository exists.

    Args:
        repos_path: Base path where repos are stored
        name: Repository name (without .git extension)

    Returns:
        True if repo exists
    """
    repo_path = Path(repos_path) / f"{name}.git"
    return repo_path.exists() and repo_path.is_dir()


def get_metadata(repos_path: str, name: str) -> RepoMetadata | None:
    """Read gitflare.json from a repo.

    Returns:
        RepoMetadata if repo exists and has metadata, None otherwise
    """
    repo_path = Path(repos_path) / f"{name}.git" / "gitflare.json"
    if not repo_path.exists():
        return None
    with open(repo_path) as f:
        return RepoMetadata.model_validate_json(f.read())


def save_metadata(repos_path: str, name: str, metadata: RepoMetadata) -> None:
    """Write gitflare.json to a repo."""
    repo_path = Path(repos_path) / f"{name}.git" / "gitflare.json"
    with open(repo_path, "w") as f:
        json.dump(metadata.model_dump(), f, indent=2)
