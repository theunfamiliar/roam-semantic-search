"""Main FastAPI application."""

from fastapi import FastAPI, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from app.services.security import SecurityService
from app.services.search import SearchService
from app.services.indexing import IndexingService
from app.models.api import (
    SearchRequest,
    SearchResponse,
    ReindexRequest,
    ReindexResponse,
    HealthResponse
)

app = FastAPI(title="Roam Semantic Search API")
security_service = SecurityService()
search_service = SearchService()
indexing_service = IndexingService()

async def get_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> str:
    """Get and validate token from request."""
    return await security_service.validate_token(credentials, request)

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

@app.get("/api/health/ping")
async def ping():
    """Simple ping endpoint."""
    return {"message": "pong"}

@app.post("/api/search", response_model=SearchResponse)
async def search(
    request: Request,
    search_request: SearchRequest,
    token: str = Depends(get_token)
):
    """
    Search endpoint.
    
    Args:
        request: The FastAPI request object
        search_request: The search parameters
        token: The validated authentication token
        
    Returns:
        SearchResponse: The search results
    """
    # Validate brain access
    security_service.validate_brain_access(token, search_request.brain)
    
    # Perform search
    return await search_service.search(
        query=search_request.query,
        brain=search_request.brain,
        top_k=search_request.top_k
    )

@app.post("/api/reindex", response_model=ReindexResponse)
async def reindex(
    request: Request,
    reindex_request: ReindexRequest,
    token: str = Depends(get_token)
):
    """
    Reindex endpoint.
    
    Args:
        request: The FastAPI request object
        reindex_request: The reindex parameters
        token: The validated authentication token
        
    Returns:
        ReindexResponse: The reindex status
    """
    # Validate brain access
    security_service.validate_brain_access(token, reindex_request.brain)
    
    # Perform reindex
    await indexing_service.reindex_brain(reindex_request.brain)
    return {"status": "success"} 