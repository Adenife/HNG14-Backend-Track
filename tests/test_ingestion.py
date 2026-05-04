import pytest
from unittest.mock import AsyncMock, patch
import io

@pytest.mark.asyncio
async def test_csv_upload_success(client):
    """Test successful CSV upload with valid rows."""
    csv_content = (
        "name,gender,age,country_id,gender_probability,country_probability\n"
        "Alice,female,25,US,0.99,0.95\n"
        "Bob,male,30,GB,0.98,0.90\n"
    )
    
    with patch("app.models.cruds.profileCrud.get_profile_by_name", new_callable=AsyncMock) as mock_name:
        mock_name.return_value = None
        
        response = client.post(
            "/api/profiles/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_rows"] == 2
        assert data["inserted"] == 2
        assert data["skipped"] == 0

@pytest.mark.asyncio
async def test_csv_upload_with_skips(client):
    """Test CSV upload with mixed valid and invalid rows."""
    csv_content = (
        "name,gender,age,country_id\n"
        "Valid,female,25,US\n"              # Valid
        "InvalidAge,female,-5,US\n"         # Invalid age
        "MissingField,female,,US\n"         # Missing age
        "Duplicate,male,30,GB\n"            # Will be mocked as duplicate
        "BadGender,robot,10,XX\n"           # Unrecognized gender
    )
    
    async def side_effect(db, name):
        if name == "duplicate":
            return True
        return None

    with patch("app.models.cruds.profileCrud.get_profile_by_name", side_effect=side_effect):
        response = client.post(
            "/api/profiles/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_rows"] == 5
        assert data["inserted"] == 1
        assert data["skipped"] == 4
        assert data["reasons"]["invalid_age"] == 1
        assert data["reasons"]["missing_fields"] == 1
        assert data["reasons"]["duplicate_name"] == 1
        assert data["reasons"]["unrecognized_gender"] == 1
