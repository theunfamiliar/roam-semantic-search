"""Health check routes."""

from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

@router.get("/ping")
async def ping():
    """Ping endpoint."""
    return {"message": "pong"} 