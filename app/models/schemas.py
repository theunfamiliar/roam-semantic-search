from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SearchRequest(BaseModel):
    """Schema for search requests."""
    query: str
    top_k: int = Field(default=5, gt=0)
    page: int = Field(default=1, gt=0)
    per_page: int = Field(default=5, gt=0)
    mode: str = Field(default="Next RAP")
    rhyme_sound: Optional[str] = None
    brain: str = Field(default="ideas")

class SearchResult(BaseModel):
    """Schema for individual search results."""
    text: str
    ref: str
    uid: str
    parent_uid: Optional[str]
    page_title: Optional[str]
    children: List[str]
    is_rap: bool
    is_ripe: bool
    near_idea: bool = False

class SearchResponse(BaseModel):
    """Schema for search response."""
    results: List[SearchResult]
    count: int
    query: str

class ReindexResponse(BaseModel):
    """Schema for reindex response."""
    status: str
    blocks_processed: Optional[int] = None
    error: Optional[str] = None 