import os
import json
import pytest
import httpx
import faiss
import asyncio
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import AsyncMock, patch

from app.config import get_filenames
from app.utils.roam_api import (
    get_blocks_under_toc,
    get_block_references,
    get_block_content,
    get_page_content,
    query_roam,
    BASE_URL,
    ROAM_API_TOKEN
)
from app.services.indexing import reindex_brain

@pytest.fixture
async def mock_roam_response():
    """Fixture for mocked Roam API response."""
    return {
        "result": [
            ["block-uid-1", "Test block content", 1621234567890, 0],
            ["block-uid-2", "Another test block", 1621234567891, 1]
        ]
    }

@pytest.fixture
async def mock_empty_response():
    """Fixture for empty Roam API response."""
    return {"result": []}

@pytest.fixture
async def mock_error_response():
    """Fixture for error response."""
    async def raise_error(*args, **kwargs):
        raise httpx.HTTPError("Mocked API error")
    return raise_error

@pytest.mark.integration
class TestRoamIntegration:
    """Integration tests for Roam Research API and semantic search."""
    
    def setup_method(self):
        """Setup test environment and validate required environment variables."""
        # Validate required environment variables
        required_vars = ["GRAPH_NAME", "ROAM_API_TOKEN"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            pytest.skip(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        self.graph_name = os.getenv("GRAPH_NAME")
        self.api_token = os.getenv("ROAM_API_TOKEN")
        self.url = BASE_URL
        self.headers = {
            "X-Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "accept": "application/json"
        }

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_api_connection(self):
        """Test basic connection to Roam API with proper error handling."""
        query = {
            "query": "[:find ?uid :where [?b :block/uid ?uid]]",
            "args": []
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.url,
                headers=self.headers,
                json=query,
                follow_redirects=True
            )
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)
            assert "result" in data

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    @pytest.mark.parametrize("invalid_token", [
        None,
        "invalid_token",
        "Bearer invalid",
        "not_a_token",
        "Bearer\tinvalid"
    ])
    async def test_invalid_auth(self, invalid_token):
        """Test API behavior with various invalid authentication scenarios."""
        headers = {
            "X-Authorization": invalid_token if invalid_token else "",
            "Content-Type": "application/json",
            "accept": "application/json"
        }
        query = {
            "query": "[:find ?uid :where [?b :block/uid ?uid]]",
            "args": []
        }
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.post(
                self.url,
                headers=headers,
                json=query
            )
        
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("brain", ["ideas", "marketing"])
    async def test_get_blocks_under_toc(self, brain, mock_roam_response):
        """Test fetching blocks under TOC pages with mocked responses."""
        with patch('app.utils.roam_api.query_roam', return_value=mock_roam_response):
            blocks = await get_blocks_under_toc(f"TOC - {brain}")
            assert isinstance(blocks, list)
            assert len(blocks) > 0
            
            # Verify block structure
            for block in blocks:
                assert isinstance(block, list)
                assert len(block) >= 3
                assert all(x is not None for x in block)
                uid, content, timestamp = block[:3]
                assert isinstance(uid, str)
                assert isinstance(content, str)
                assert isinstance(timestamp, (int, float))

    @pytest.mark.asyncio
    async def test_get_block_references_with_data(self, mock_roam_response):
        """Test fetching block references with mock data."""
        # Mock response should match the new format from get_block_references_batch
        mock_data = {
            "result": [
                ["ref-uid-1", "Reference content 1", 1621234567890, "test-uid"],
                ["ref-uid-2", "Reference content 2", 1621234567891, "test-uid"],
                ["ref-uid-3", "Reference content 3", 1621234567892, "other-uid"]
            ]
        }
        
        with patch('app.utils.roam_api.query_roam', return_value=mock_data):
            refs = await get_block_references("test-uid")
            assert isinstance(refs, list)
            assert len(refs) == 2  # Should only get refs for test-uid
            for ref in refs:
                assert len(ref) == 3  # uid, content, timestamp
                assert isinstance(ref[0], str)
                assert isinstance(ref[1], str)
                assert isinstance(ref[2], int)

    @pytest.mark.asyncio
    async def test_get_block_references_empty(self, mock_empty_response):
        """Test fetching block references with no data."""
        with patch('app.utils.roam_api.query_roam', return_value=mock_empty_response):
            refs = await get_block_references("test-uid")
            assert isinstance(refs, list)
            assert len(refs) == 0

    @pytest.mark.asyncio
    async def test_get_block_content_success(self, mock_roam_response):
        """Test successful block content retrieval."""
        with patch('app.utils.roam_api.query_roam', return_value=mock_roam_response):
            content = await get_block_content("test-uid")
            assert isinstance(content, str)
            assert len(content) > 0

    @pytest.mark.asyncio
    async def test_get_block_content_not_found(self, mock_empty_response):
        """Test block content retrieval for non-existent block."""
        with patch('app.utils.roam_api.query_roam', return_value=mock_empty_response):
            content = await get_block_content("nonexistent-uid")
            assert content is None

    @pytest.mark.asyncio
    async def test_get_page_content_success(self, mock_roam_response):
        """Test successful page content retrieval."""
        with patch('app.utils.roam_api.query_roam', return_value=mock_roam_response):
            blocks = await get_page_content("Test Page")
            assert isinstance(blocks, list)
            assert len(blocks) > 0
            
            # Verify block structure
            for block in blocks:
                assert isinstance(block, list)
                assert len(block) >= 4  # uid, string, time, order
                uid, content, timestamp, order = block
                assert isinstance(uid, str)
                assert isinstance(content, str)
                assert isinstance(timestamp, (int, float))
                assert isinstance(order, (int, float))

    @pytest.mark.asyncio
    async def test_get_page_content_empty(self, mock_empty_response):
        """Test page content retrieval for empty page."""
        with patch('app.utils.roam_api.query_roam', return_value=mock_empty_response):
            blocks = await get_page_content("Empty Page")
            assert isinstance(blocks, list)
            assert len(blocks) == 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_api_error_handling(self, mock_error_response):
        """Test error handling during API calls."""
        with patch('app.utils.roam_api.query_roam', mock_error_response):
            with pytest.raises(httpx.HTTPError):
                await get_blocks_under_toc("Test Page")

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)  # Increased timeout for complete reindex flow
    @pytest.mark.reindex
    async def test_complete_reindex_flow(self):
        """Test complete reindexing flow with real Roam data."""
        try:
            result = await reindex_brain("ideas")
            assert result["status"] == "success"
            assert result["blocks_processed"] > 0
            assert result["duration"] > 0
            
            # Verify files were created
            files = get_filenames("ideas")
            assert os.path.exists(files["index"])
            assert os.path.exists(files["meta"])
            
            # Verify metadata structure
            with open(files["meta"], "r") as f:
                metadata = json.load(f)
                assert isinstance(metadata, list)
                assert len(metadata) > 0
                assert all(isinstance(block, dict) for block in metadata)
                assert all("uid" in block and "content" in block for block in metadata)
            
            # Verify FAISS index
            index = faiss.read_index(files["index"])
            assert index.ntotal == len(metadata)
            
        except Exception as e:
            pytest.fail(f"Reindex flow failed: {str(e)}")

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)  # Increased timeout for data integrity test
    @pytest.mark.reindex
    async def test_reindex_data_integrity(self):
        """Test data integrity during reindexing process."""
        try:
            # First reindex
            result1 = await reindex_brain("ideas")
            assert result1["status"] == "success"

            # Get first index data
            files = get_filenames("ideas")
            with open(files["meta"], "r") as f:
                metadata1 = json.load(f)
            index1 = faiss.read_index(files["index"])

            # Wait a bit to ensure no file locks
            await asyncio.sleep(1)

            # Second reindex
            result2 = await reindex_brain("ideas")
            assert result2["status"] == "success"

            # Get second index data
            with open(files["meta"], "r") as f:
                metadata2 = json.load(f)
            index2 = faiss.read_index(files["index"])

            # Compare metadata
            assert len(metadata1) == len(metadata2), "Metadata length mismatch"
            # Sort both lists by uid to ensure consistent comparison
            metadata1 = sorted(metadata1, key=lambda x: x["uid"])
            metadata2 = sorted(metadata2, key=lambda x: x["uid"])
            
            for item1, item2 in zip(metadata1, metadata2):
                assert item1["uid"] == item2["uid"], f"UID mismatch: {item1['uid']} != {item2['uid']}"
                assert item1["content"] == item2["content"], f"Content mismatch for uid {item1['uid']}"
                assert item1["brain"] == item2["brain"], f"Brain mismatch for uid {item1['uid']}"

            # Compare FAISS indices
            assert index1.ntotal == index2.ntotal, "Index size mismatch"
            assert index1.d == index2.d, "Index dimension mismatch"

        except Exception as e:
            pytest.fail(f"Data integrity test failed: {str(e)}") 