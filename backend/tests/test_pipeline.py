from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import openai
import pytest
from fastapi import HTTPException

from app.models.pipeline import ClassificationResult, ExtractionResult
from app.services.agents.classifier import run_classifier
from app.services.agents.extractor import run_extractor
from app.services.agents.llm import create_json_completion
from app.services.extraction_pipeline import run_extraction_pipeline

pytestmark = pytest.mark.asyncio


def _response(content: str) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content),
            )
        ]
    )


def _rate_limit_error() -> openai.RateLimitError:
    request = httpx.Request("POST", "https://api.x.ai/v1/chat/completions")
    response = httpx.Response(429, request=request)
    return openai.RateLimitError("rate limited", response=response, body=None)


@pytest.mark.asyncio
async def test_classifier_low_confidence_rejected_by_pipeline():
    classification = ClassificationResult(
        document_type="unknown",
        agency_name=None,
        confidence=0.49,
        extraction_strategy="partial",
        notes="Not enough confidence.",
    )
    with patch(
        "app.services.extraction_pipeline.run_classifier", AsyncMock(return_value=classification)
    ):
        with pytest.raises(HTTPException) as exc:
            await run_extraction_pipeline("text", "ACS", b"pdf")
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_classifier_skip_short_circuits_pipeline():
    classification = ClassificationResult(
        document_type="unknown",
        agency_name=None,
        confidence=0.9,
        extraction_strategy="skip",
        notes="No disclosure data.",
    )
    with patch(
        "app.services.extraction_pipeline.run_classifier", AsyncMock(return_value=classification)
    ):
        result = await run_extraction_pipeline("text", "ACS", b"pdf")
    assert result.skipped is True
    assert result.reason == "No disclosure data."


@pytest.mark.asyncio
async def test_malformed_classifier_json_returns_422():
    with patch(
        "app.services.agents.classifier.create_json_completion",
        AsyncMock(return_value={"document_type": "bad"}),
    ):
        with pytest.raises(HTTPException) as exc:
            await run_classifier("text")
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_rate_limit_fallback_success():
    create = AsyncMock(side_effect=[_rate_limit_error(), _response('{"ok": true}')])
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    with patch("app.services.agents.llm.get_grok_client", return_value=client):
        result = await create_json_completion([{"role": "user", "content": "hello"}])
    assert result == {"ok": True}
    assert create.call_args_list[1].kwargs["model"] == "grok-3-mini"


@pytest.mark.asyncio
async def test_rate_limit_fallback_failure_returns_503():
    create = AsyncMock(side_effect=[_rate_limit_error(), _rate_limit_error()])
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    with patch("app.services.agents.llm.get_grok_client", return_value=client):
        with pytest.raises(HTTPException) as exc:
            await create_json_completion([{"role": "user", "content": "hello"}])
    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_extractor_drops_missing_system_names():
    raw = {
        "agency_name": "ACS",
        "systems": [
            {"system_name": "Risk Model", "purpose": "Screening"},
            {"purpose": "No name"},
            {"system_name": "   "},
        ],
        "extraction_confidence": 0.9,
        "missing_fields_note": "",
    }
    with patch("app.services.agents.extractor.create_json_completion", AsyncMock(return_value=raw)):
        extraction = await run_extractor("text", "ll35_annual_report", "ACS")
    assert [system.system_name for system in extraction.systems] == ["Risk Model"]


@pytest.mark.asyncio
async def test_pipeline_inserts_multiple_systems_and_gaps():
    classification = ClassificationResult(
        document_type="ll35_annual_report",
        agency_name="ACS",
        confidence=0.91,
        extraction_strategy="full",
        notes="Clear filing.",
    )
    extraction = ExtractionResult(
        agency_name="ACS",
        systems=[
            {"system_name": "Risk Model", "purpose": "Screening", "data_sources": ["case data"]},
            {"system_name": "Audit Tool", "vendor": "VendorCo"},
        ],
        extraction_confidence=0.86,
        missing_fields_note="Some audit fields missing.",
    )
    execute_mock = AsyncMock(return_value="INSERT 0 1")
    with (
        patch(
            "app.services.extraction_pipeline.run_classifier",
            AsyncMock(return_value=classification),
        ),
        patch("app.services.extraction_pipeline.run_extractor", AsyncMock(return_value=extraction)),
        patch("app.services.extraction_pipeline.storage.upload_pdf", return_value="key.pdf"),
        patch(
            "app.services.extraction_pipeline.storage.get_presigned_url",
            return_value="https://r2/key.pdf",
        ),
        patch("app.services.extraction_pipeline.database.execute", execute_mock),
        patch(
            "app.services.extraction_pipeline.detect_and_store_disclosure_gaps",
            AsyncMock(return_value=["Missing System"]),
        ),
    ):
        result = await run_extraction_pipeline("text", "ACS", b"pdf")

    assert len(result.systems) == 2
    assert result.gaps == ["Missing System"]
    assert execute_mock.await_count == 2


@pytest.mark.asyncio
async def test_high_confidence_empty_extraction_is_legitimate_empty_disclosure():
    classification = ClassificationResult(
        document_type="ll35_annual_report",
        agency_name="ACS",
        confidence=0.9,
        extraction_strategy="full",
        notes="Clear filing.",
    )
    extraction = ExtractionResult(
        agency_name="ACS",
        systems=[],
        extraction_confidence=0.95,
        missing_fields_note="No AI disclosures.",
    )
    with (
        patch(
            "app.services.extraction_pipeline.run_classifier",
            AsyncMock(return_value=classification),
        ),
        patch("app.services.extraction_pipeline.run_extractor", AsyncMock(return_value=extraction)),
        patch("app.services.extraction_pipeline.storage.upload_pdf", return_value="key.pdf"),
        patch(
            "app.services.extraction_pipeline.storage.get_presigned_url",
            return_value="https://r2/key.pdf",
        ),
        patch("app.services.extraction_pipeline.database.execute", AsyncMock()),
        patch(
            "app.services.extraction_pipeline.detect_and_store_disclosure_gaps",
            AsyncMock(return_value=[]),
        ),
    ):
        result = await run_extraction_pipeline("text", "ACS", b"pdf")

    assert result.systems == []
    assert result.validation is not None
    assert result.validation.overall_quality == "high"
