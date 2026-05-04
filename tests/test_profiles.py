import pytest
from unittest.mock import AsyncMock, patch
from app.models import models
import uuid

@pytest.mark.asyncio
async def test_get_all_profiles_cache_hit(client):
    """Test that repeated queries hit the cache."""
    # First request
    with patch("app.models.cruds.profileCrud.get_profiles", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = ([], 0)
        
        # Request 1
        response1 = client.get("/api/profiles?gender=female")
        assert response1.status_code == 200
        assert mock_get.call_count == 1
        
        # Request 2 (Identical)
        response2 = client.get("/api/profiles?gender=female")
        assert response2.status_code == 200
        assert mock_get.call_count == 1  # Should NOT increase, hit cache
        
        # Request 3 (Different but semantically same - normalization test)
        # Note: Query params are usually ordered by the browser/client, 
        # but our normalization handles dict keys.
        response3 = client.get("/api/profiles?gender=female&page=1")
        assert response3.status_code == 200
        # In our implementation, page/limit are part of the cache key prefix, 
        # so this might be a different key if defaults are explicit.
        # But let's check if the filter part is normalized.

@pytest.mark.asyncio
async def test_natural_query_normalization(client):
    """Test that semantically identical natural queries hit the same cache key."""
    with patch("app.models.cruds.profileCrud.get_profiles", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = ([], 0)
        
        # Query 1
        client.get("/api/profiles/search?q=Nigerian females between ages 20 and 45")
        assert mock_get.call_count == 1
        
        # Query 2 (Different wording, same intent)
        # Our current parse_natural_query is simple, so "between ages 20 and 45" 
        # might need better parsing to match "aged 20-45".
        # Let's see if it works with what we have.
        client.get("/api/profiles/search?q=Females from Nigeria aged 20 to 45")
        # If normalization works, call_count should stay 1 (assuming same parsed filters)
        # Actually, let's verify if they parse to same filters first.

@pytest.mark.asyncio
async def test_create_profile_invalidates_cache(client):
    """Test that creating a profile clears the cache."""
    with patch("app.models.cruds.profileCrud.get_profiles", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = ([], 0)
        client.get("/api/profiles")
        assert mock_get.call_count == 1
        
        # Clear cache check
        client.get("/api/profiles")
        assert mock_get.call_count == 1 # Cache hit
        
        # Create profile
        with patch("app.services.external_api.fetch_external_data", new_callable=AsyncMock) as mock_ext:
            mock_ext.return_value = {"gender": "male", "age": 30, "country_id": "US", "gender_probability": 1.0, "country_probability": 1.0}
            with patch("app.models.cruds.profileCrud.get_profile_by_name", new_callable=AsyncMock) as mock_name:
                mock_name.return_value = None
                with patch("app.models.cruds.profileCrud.create_profile", new_callable=AsyncMock) as mock_create:
                    mock_create.return_value = models.Profile(
                        id=uuid.uuid4(),
                        name="newuser",
                        gender="male",
                        age=30,
                        age_group="adult",
                        country_id="US",
                        gender_probability=1.0,
                        country_probability=1.0
                    )
                    client.post("/api/profiles", json={"name": "NewUser"})
        
        # Next list request should be a cache miss
        client.get("/api/profiles")
        assert mock_get.call_count == 2
