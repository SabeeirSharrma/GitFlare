"""Web UI routes and API endpoints for GitFlare."""

import subprocess
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, FileResponse

from ..config import load_config
from ..git.repo import get_metadata, list_repos, repo_exists

router = APIRouter()
STATIC_DIR = Path(__file__).parent.parent / "static"


def _repo_path(name: str) -> Path:
    """Get the path to a bare repo."""
    config = load_config()
    return Path(config.server.repos_path) / f"{name}.git"


def _run_git(repo_path: Path, *args: str) -> subprocess.CompletedProcess:
    """Run a git command in a bare repo."""
    return subprocess.run(
        ["git", "-C", str(repo_path), *args],
        capture_output=True,
        text=True,
        check=True,
    )


# --- HTML serving ---


@router.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main UI page."""
    html_path = STATIC_DIR / "index.html"
    return HTMLResponse(content=html_path.read_text())


@router.get("/static/style.css")
async def serve_css():
    """Serve the CSS file."""
    return FileResponse(STATIC_DIR / "style.css", media_type="text/css")


@router.get("/static/app.js")
async def serve_js():
    """Serve the JavaScript file."""
    return FileResponse(STATIC_DIR / "app.js", media_type="application/javascript")


# --- API endpoints (no auth, read-only) ---


@router.get("/ui/api/repos")
def api_list_repos():
    """List all repositories with metadata."""
    config = load_config()
    repos = list_repos(config.server.repos_path)
    repo_list = []
    for name in sorted(repos):
        meta = get_metadata(config.server.repos_path, name)
        repo_dir = Path(config.server.repos_path) / f"{name}.git"

        # Get latest commit
        latest_commit = None
        try:
            log_result = subprocess.run(
                ["git", "-C", str(repo_dir), "log", "HEAD", "-1", "--format=%H|%s|%an|%ai"],
                capture_output=True, text=True, check=True,
            )
            parts = log_result.stdout.strip().split("|", 3)
            if len(parts) == 4:
                latest_commit = {
                    "hash": parts[0],
                    "message": parts[1],
                    "author": parts[2],
                    "date": parts[3],
                }
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Count branches
        branch_count = 0
        try:
            branch_result = subprocess.run(
                ["git", "-C", str(repo_dir), "branch", "--format=%(refname:short)"],
                capture_output=True, text=True, check=True,
            )
            branch_count = len([b for b in branch_result.stdout.splitlines() if b.strip()])
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        repo_list.append({
            "name": name,
            "auth_mode": meta.auth_mode if meta else "unknown",
            "latest_commit": latest_commit,
            "branch_count": branch_count,
        })
    return repo_list


@router.get("/ui/api/repos/{name}")
def api_repo_info(name: str):
    """Get detailed repo info (branches, tags, latest commits)."""
    if not repo_exists(load_config().server.repos_path, name):
        raise HTTPException(status_code=404, detail="Repository not found")

    repo_dir = _repo_path(name)
    meta = get_metadata(load_config().server.repos_path, name)

    # Branches
    branches = []
    try:
        result = _run_git(repo_dir, "branch", "--format=%(refname:short)")
        branches = [b.strip() for b in result.stdout.splitlines() if b.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Tags
    tags = []
    try:
        result = _run_git(repo_dir, "tag", "-l", "--format=%(refname:short)|%(objectname:short)")
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            parts = line.split("|", 1)
            tags.append({
                "name": parts[0],
                "commit": parts[1] if len(parts) > 1 else "",
            })
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Recent commits
    commits = []
    try:
        result = _run_git(repo_dir, "log", "HEAD", "-10", "--format=%H|%s|%an|%ai")
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
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Default branch
    default_branch = "main"
    try:
        result = _run_git(repo_dir, "symbolic-ref", "--short", "HEAD")
        default_branch = result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    return {
        "name": name,
        "auth_mode": meta.auth_mode if meta else "unknown",
        "default_branch": default_branch,
        "branches": branches,
        "tags": tags,
        "commits": commits,
    }


@router.get("/ui/api/repos/{name}/tree/{ref}")
@router.get("/ui/api/repos/{name}/tree/{ref}/{path:path}")
def api_tree(name: str, ref: str, path: str = ""):
    """Get file tree at a given ref and path with per-file commit info."""
    if not repo_exists(load_config().server.repos_path, name):
        raise HTTPException(status_code=404, detail="Repository not found")

    repo_dir = _repo_path(name)

    try:
        # Get tree listing
        ls_args = ["ls-tree", "-r", "--name-only", ref]
        if path:
            ls_args.extend(["--", path])
        result = _run_git(repo_dir, *ls_args)
        files = [f for f in result.stdout.splitlines() if f.strip()]

        # Filter to show only items at the current level
        items = []
        seen_dirs = set()
        for f in files:
            if not path:
                # Root level
                parts = f.split("/", 1)
                if len(parts) > 1:
                    # It's in a subdirectory
                    if parts[0] not in seen_dirs:
                        seen_dirs.add(parts[0])
                        items.append({"name": parts[0], "type": "dir"})
                else:
                    items.append({"name": parts[0], "type": "file"})
            else:
                # Subdirectory level
                rel = f[len(path):].lstrip("/")
                parts = rel.split("/", 1)
                if len(parts) > 1:
                    if parts[0] not in seen_dirs:
                        seen_dirs.add(parts[0])
                        items.append({"name": parts[0], "type": "dir"})
                else:
                    items.append({"name": parts[0], "type": "file"})

        # Sort: dirs first, then files
        items.sort(key=lambda x: (x["type"] != "dir", x["name"].lower()))

        # Get per-file last commit info (batch for efficiency)
        for item in items:
            item_path = f"{path}/{item['name']}" if path else item["name"]
            try:
                log_result = _run_git(
                    repo_dir, "log", "-1", "--format=%H|%s|%an|%ai",
                    ref, "--", item_path,
                )
                if log_result.stdout.strip():
                    parts = log_result.stdout.strip().split("|", 3)
                    if len(parts) == 4:
                        item["last_commit"] = {
                            "hash": parts[0],
                            "message": parts[1],
                            "author": parts[2],
                            "date": parts[3],
                        }
            except subprocess.CalledProcessError:
                pass

        # Get parent path for breadcrumbs
        parent = ""
        if path:
            parent = "/".join(path.rstrip("/").split("/")[:-1])

        return {
            "ref": ref,
            "path": path,
            "parent": parent,
            "items": items,
        }
    except subprocess.CalledProcessError:
        raise HTTPException(status_code=404, detail="Reference not found or path does not exist")


@router.get("/ui/api/repos/{name}/blob/{ref}/{path:path}")
def api_blob(name: str, ref: str, path: str):
    """Get file content at a given ref."""
    if not repo_exists(load_config().server.repos_path, name):
        raise HTTPException(status_code=404, detail="Repository not found")

    repo_dir = _repo_path(name)

    try:
        # Check if it's a binary file
        result = _run_git(repo_dir, "diff", "--no-index", "/dev/null", ref + ":" + path)
        # If we get here, it's text (diff returns non-zero for differences)
    except subprocess.CalledProcessError:
        pass

    try:
        # Get file size
        result = _run_git(repo_dir, "cat-file", "-s", ref + ":" + path)
        size = int(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        size = 0

    # Check if binary (simple heuristic: try to detect null bytes)
    try:
        result = _run_git(repo_dir, "show", ref + ":" + path)
        content = result.stdout
        is_binary = "\x00" in content
    except subprocess.CalledProcessError:
        raise HTTPException(status_code=404, detail="File not found")

    if is_binary:
        return {
            "ref": ref,
            "path": path,
            "binary": True,
            "size": size,
            "content": None,
        }

    # Get line count
    line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)

    # Get parent directory
    parent = "/".join(path.rstrip("/").split("/")[:-1])

    return {
        "ref": ref,
        "path": path,
        "parent": parent,
        "binary": False,
        "size": size,
        "line_count": line_count,
        "content": content,
    }


@router.get("/ui/api/repos/{name}/commits/{ref}")
def api_commits(name: str, ref: str, limit: int = 50):
    """Get commit log for a ref."""
    if not repo_exists(load_config().server.repos_path, name):
        raise HTTPException(status_code=404, detail="Repository not found")

    repo_dir = _repo_path(name)

    try:
        result = _run_git(
            repo_dir, "log", ref,
            f"-{min(limit, 100)}",
            "--format=%H|%s|%an|%ae|%ai",
        )
        commits = []
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            parts = line.split("|", 4)
            if len(parts) == 5:
                commits.append({
                    "hash": parts[0],
                    "short_hash": parts[0][:8],
                    "message": parts[1],
                    "author": parts[2],
                    "email": parts[3],
                    "date": parts[4],
                })
        return {
            "ref": ref,
            "commits": commits,
        }
    except subprocess.CalledProcessError:
        raise HTTPException(status_code=404, detail="Reference not found")
