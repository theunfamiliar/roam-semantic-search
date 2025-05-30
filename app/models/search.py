"""Search models."""

from pydantic import BaseModel, Field
from typing import List, Optional

class SearchResult(BaseModel):
    """Search result model."""
    uid: str
    content: str
    score: float
    brain: str

class SearchRequest(BaseModel):
    """Search request model."""
    query: str = Field(..., min_length=1, description="Search query")
    brain: str = Field(default="ideas", description="Brain to search in")
    top_k: int = Field(default=5, gt=0, description="Number of results to return")

class SearchResponse(BaseModel):
    """Search response model."""
    results: List[SearchResult]
    count: int
    query: str 