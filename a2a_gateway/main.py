"""A2A Coding Gateway - FastAPI application"""

import sys

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest

from a2a_gateway.config import settings
from a2a_gateway.routes import router
from a2a_gateway.tasks import task_store

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        (
            structlog.dev.ConsoleRenderer()
            if sys.stdout.isatty()
            else structlog.processors.JSONRenderer()
        ),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Create FastAPI application
app = FastAPI(
    title="A2A Coding Gateway",
    version="1.0.0",
    description="A2A Coding Gateway for Clawdbot",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    from a2a_gateway import __version__

    logger.info("Starting A2A Coding Gateway", version=__version__)
    await task_store.initialize()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup application on shutdown"""
    logger.info("Shutting down A2A Coding Gateway")
    await task_store.close()


@app.get("/health")
async def health_check(detailed: bool = False):
    """Health check endpoint"""
    from a2a_gateway import __version__

    health_status = {
        "status": "healthy",
        "version": __version__,
        "active_tasks": task_store.active_count,
        "max_concurrent_tasks": settings.max_concurrent_tasks,
    }

    if detailed and settings.redis_enabled:
        health_status["redis"] = await task_store.check_redis_health()

    return health_status


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "a2a_gateway.main:app", host=settings.host, port=settings.port, reload=True
    )
