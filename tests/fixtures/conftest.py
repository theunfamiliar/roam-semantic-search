import os
import pytest
import faiss
import numpy as np
from typing import Generator, Dict, Any, List
from httpx import AsyncClient
from fastapi.testclient import TestClient
from faker import Faker
import factory
from app.models.schemas import SearchResult, SearchRequest
from app.services.search import get_model
from datetime import datetime
import json

fake = Faker()

# Constants for testing
TEST_USERNAME = "admin"
TEST_PASSWORD = "secret"
TEST_VECTOR_DIM = 384  # MiniLM dimension

@pytest.fixture
def client() -> Generator:
    """Create a TestClient instance for synchronous tests."""
    from server import app
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
async def async_client() -> AsyncClient:
    """Create an AsyncClient instance for async tests."""
    from server import app
    return AsyncClient(app=app, base_url="http://test")

@pytest.fixture
def auth_headers() -> Dict[str, str]:
    """Get basic auth headers."""
    import base64
    credentials = base64.b64encode(
        f"{TEST_USERNAME}:{TEST_PASSWORD}".encode()
    ).decode()
    return {"Authorization": f"Basic {credentials}"}

class SearchResultFactory(factory.Factory):
    """Factory for generating test SearchResult objects."""
    class Meta:
        model = SearchResult

    text = factory.LazyFunction(lambda: fake.paragraph())
    ref = factory.LazyFunction(lambda: f"(({fake.uuid4()}))")
    uid = factory.LazyFunction(fake.uuid4)
    parent_uid = factory.LazyFunction(fake.uuid4)
    page_title = factory.LazyFunction(fake.sentence)
    children = factory.LazyFunction(lambda: [fake.uuid4() for _ in range(2)])
    is_rap = False
    is_ripe = False
    near_idea = False

@pytest.fixture
def search_result() -> SearchResult:
    """Generate a single test SearchResult."""
    return SearchResultFactory()

@pytest.fixture
def search_results(size: int = 5) -> list[SearchResult]:
    """Generate multiple test SearchResults."""
    return [SearchResultFactory() for _ in range(size)]

@pytest.fixture
def test_index(tmp_path):
    """Create a test FAISS index with random vectors."""
    dimension = 768  # BERT embedding dimension
    index = faiss.IndexFlatL2(dimension)
    vectors = np.random.random((10, dimension)).astype('float32')
    index.add(vectors)
    index_path = tmp_path / "test_index.faiss"
    faiss.write_index(index, str(index_path))
    return str(index_path)

@pytest.fixture
def test_metadata(tmp_path):
    """Create test metadata file."""
    metadata = {
        "blocks": [
            {
                "uid": fake.uuid4(),
                "content": fake.paragraph(),
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
            for _ in range(10)
        ],
        "timestamp": datetime.now().isoformat()
    }
    meta_path = tmp_path / "test_meta.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f)
    return str(meta_path)

@pytest.fixture
def mock_roam_blocks() -> List[Dict]:
    """Create mock Roam blocks for testing."""
    return [
        {
            "uid": fake.uuid4(),
            "content": fake.paragraph(),
            "timestamp": int(datetime.now().timestamp() * 1000)
        }
        for _ in range(20)
    ]

@pytest.fixture
def mock_model():
    """Mock the sentence transformer model."""
    model = get_model()
    return model

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Setup test environment variables."""
    monkeypatch.setenv("USERNAME", TEST_USERNAME)
    monkeypatch.setenv("PASSWORD", TEST_PASSWORD)
    monkeypatch.setenv("ROAM_GRAPH", "test-graph")
    monkeypatch.setenv("ROAM_API_TOKEN", "test-token") 