"""Indexing service for Roam semantic search."""

import json
import faiss
import numpy as np
import logging
import re
import asyncio
from typing import List, Dict, Any, Set
from datetime import datetime
from app.config import get_filenames, DATA_DIR
from app.services.search import get_model
from app.utils.export import save_roam_data
from app.utils.roam_api import get_blocks_under_toc, get_block_references, get_block_references_batch
import os

logger = logging.getLogger(__name__)

def normalize_vectors(vectors: np.ndarray) -> np.ndarray:
    """Normalize vectors to unit length for cosine similarity."""
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / norms

async def process_references(refs: List[List[Any]], processed_uids: Set[str]) -> List[Dict[str, Any]]:
    """
    Process block references into a standardized format.
    
    Args:
        refs: List of reference data from Roam
        processed_uids: Set of already processed UIDs
        
    Returns:
        List of processed block data
    """
    blocks = []
    for ref in refs:
        ref_uid, ref_content, ref_time, ref_target = ref
        if ref_uid not in processed_uids:
            processed_uids.add(ref_uid)
            blocks.append({
                "uid": ref_uid,
                "content": ref_content,
                "timestamp": ref_time,
                "type": "reference",
                "references": ref_target
            })
    return blocks

async def create_embeddings(blocks: List[Dict[str, Any]], brain: str) -> tuple[np.ndarray, List[Dict[str, Any]]]:
    """
    Create embeddings for blocks using the sentence transformer model.
    
    Args:
        blocks: List of block data
        brain: Brain name for metadata
        
    Returns:
        Tuple of (embeddings array, metadata list)
    """
    model = get_model()
    embeddings = []
    metadata = []
    
    # Process in batches to avoid memory issues
    batch_size = 32
    for i in range(0, len(blocks), batch_size):
        batch = blocks[i:i + batch_size]
        batch_texts = [block["content"] for block in batch]
        batch_embeddings = model.encode(batch_texts, convert_to_numpy=True)
        
        embeddings.extend(batch_embeddings)
        for block in batch:
            metadata.append({
                "uid": block["uid"],
                "content": block["content"],
                "brain": brain
            })
    
    embeddings_array = np.array(embeddings).astype('float32')
    # Normalize vectors for cosine similarity
    normalized_embeddings = normalize_vectors(embeddings_array)
    return normalized_embeddings, metadata

async def reindex_brain(brain: str) -> Dict[str, Any]:
    """
    Reindex a specific brain's content using Roam API data.
    
    Args:
        brain: The brain to reindex ("ideas" or "marketing")
        
    Returns:
        Dict containing status and metrics
        
    Raises:
        Exception: If reindexing fails
    """
    start_time = datetime.now()
    processed_uids = set()  # Track processed block UIDs
    
    try:
        # Get blocks under TOC page
        toc_page = f"TOC - {brain}"
        logger.info(f"Fetching blocks under {toc_page}")
        blocks = await get_blocks_under_toc(toc_page)
        
        if not blocks:
            raise ValueError(f"No blocks found under {toc_page}")
        
        # Process TOC blocks first
        all_blocks = []
        toc_uids = []
        for block in blocks:
            uid, content, timestamp = block
            if uid not in processed_uids:
                processed_uids.add(uid)
                all_blocks.append({
                    "uid": uid,
                    "content": content,
                    "timestamp": timestamp,
                    "type": "block"
                })
                toc_uids.append(uid)
        
        # Get all references in a single batch
        logger.info("Fetching block references")
        refs = await get_block_references_batch(toc_uids)
        ref_blocks = await process_references(refs, processed_uids)
        all_blocks.extend(ref_blocks)
        
        if not all_blocks:
            raise ValueError(f"No valid blocks found to index in {brain} brain")
            
        # Create embeddings and metadata
        logger.info("Creating embeddings")
        embeddings, metadata = await create_embeddings(all_blocks, brain)
        
        # Create and save FAISS index
        logger.info("Creating FAISS index")
        dimension = embeddings.shape[1]
        # Use IndexFlatIP for inner product (cosine similarity with normalized vectors)
        index = faiss.IndexFlatIP(dimension)
        index.add(embeddings)
        
        # Save index and metadata
        files = get_filenames(brain)
        os.makedirs(os.path.dirname(files["index"]), exist_ok=True)
        os.makedirs(os.path.dirname(files["meta"]), exist_ok=True)
        
        faiss.write_index(index, files["index"])
        with open(files["meta"], "w") as f:
            json.dump(metadata, f)
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Successfully reindexed {brain} brain in {duration:.2f} seconds")
        
        return {
            "status": "success",
            "blocks_processed": len(all_blocks),
            "duration": duration
        }
            
    except Exception as e:
        logger.error(f"❌ Failed to reindex {brain} brain", exc_info=True)
        raise

class IndexingService:
    """Service for handling brain indexing operations."""
    
    async def reindex_brain(self, brain: str) -> None:
        """
        Reindex a specific brain.
        
        Args:
            brain: The brain to reindex
        """
        # For testing purposes, just pass
        pass 