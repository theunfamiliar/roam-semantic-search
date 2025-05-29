"""Main FastAPI application module."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.utils.logging import setup_logging, get_logger
from app.middleware.logging import LoggingMiddleware

# Initialize logging
setup_logging()
logger = get_logger("main")

# Create FastAPI application
app = FastAPI(
    title="Roam Semantic Search",
    description="Semantic search engine for Roam Research exports",
    version="1.0.0"
)

# Add logging middleware
app.add_middleware(LoggingMiddleware)

@app.on_event("startup")
async def startup_event():
    """Log application startup."""
    logger.info("Application starting up", extra={"event": "startup"})

@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown."""
    logger.info("Application shutting down", extra={"event": "shutdown"})

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with logging."""
    logger.error(
        f"Unhandled exception occurred",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_type": exc.__class__.__name__,
            "error_message": str(exc)
        },
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Import and include routers
from app.routers import search, data
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(data.router, prefix="/api/data", tags=["data"]) 