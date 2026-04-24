import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
pytestmark = pytest.mark.asyncio

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_submit_complaint_token():
    payload = {"agency": "ACS", "incident_description": "Test", "system_name": "Test"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/complaints", json=payload)
    assert response.status_code == 200
    assert "complaint_token" in response.json()

@pytest.mark.asyncio
async def test_ingest_socrata_status():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/ingest/socrata")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_check_gaps():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/signals/check-gaps/ACS")
    assert response.status_code == 200