import httpx
import json
import faiss
import numpy as np
import logging
import re
from typing import List, Dict, Any, Tuple
from datetime import datetime
from app.config import ROAM_GRAPH, ROAM_TOKEN, get_filenames, DATA_DIR
from app.services.search import get_model
from app.services.notifications import send_email
from app.utils.export import save_roam_data
import os

logger = logging.getLogger(__name__)

async def _fetch_roam_data(client: httpx.AsyncClient, url: str, headers: Dict[str, str], 
                          query: Dict[str, str], query_name: str) -> List[Any]:
    """
    Helper function to fetch and log Roam API requests.
    
    Args:
        client: HTTP client
        url: API endpoint
        headers: Request headers
        query: Query payload
        query_name: Name of query for logging
    
    Returns:
        Query results
    
    Raises:
        httpx.HTTPError: If API request fails
    """
    try:
        logger.debug(f"Fetching {query_name} from Roam API", extra={
            "query": query,
            "url": url
        })
        
        response = await client.post(url, headers=headers, json=query, follow_redirects=True)
        response.raise_for_status()
        
        result = response.json()["result"]
        logger.debug(f"Successfully fetched {query_name}", extra={
            "result_count": len(result)
        })
        
        return result
        
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch {query_name}", extra={
            "error": str(e),
            "status_code": e.response.status_code if e.response else None,
            "response_text": e.response.text if e.response else None
        })
        raise

async def _process_blocks(raw_blocks: List[Tuple], brain_tags: set) -> Tuple[List[Dict], Dict, Dict]:
    """
    Process raw blocks into structured data with weights and relationships.
    
    Args:
        raw_blocks: Raw block data from API
        brain_tags: Set of tags for this brain
        
    Returns:
        Tuple of (processed blocks, uid map, parent map)
    """
    blocks = []
    uid_map = {}
    parent_map = {}
    
    for uid, string, parent_uid, page_title in raw_blocks:
        if not (string and uid and page_title != "roam/js"):
            continue
            
        block = {
            "uid": uid,
            "string": string,
            "parent_uid": parent_uid,
            "page_title": page_title
        }
        
        # Calculate weight based on TOC relationship
        if page_title in brain_tags or string in brain_tags:
            block["__weight"] = 1.0
        elif any(f"[[{tag}]]" in string or f"#{tag}" in string for tag in brain_tags):
            block["__weight"] = 0.5
        else:
            continue  # Skip blocks not related to this brain
            
        blocks.append(block)
        uid_map[uid] = block
        parent_map.setdefault(parent_uid, []).append(uid)
    
    return blocks, uid_map, parent_map

async def reindex_brain(brain: str) -> Dict[str, Any]:
    """
    Reindex a specific brain's content using Roam API data.
    
    Args:
        brain: The brain to reindex ("ideas" or "work")
        
    Returns:
        Dict containing status and metrics
        
    Raises:
        Exception: If reindexing fails
    """
    start_time = datetime.now()
    
    try:
        url = f"https://api.roamresearch.com/api/graph/{ROAM_GRAPH}/q"
        headers = {
            "X-Authorization": f"Bearer {ROAM_TOKEN}",
            "Content-Type": "application/json"
        }

        # Query definitions
        toc_query = {
            "query": """
            [:find ?brain ?title
             :where
             [?toc :node/title ?brain]
             [?toc :block/children ?child]
             [?child :block/string ?title]
             [(clojure.string/starts-with? ?brain "TOC -")]]
            """
        }

        block_query = {
            "query": """
            [:find ?uid ?str ?parent ?page_title
             :where
             [?b :block/uid ?uid]
             [?b :block/string ?str]
             [?b :block/parents ?parent]
             [?b :block/page ?p]
             [?p :node/title ?page_title]]
            """
        }

        async with httpx.AsyncClient() as client:
            # Fetch data with proper logging
            toc_result = await _fetch_roam_data(client, url, headers, toc_query, "TOC data")
            raw_blocks = await _fetch_roam_data(client, url, headers, block_query, "block data")

        # Save raw API response with compression and versioning
        raw_data = {
            "toc": toc_result,
            "blocks": raw_blocks,
            "timestamp": datetime.now().isoformat(),
            "brain": brain
        }
        export_path = await save_roam_data(raw_data, brain, DATA_DIR)
        logger.info(f"Saved compressed Roam export to {export_path}")

        # Process TOC data
        brain_tags = set()
        for full_title, tag in toc_result:
            if full_title.replace("TOC - ", "").lower() == brain:
                brain_tags.add(tag)

        logger.debug(f"Found {len(brain_tags)} tags for brain: {brain}", extra={
            "tags": list(brain_tags)
        })

        # Process blocks with helper function
        blocks, uid_map, parent_map = await _process_blocks(raw_blocks, brain_tags)

        # Generate embeddings
        model = get_model()
        
        def extract_tags(text: str) -> str:
            return " ".join(re.findall(r"#\w+|\[\[.*?\]\]", text))

        def get_block_context(block: Dict) -> str:
            parent = uid_map.get(block["parent_uid"], {}).get("string", "")
            children = [uid_map[c]["string"] for c in parent_map.get(block["uid"], []) if uid_map.get(c)]
            return f"Page: {block['page_title']} {extract_tags(block['string'])} {parent} {block['string']} {' '.join(children)}".strip()

        # Prepare data for FAISS
        texts = [get_block_context(b) for b in blocks]
        refs = [f"(({b['uid']}))" for b in blocks]
        weights = [b["__weight"] for b in blocks]

        # Generate embeddings with progress logging
        logger.info(f"Generating embeddings for {len(texts)} blocks...")
        embeddings = model.encode(texts, batch_size=64, convert_to_numpy=True, show_progress_bar=True)
        embeddings *= np.array(weights)[:, None]  # Apply weights

        # Create and save FAISS index
        dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(embeddings)

        # Save index and metadata
        files = get_filenames(brain)
        faiss.write_index(index, files["index"])

        # Prepare and save metadata
        metadata = []
        for i, block in enumerate(blocks):
            metadata.append({
                "text": texts[i],
                "ref": refs[i],
                "uid": block["uid"],
                "parent_uid": block.get("parent_uid"),
                "page_title": block.get("page_title"),
                "children": parent_map.get(block["uid"], []),
                "is_rap": "#raps" in texts[i].lower() or "[[raps]]" in texts[i].lower(),
                "is_ripe": "[[ripe]]" in texts[i].lower(),
                "near_idea": False
            })

        with open(files["meta"], "w", encoding="utf-8") as f:
            json.dump(metadata, f)

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Reindexed {brain} brain", extra={
            "brain": brain,
            "blocks_processed": len(blocks),
            "duration_seconds": duration,
            "embedding_dimension": dim,
            "index_file": files["index"],
            "metadata_file": files["meta"],
            "export_file": str(export_path)
        })

        return {
            "status": "success",
            "blocks_processed": len(blocks),
            "duration_seconds": duration
        }

    except Exception as e:
        error_msg = str(e)
        logger.exception(f"❌ Failed to reindex {brain} brain", extra={
            "brain": brain,
            "error": error_msg,
            "duration_seconds": (datetime.now() - start_time).total_seconds()
        })
        
        send_email(
            subject=f"❌ Reindex Failed: {brain}",
            body=f"Error during reindexing:\n\n{error_msg}"
        )
        raise 