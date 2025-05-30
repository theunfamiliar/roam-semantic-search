import pytest
import os
import faiss
import json
from app.services.indexing import reindex_brain
from app.config import get_filenames
from faker import Faker
from datetime import datetime

fake = Faker()

@pytest.mark.integration
class TestIndexingIntegration:
    @pytest.fixture(autouse=True)
    def setup_data_dir(self):
        """Create data directory for test files."""
        os.makedirs("data", exist_ok=True)
        yield
        # Clean up test files
        for file in os.listdir("data"):
            if file.startswith("index_") or file.startswith("meta_"):
                os.remove(os.path.join("data", file))

    @pytest.mark.timeout(45)  # This test involves model loading and indexing
    async def test_full_indexing_flow(self, mock_roam_blocks, monkeypatch):
        """Test complete indexing flow with mock Roam data."""
        # Mock Roam API response
        async def mock_post(*args, **kwargs):
            class MockResponse:
                def raise_for_status(self): pass
                def json(self):
                    if "block/refs" in kwargs.get("json", {}).get("query", ""):
                        # Return reference blocks with 4 values
                        return {"result": [
                            [
                                fake.uuid4(),  # uid
                                fake.paragraph(),  # content
                                int(datetime.now().timestamp() * 1000),  # timestamp
                                mock_roam_blocks[0][0]  # ref_target
                            ]
                            for _ in range(5)
                        ]}
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

    @pytest.mark.timeout(10)
    async def test_indexing_error_handling(self, monkeypatch):
        """Test indexing error handling."""
        async def mock_post(*args, **kwargs):
            raise Exception("API Error")

        monkeypatch.setattr("httpx.AsyncClient.post", mock_post)

        with pytest.raises(Exception) as exc:
            await reindex_brain("ideas")
        assert "API Error" in str(exc.value)

    @pytest.mark.slow
    @pytest.mark.timeout(60)  # Large dataset test needs more time
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