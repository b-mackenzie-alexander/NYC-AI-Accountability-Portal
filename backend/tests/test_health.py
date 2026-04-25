import os
from unittest.mock import AsyncMock, patch

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


@pytest.mark.asyncio
async def test_health_check():
    with (
        patch("app.services.database.get_pool", new_callable=AsyncMock),
        patch("app.services.database.close_pool", new_callable=AsyncMock),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_cors_blocked_for_unknown_origin():
    with (
        patch("app.services.database.get_pool", new_callable=AsyncMock),
        patch("app.services.database.close_pool", new_callable=AsyncMock),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health", headers={"Origin": "https://evil.example.com"})
    assert "access-control-allow-origin" not in response.headers




