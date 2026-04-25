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
os.environ.setdefault("ADMIN_API_TOKEN", "test-admin-token")

from app.main import app  # noqa: E402
from app.models.pipeline import PipelineResult, ValidationResult  # noqa: E402

pytestmark = pytest.mark.asyncio

ADMIN_HEADERS = {"X-Admin-Token": "test-admin-token"}


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
                json={
                    "agency": "ACS",
                    "incident_description": "Test incident",
                    "system_name": "Test",
                },
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
            response = await client.post("/ingest/socrata", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert response.json()["status"] == "success"


@pytest.mark.asyncio
async def test_list_disclosures_no_filter():
    fetch_all_mock = AsyncMock(
        return_value=[
            {
                "id": "abc",
                "agency_name": "ACS",
                "system_name": "Test System",
                "extraction_confidence": 0.9,
            }
        ]
    )
    with (
        patch("app.services.database.get_pool", new_callable=AsyncMock),
        patch("app.services.database.close_pool", new_callable=AsyncMock),
        patch("app.services.database.fetch_all", fetch_all_mock),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/disclosures")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_list_disclosures_agency_filter():
    fetch_all_mock = AsyncMock(return_value=[])
    with (
        patch("app.services.database.get_pool", new_callable=AsyncMock),
        patch("app.services.database.close_pool", new_callable=AsyncMock),
        patch("app.services.database.fetch_all", fetch_all_mock),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/disclosures?agency=ACS")
    assert response.status_code == 200
    fetch_all_mock.assert_called_once()
    call_args = fetch_all_mock.call_args
    assert "ACS" in call_args.args


@pytest.mark.asyncio
async def test_ingest_socrata_502_on_failure():
    mock_response = MagicMock()
    mock_response.status_code = 503
    with (
        patch("app.services.database.get_pool", new_callable=AsyncMock),
        patch("app.services.database.close_pool", new_callable=AsyncMock),
        patch("httpx.AsyncClient.get", AsyncMock(return_value=mock_response)),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/ingest/socrata", headers=ADMIN_HEADERS)
    assert response.status_code == 502


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
                "/signals/check-gaps/Administration for Children's Services",
                headers=ADMIN_HEADERS,
            )
    assert response.status_code == 200
    assert response.json()["status"] == "success"


@pytest.mark.asyncio
async def test_internal_endpoint_requires_admin_token():
    with (
        patch("app.services.database.get_pool", new_callable=AsyncMock),
        patch("app.services.database.close_pool", new_callable=AsyncMock),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/ingest/socrata")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_internal_endpoint_rejects_wrong_admin_token():
    with (
        patch("app.services.database.get_pool", new_callable=AsyncMock),
        patch("app.services.database.close_pool", new_callable=AsyncMock),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/ingest/socrata",
                headers={"X-Admin-Token": "wrong-token"},
            )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_generate_signals_produces_disparity_signal():
    fixture_records = [
        {"race_ethnicity": "Black", "count": 600, "outcome_type": "referral", "agency": "ACS"},
        {"race_ethnicity": "White Non-Hispanic", "count": 200, "outcome_type": "referral", "agency": "ACS"},
        {"race_ethnicity": "Hispanic", "count": 300, "outcome_type": "referral", "agency": "ACS"},
    ]
    fetch_all_mock = AsyncMock(return_value=fixture_records)
    execute_mock = AsyncMock(return_value="INSERT 0 1")
    with (
        patch("app.services.database.get_pool", new_callable=AsyncMock),
        patch("app.services.database.close_pool", new_callable=AsyncMock),
        patch("app.services.database.fetch_all", fetch_all_mock),
        patch("app.services.database.execute", execute_mock),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/signals/generate/Administration for Children's Services",
                headers=ADMIN_HEADERS,
            )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["signals_analyzed"] >= 1


@pytest.mark.asyncio
async def test_generate_signals_no_outcome_data():
    fetch_all_mock = AsyncMock(return_value=[])
    with (
        patch("app.services.database.get_pool", new_callable=AsyncMock),
        patch("app.services.database.close_pool", new_callable=AsyncMock),
        patch("app.services.database.fetch_all", fetch_all_mock),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/signals/generate/Administration for Children's Services",
                headers=ADMIN_HEADERS,
            )
    assert response.status_code == 200
    assert response.json()["signals_analyzed"] == 0


@pytest.mark.asyncio
async def test_upload_delegates_to_pipeline_with_admin_token():
    validation = ValidationResult(
        validated_systems=[],
        overall_quality="high",
        review_recommended=False,
        validation_notes="0 systems extracted. Quality: high.",
    )
    result = PipelineResult(
        agency_name="ACS",
        systems=[],
        gaps=[],
        validation=validation,
        extraction_confidence=1.0,
    )
    with (
        patch("app.services.database.get_pool", new_callable=AsyncMock),
        patch("app.services.database.close_pool", new_callable=AsyncMock),
        patch("app.routes.disclosures.extract_pdf_text", return_value="A" * 120),
        patch("app.routes.disclosures.run_extraction_pipeline", AsyncMock(return_value=result)),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/disclosures/upload",
                headers=ADMIN_HEADERS,
                data={"agency_name": "ACS"},
                files={"file": ("test.pdf", b"%PDF fake", "application/pdf")},
            )

    assert response.status_code == 200
    assert response.json()["status"] == "received"
    assert response.json()["agency_name"] == "ACS"
