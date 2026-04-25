import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")
os.environ.setdefault("COMPLAINT_HMAC_SECRET", "test-hmac-secret-32-bytes-xxxxxxxx")
os.environ.setdefault("GROK_API_KEY", "test-key")
os.environ.setdefault("R2_ENDPOINT_URL", "https://test.r2.cloudflarestorage.com")
os.environ.setdefault("R2_ACCESS_KEY_ID", "test-key-id")
os.environ.setdefault("R2_SECRET_ACCESS_KEY", "test-secret")

from app.main import app  # noqa: E402

pytestmark = pytest.mark.asyncio


@pytest.mark.asyncio
async def test_health_check():
    with (
        patch("app.services.database.get_pool", new_callable=AsyncMock),
        patch("app.services.database.close_pool", new_callable=AsyncMock),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_submit_complaint_token():
    execute_mock = AsyncMock(return_value="INSERT 0 1")
    with (
        patch("app.services.database.get_pool", new_callable=AsyncMock),
        patch("app.services.database.close_pool", new_callable=AsyncMock),
        patch("app.services.database.execute", execute_mock),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/complaints",
                json={"agency": "ACS", "incident_description": "Test incident", "system_name": "Test"},
            )
    assert response.status_code == 200
    data = response.json()
    assert "complaint_token" in data
    assert data["status"] == "received"


@pytest.mark.asyncio
async def test_ingest_socrata_status():
    execute_mock = AsyncMock(return_value="INSERT 0 1")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"race_ethnicity": "Black", "count": "1200"},
        {"race_ethnicity": "White Non-Hispanic", "count": "450"},
    ]
    with (
        patch("app.services.database.get_pool", new_callable=AsyncMock),
        patch("app.services.database.close_pool", new_callable=AsyncMock),
        patch("app.services.database.execute", execute_mock),
        patch("httpx.AsyncClient.get", AsyncMock(return_value=mock_response)),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/ingest/socrata")
    assert response.status_code == 200
    assert response.json()["status"] == "success"


@pytest.mark.asyncio
async def test_check_gaps():
    fetch_all_mock = AsyncMock(return_value=[])
    fetch_one_mock = AsyncMock(return_value=None)
    execute_mock = AsyncMock(return_value="INSERT 0 1")
    with (
        patch("app.services.database.get_pool", new_callable=AsyncMock),
        patch("app.services.database.close_pool", new_callable=AsyncMock),
        patch("app.services.database.fetch_all", fetch_all_mock),
        patch("app.services.database.fetch_one", fetch_one_mock),
        patch("app.services.database.execute", execute_mock),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/signals/check-gaps/Administration for Children's Services"
            )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
