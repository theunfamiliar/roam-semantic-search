"""Roam Research API utilities."""

import os
import logging
import httpx
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Use direct peer URL to avoid redirects
BASE_URL = "https://peer-13.api.roamresearch.com:3000/api/graph/unfamiliar/q"
ROAM_API_TOKEN = os.getenv("ROAM_API_TOKEN")

async def query_roam(query: str, *args) -> Dict[str, Any]:
    """Execute a Datalog query against Roam API."""
    if not ROAM_API_TOKEN:
        raise ValueError("ROAM_API_TOKEN environment variable not set")

    headers = {
        "X-Authorization": f"Bearer {ROAM_API_TOKEN}",
        "Content-Type": "application/json",
        "accept": "application/json"
    }

    data = {
        "query": query,
        "args": list(args)
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                BASE_URL,
                headers=headers,
                json=data,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error("HTTP error occurred: %s", str(e))
        raise

async def get_blocks_under_toc(toc_page: str) -> List[Dict]:
    """Get all blocks under a specific TOC page."""
    query = """
    [:find ?uid ?string ?time
     :in $ ?title
     :where
     [?p :node/title ?title]
     [?b :block/page ?p]
     [?b :block/uid ?uid]
     [?b :block/string ?string]
     [?b :edit/time ?time]]
    """
    
    result = await query_roam(query, toc_page)
    return result.get("result", [])

async def get_block_references_batch(block_uids: List[str]) -> List[Dict]:
    """Get all blocks that reference any of the given blocks in a single query."""
    if not block_uids:
        return []

    # Build a query that finds references to any of the input blocks
    query = """
    [:find ?uid ?string ?time ?ref-uid
     :in $ [?ref-uid ...]
     :where
     [?b :block/uid ?uid]
     [?b :block/string ?string]
     [?b :edit/time ?time]
     [?b :block/refs ?ref]
     [?ref :block/uid ?ref-uid]]
    """
    
    result = await query_roam(query, block_uids)
    return result.get("result", [])

async def get_block_references(block_uid: str) -> List[Dict]:
    """Get all blocks that reference a specific block."""
    result = await get_block_references_batch([block_uid])
    return [ref[:3] for ref in result if ref[3] == block_uid]  # Only return refs for this block

async def get_block_content(block_uid: str) -> Optional[str]:
    """Get the content of a specific block by its UID."""
    query = """
    [:find ?string
     :in $ ?uid
     :where
     [?b :block/uid ?uid]
     [?b :block/string ?string]]
    """
    
    result = await query_roam(query, block_uid)
    if result.get("result"):
        return result["result"][0][0]
    return None

async def get_page_content(page_title: str) -> List[Dict]:
    """Get all blocks on a specific page."""
    query = """
    [:find ?uid ?string ?time ?order
     :in $ ?title
     :where
     [?p :node/title ?title]
     [?b :block/page ?p]
     [?b :block/uid ?uid]
     [?b :block/string ?string]
     [?b :edit/time ?time]
     [?b :block/order ?order]]
    """
    
    result = await query_roam(query, page_title)
    return result.get("result", []) 