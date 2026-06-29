"""GitFlare main application."""

import logging

import uvicorn
from fastapi import FastAPI

from .config import load_config
from .logging import RequestLogMiddleware, setup_logging
from .routes import admin, git_http

logger = logging.getLogger("gitflare")

app = FastAPI(
    title="GitFlare",
    description="Self-hosted Git repository hosting server",
    version="0.4.0",
)

app.add_middleware(RequestLogMiddleware)
app.include_router(admin.router)
app.include_router(git_http.router)


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
