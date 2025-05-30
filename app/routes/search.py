"""Search routes."""

from fastapi import APIRouter, HTTPException, Depends
from app.models.search import SearchRequest, SearchResult, SearchResponse
from app.services.search import search
from app.services.auth import authenticate
from typing import List
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("")
async def search_endpoint(request: SearchRequest, auth: bool = Depends(authenticate)) -> SearchResponse:
    """
    Search endpoint.
    
    Args:
        request: Search request parameters
        auth: Authentication dependency
        
    Returns:
        SearchResponse: Search results with metadata
        
    Raises:
        HTTPException: If search fails
    """
    try:
        results = await search(request)
        return SearchResponse(
            results=results,
            count=len(results),
            query=request.query
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except FileNotFoundError as e:
        # File not found is a client error if they haven't indexed yet
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Search failed", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}") 