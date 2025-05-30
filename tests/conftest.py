"""Global test fixtures."""

import os
import json
import pytest
import faiss
import numpy as np
from faker import Faker
from httpx import AsyncClient
from fastapi import FastAPI
from typing import Dict, List, AsyncGenerator
import factory
from datetime import datetime
from fastapi.testclient import TestClient
from httpx import ASGITransport

from app.server import app
from app.models.search import SearchResult
from app.services.search import get_model

fake = Faker()

@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Get async client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.fixture
def auth_headers() -> Dict[str, str]:
    """Get auth headers with admin token."""
    return {"Authorization": "Bearer admin-test-token"}

@pytest.fixture
def mock_roam_blocks() -> List[List]:
    """Create mock Roam blocks for testing."""
    return [
        [
            fake.uuid4(),  # uid
            fake.paragraph(),  # content
            int(datetime.now().timestamp() * 1000)  # timestamp
        ]
        for _ in range(20)
    ]

@pytest.fixture
def search_results() -> List[SearchResult]:
    """Create mock search results for testing."""
    return [
        SearchResult(
            uid=fake.uuid4(),
            content=fake.paragraph(),
            score=float(fake.random.random()),
            brain="ideas"
        )
        for _ in range(5)
    ]

@pytest.fixture
def test_index(tmp_path):
    """Create a test FAISS index."""
    # Get the actual model to ensure dimension matches
    model = get_model()
    # Create a small test sentence and get its embedding to determine dimension
    test_embedding = model.encode("test", convert_to_numpy=True)
    dimension = len(test_embedding)
    
    index = faiss.IndexFlatL2(dimension)
    vectors = np.random.random((10, dimension)).astype('float32')
    index.add(vectors)
    index_path = tmp_path / "test_index.faiss"
    faiss.write_index(index, str(index_path))
    return str(index_path)

@pytest.fixture
def test_metadata(tmp_path):
    """Create test metadata file."""
    metadata = [  # Change to list to match search service
        {
            "uid": fake.uuid4(),
            "content": fake.paragraph(),
            "brain": "ideas",  # Add brain field to match SearchResult model
            "score": 0.0  # Add default score
        }
        for _ in range(10)
    ]
    meta_path = tmp_path / "test_meta.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f)
    return str(meta_path) 