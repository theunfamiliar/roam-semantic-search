"""Reindex routes."""

from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import ReindexResponse
from app.services.auth import authenticate
from app.services.indexing import reindex_brain
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/reindex")
async def reindex_endpoint(auth: bool = Depends(authenticate)) -> ReindexResponse:
    """
    Reindex both brains (ideas and work) from Roam API data.
    """
    try:
        # Reindex both brains
        results = {}
        for brain in ["ideas", "work"]:
            result = await reindex_brain(brain)
            results[brain] = result["blocks_processed"]
            
        total_blocks = sum(results.values())
        return ReindexResponse(
            status="success",
            blocks_processed=total_blocks
        )
            
    except Exception as e:
        logger.exception("Reindex failed")
        raise HTTPException(status_code=500, detail=str(e)) 