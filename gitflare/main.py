"""GitFlare main application."""

import uvicorn
from fastapi import FastAPI

from .config import load_config
from .routes import admin, git_http

app = FastAPI(
    title="GitFlare",
    description="Self-hosted Git repository hosting server",
    version="0.3.0",
)

app.include_router(admin.router)
app.include_router(git_http.router)


def run():
    """Run the GitFlare server."""
    config = load_config()
    uvicorn.run(
        "gitflare.main:app",
        host=config.server.host,
        port=config.server.port,
        reload=False,
    )


if __name__ == "__main__":
    run()
