from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import SearchRequest, SearchResponse
from app.services.auth import authenticate
from app.services.search import search
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/search", response_model=SearchResponse)
async def search_endpoint(request: SearchRequest, auth: bool = Depends(authenticate)):
    """
    Perform semantic search over the specified brain.
    """
    try:
        results = search(request)
        return SearchResponse(
            results=results,
            count=len(results),
            query=request.query
        )
    except Exception as e:
        logger.exception("Search failed")
        raise HTTPException(status_code=500, detail=str(e)) 