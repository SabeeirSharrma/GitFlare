"""Git HTTP protocol routes."""

import re
from fastapi import APIRouter, Request, Response

from ..git.backend import run_git_backend
from ..git.repo import repo_exists

router = APIRouter()


async def _handle_git_request(repo_path: str, request: Request) -> Response:
    """Common handler for all git HTTP requests."""
    from ..config import load_config
    config = load_config()

    # Extract repo name from the path (e.g. test.git/info/refs -> test)
    match = re.match(r"^(.+)\.git(/.*)?$", repo_path)
    if not match:
        return Response(status_code=400, content="Invalid repository path")

    repo_name = match.group(1)

    if not repo_exists(config.server.repos_path, repo_name):
        return Response(status_code=404, content="Repository not found")

    return await run_git_backend(config.server.repos_path, repo_name, request)


@router.api_route("/{repo_path:path}", methods=["GET", "POST"])
async def git_handler(repo_path: str, request: Request) -> Response:
    """Catch-all handler for git smart HTTP protocol.

    This handles all git HTTP endpoints:
    - /<repo>.git/info/refs?service=git-upload-pack (clone/fetch)
    - /<repo>.git/git-upload-pack (clone/fetch data)
    - /<repo>.git/info/refs?service=git-receive-pack (push)
    - /<repo>.git/git-receive-pack (push data)
    """
    return await _handle_git_request(repo_path, request)
