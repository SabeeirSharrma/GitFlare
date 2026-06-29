"""Git HTTP protocol routes."""

import base64
import re

from fastapi import APIRouter, Request, Response

from ..auth.tokens import verify_token
from ..git.backend import run_git_backend
from ..git.repo import get_metadata, repo_exists

router = APIRouter()


@router.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "gitflare"}


def _extract_token(request: Request) -> str | None:
    """Extract token from Basic auth header.

    Git sends: Authorization: Basic base64(gitflare:<token>)
    """
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Basic "):
        return None

    try:
        decoded = base64.b64decode(auth_header[6:]).decode()
        username, _, password = decoded.partition(":")
        if username == "gitflare" and password:
            return password
    except Exception:
        return None

    return None


def _is_push_request(request: Request) -> bool:
    """Check if this is a push (git-receive-pack) request."""
    path = request.url.path
    query = request.url.query

    if "git-receive-pack" in path:
        return True
    if "service=git-receive-pack" in query:
        return True
    return False


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

    # Token auth enforcement for push
    if _is_push_request(request):
        meta = get_metadata(config.server.repos_path, repo_name)
        if meta and meta.auth_mode in ("token", "both"):
            token = _extract_token(request)
            if not token:
                return Response(
                    status_code=401,
                    content="Authentication required",
                    headers={"WWW-Authenticate": 'Basic realm="GitFlare"'},
                )
            valid = any(verify_token(token, h) for h in meta.tokens)
            if not valid:
                return Response(
                    status_code=401,
                    content="Invalid token",
                    headers={"WWW-Authenticate": 'Basic realm="GitFlare"'},
                )
        elif meta and meta.auth_mode == "ssh":
            return Response(
                status_code=403,
                content="Push over HTTP not allowed for this repository. Use SSH.",
            )

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
