import faiss
import numpy as np
import json
import logging
import os
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
from app.config import get_filenames
from app.models.schemas import SearchRequest, SearchResult

logger = logging.getLogger(__name__)

# Initialize the sentence transformer model
_model = None

def get_model() -> SentenceTransformer:
    """Get or initialize the sentence transformer model."""
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def search(request: SearchRequest) -> List[SearchResult]:
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
        embedding = model.encode(request.query, convert_to_numpy=True)
        
        # Search
        D, I = index.search(np.array([embedding]), request.top_k)
        
        # Convert results
        results = []
        for idx in I[0]:
            if idx < len(metadata):  # Safety check
                result_dict = metadata[idx]
                results.append(SearchResult(**result_dict))
                
        return results
        
    except (FileNotFoundError, ValueError) as e:
        logger.warning(f"Search validation error: {str(e)}")
        raise
    except Exception as e:
        logger.exception("Unexpected error during search")
        raise Exception(f"Search failed: {str(e)}") 