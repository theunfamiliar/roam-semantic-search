import os
import pytest
import httpx
from app.config import get_settings

@pytest.mark.integration
class TestRoamAPI:
    """Integration tests for Roam Research API."""
    
    def setup_method(self):
        """Setup test environment."""
        self.settings = get_settings()
        self.headers = {
            "Authorization": f"Bearer {self.settings.roam_token}",
            "Content-Type": "application/json"
        }
        self.url = f"https://api.roamresearch.com/api/graph/{self.settings.roam_graph}/datalog"

    async def test_api_connection(self):
        """Test basic connection to Roam API."""
        query = {
            "query": "[ :find ?uid :where [?b :block/uid ?uid] ]"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.url,
                headers=self.headers,
                json=query
            )
            
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "result" in data

    @pytest.mark.parametrize("invalid_token", ["", "invalid_token", None])
    async def test_invalid_auth(self, invalid_token):
        """Test API behavior with invalid authentication."""
        headers = {
            "Authorization": f"Bearer {invalid_token}",
            "Content-Type": "application/json"
        }
        query = {"query": "[ :find ?uid :where [?b :block/uid ?uid] ]"}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.url,
                headers=headers,
                json=query
            )
        
        assert response.status_code in [401, 403]  # Either unauthorized or forbidden 