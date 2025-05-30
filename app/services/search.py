"""Search service for semantic search functionality."""

import faiss
import numpy as np
import json
import logging
import os
from sentence_transformers import SentenceTransformer, util
from typing import List, Dict, Any
from app.config import get_filenames
from app.models.api import SearchRequest, SearchResult
import uuid

logger = logging.getLogger(__name__)

# Initialize the sentence transformer model
_model = None

def get_model() -> SentenceTransformer:
    """Get or initialize the sentence transformer model."""
    global _model
    if _model is None:
        # Download and cache the model
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model

def normalize_vectors(vectors: np.ndarray) -> np.ndarray:
    """Normalize vectors to unit length for cosine similarity."""
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / norms

def normalize_score(score: float) -> float:
    """
    Normalize the inner product score to a similarity score between 0 and 1.
    Since vectors are normalized, inner product is already cosine similarity (-1 to 1).
    We rescale it to 0 to 1 range.
    """
    return (score + 1) / 2

async def search(request: SearchRequest) -> List[SearchResult]:
    """
    Perform semantic search using FAISS.
    
    Args:
        request: Search request parameters
        
    Returns:
        List of search results
        
    Raises:
        FileNotFoundError: If index or metadata files are missing
        ValueError: If query is empty or invalid
        Exception: For other unexpected errors
    """
    if not request.query.strip():
        raise ValueError("Search query cannot be empty")

    try:
        files = get_filenames(request.brain)
        
        # Verify files exist
        missing_files = [f for f, path in files.items() if not os.path.exists(path)]
        if missing_files:
            raise FileNotFoundError(f"Missing files: {', '.join(missing_files)}. Try reindexing first.")
            
        # Load FAISS index
        index = faiss.read_index(files["index"])
        
        # Load metadata
        with open(files["meta"], "r", encoding="utf-8") as f:
            metadata = json.load(f)
            
        # Generate embedding for query
        model = get_model()
        query_text = request.query.strip()
        embedding = model.encode(query_text, convert_to_numpy=True)
        
        # Normalize query vector for cosine similarity
        embedding = normalize_vectors(np.array([embedding]))[0]
        
        # Search
        D, I = index.search(np.array([embedding]).astype('float32'), request.top_k)
        
        # Convert results
        results = []
        for score, idx in zip(D[0], I[0]):
            if idx < len(metadata):  # Safety check
                meta = metadata[idx]
                result = SearchResult(
                    content=meta["content"],
                    score=normalize_score(float(score)),  # Convert cosine similarity to 0-1 range
                    brain=request.brain,
                    metadata={"uid": meta.get("uid", str(uuid.uuid4()))}
                )
                results.append(result)
                
        return results
        
    except (FileNotFoundError, ValueError) as e:
        logger.warning(f"Search validation error: {str(e)}")
        raise
    except Exception as e:
        logger.exception("Unexpected error during search")
        raise Exception(f"Search failed: {str(e)}")

class SearchService:
    """Service for handling semantic search operations."""
    
    async def search(
        self,
        query: str,
        brain: str,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Search for semantically similar content.
        
        Args:
            query: The search query
            brain: The brain to search in
            top_k: Number of results to return
            
        Returns:
            Dict containing search results
        """
        request = SearchRequest(query=query, brain=brain, top_k=top_k)
        results = await search(request)
        return {
            "query": query,
            "results": results,
            "count": len(results)
        } 