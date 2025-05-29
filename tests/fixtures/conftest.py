import os
import pytest
import faiss
import numpy as np
from typing import Generator, Dict, Any
from httpx import AsyncClient
from fastapi.testclient import TestClient
from faker import Faker
import factory
from app.models.schemas import SearchResult, SearchRequest
from app.services.search import get_model

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
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

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
def test_index():
    """Create a test FAISS index with random vectors."""
    index = faiss.IndexFlatL2(TEST_VECTOR_DIM)
    vectors = np.random.random((100, TEST_VECTOR_DIM)).astype('float32')
    index.add(vectors)
    return index

@pytest.fixture
def test_metadata() -> list[Dict[str, Any]]:
    """Create test metadata for FAISS results."""
    return [
        SearchResultFactory().dict()
        for _ in range(100)
    ]

@pytest.fixture
def mock_roam_blocks() -> list[Dict[str, Any]]:
    """Generate mock Roam Research blocks."""
    return [
        {
            "string": fake.paragraph(),
            "uid": fake.uuid4(),
            "page_title": fake.sentence(),
            "parent_uid": fake.uuid4()
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
    monkeypatch.setenv("ROAM_TOKEN", "test-token") 