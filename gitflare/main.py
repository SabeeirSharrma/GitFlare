"""GitFlare main application."""

import logging

import uvicorn
from fastapi import FastAPI

from .config import load_config
from .logging import RequestLogMiddleware, setup_logging
from .routes import admin, git_http, ui

logger = logging.getLogger("gitflare")

app = FastAPI(
    title="GitFlare",
    description="Self-hosted Git repository hosting server",
    version="0.5.0",
)

# UI routes (registered before git catch-all)
app.include_router(ui.router)

# Admin API routes
app.include_router(admin.router)

# Git HTTP protocol catch-all (must be last)
app.include_router(git_http.router)

app.add_middleware(RequestLogMiddleware)


@app.on_event("startup")
async def startup():
    setup_logging()
    logger.info("GitFlare starting up")


@app.on_event("shutdown")
async def shutdown():
    logger.info("GitFlare shutting down")


def run():
    """Run the GitFlare server."""
    config = load_config()
    setup_logging()
    logger.info("Starting GitFlare on %s:%d", config.server.host, config.server.port)
    uvicorn.run(
        "gitflare.main:app",
        host=config.server.host,
        port=config.server.port,
        reload=False,
    )


if __name__ == "__main__":
    run()
