"""Admin API routes for GitFlare."""

from fastapi import APIRouter, Query, Response

from ..auth.tokens import verify_token
from ..config import load_config
from ..git.repo import get_metadata

router = APIRouter(prefix="/admin")


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
