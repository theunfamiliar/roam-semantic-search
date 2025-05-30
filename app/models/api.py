"""API request and response models."""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., example="ok")

class SearchRequest(BaseModel):
    """Search request model."""
    query: str = Field(..., min_length=1, example="project management")
    brain: Literal["ideas", "marketing"] = Field(..., example="marketing")
    top_k: Optional[int] = Field(default=5, gt=0, le=100)

class SearchResult(BaseModel):
    """Single search result."""
    content: str = Field(..., example="Meeting notes about project timeline")
    score: float = Field(..., example=0.89)
    brain: Literal["ideas", "marketing"] = Field(..., example="marketing")
    metadata: dict = Field(default_factory=dict)

class SearchResponse(BaseModel):
    """Search response model."""
    query: str = Field(..., example="project management")
    results: List[SearchResult]
    count: int = Field(..., example=5)

class ReindexRequest(BaseModel):
    """Reindex request model."""
    brain: Literal["ideas", "marketing"] = Field(..., example="marketing")

class ReindexResponse(BaseModel):
    """Reindex response model."""
    status: str = Field(..., example="success")

class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str = Field(..., example="Access denied to brain: ideas")
    status_code: int = Field(..., example=403)

class TokenResponse(BaseModel):
    """Token response model."""
    token: str = Field(..., example="eyJhbGciOiJIUzI1NiIs...")
    token_type: Literal["admin", "marketing"] = Field(..., example="marketing")
    expires_at: str = Field(..., example="2024-12-31T23:59:59Z") 