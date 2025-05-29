import pytest
import os
import faiss
import json
from app.services.indexing import reindex_brain
from app.config import get_filenames

@pytest.mark.integration
class TestIndexingIntegration:
    async def test_full_indexing_flow(self, mock_roam_blocks, monkeypatch):
        """Test complete indexing flow with mock Roam data."""
        # Mock Roam API response
        async def mock_post(*args, **kwargs):
            class MockResponse:
                def raise_for_status(self): pass
                def json(self): 
                    return {"result": mock_roam_blocks}
            return MockResponse()

        monkeypatch.setattr("httpx.AsyncClient.post", mock_post)

        # Run indexing
        result = await reindex_brain("ideas")
        assert result["status"] == "success"
        assert result["blocks_processed"] > 0

        # Verify files were created
        files = get_filenames("ideas")
        assert os.path.exists(files["index"])
        assert os.path.exists(files["meta"])

        # Verify index content
        index = faiss.read_index(files["index"])
        assert index.ntotal > 0  # Has vectors

        # Verify metadata
        with open(files["meta"], "r") as f:
            metadata = json.load(f)
            assert len(metadata) > 0
            assert all(isinstance(m, dict) for m in metadata)

    async def test_indexing_error_handling(self, monkeypatch):
        """Test indexing error handling."""
        async def mock_post(*args, **kwargs):
            raise Exception("API Error")

        monkeypatch.setattr("httpx.AsyncClient.post", mock_post)

        with pytest.raises(Exception) as exc:
            await reindex_brain("ideas")
        assert "API Error" in str(exc.value)

    @pytest.mark.slow
    async def test_large_dataset_indexing(self, mock_roam_blocks):
        """Test indexing with a large dataset."""
        # Create large mock dataset
        large_blocks = mock_roam_blocks * 100  # 2000 blocks

        async def mock_post(*args, **kwargs):
            class MockResponse:
                def raise_for_status(self): pass
                def json(self): 
                    return {"result": large_blocks}
            return MockResponse()

        result = await reindex_brain("ideas")
        assert result["status"] == "success"
        assert result["blocks_processed"] > 1000 