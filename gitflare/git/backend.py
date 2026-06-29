"""Git HTTP backend wrapper."""

import asyncio
import os
import subprocess
from pathlib import Path

from fastapi import Request, Response


async def run_git_backend(repos_path: str, repo_name: str, request: Request) -> Response:
    """Run git http-backend and return the response.

    Args:
        repos_path: Base path where repos are stored
        repo_name: Repository name (without .git extension)
        request: The incoming FastAPI request

    Returns:
        Response from git http-backend
    """
    repo_path = Path(repos_path) / f"{repo_name}.git"

    if not repo_path.exists():
        return Response(status_code=404, content="Repository not found")

    path_info = request.url.path

    env = os.environ.copy()
    env.update({
        "GIT_PROJECT_ROOT": str(repos_path),
        "GIT_HTTP_EXPORT_ALL": "1",
        "PATH_INFO": path_info,
        "REQUEST_METHOD": request.method,
        "QUERY_STRING": str(request.url.query),
        "CONTENT_TYPE": request.headers.get("content-type", ""),
        "CONTENT_LENGTH": request.headers.get("content-length", ""),
        "REMOTE_ADDR": request.client.host if request.client else "",
    })

    body = await request.body()

    result = await asyncio.to_thread(
        _run_git_backend_sync, env, body
    )

    if result["returncode"] != 0 and not result["stdout"]:
        return Response(
            status_code=500,
            content=result["stderr"],
        )

    return parse_cgi_response(result["stdout"])


def _run_git_backend_sync(env: dict, body: bytes) -> dict:
    """Run git http-backend synchronously in a thread."""
    proc = subprocess.Popen(
        ["git", "http-backend"],
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stdout, stderr = proc.communicate(input=body)

    return {
        "returncode": proc.returncode,
        "stdout": stdout,
        "stderr": stderr.decode("utf-8", errors="replace"),
    }


def parse_cgi_response(output: bytes) -> Response:
    """Parse CGI response from git http-backend.

    The output uses \r\n\r\n to separate headers from the binary body.
    We must split on the first occurrence of that delimiter and keep the
    body as raw bytes.
    """
    separator = b"\r\n\r\n"
    idx = output.find(separator)

    if idx == -1:
        return Response(status_code=500, content="Invalid CGI response")

    header_bytes = output[:idx]
    body = output[idx + len(separator):]

    headers = {}
    status_code = 200

    for line in header_bytes.decode("utf-8", errors="replace").split("\r\n"):
        if not line:
            continue
        if line.startswith("Status:"):
            status_text = line.split(":", 1)[1].strip()
            status_code = int(status_text.split()[0])
        elif ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip()] = value.strip()

    return Response(
        status_code=status_code,
        content=body,
        headers=headers,
    )
