import io
import json
import os
import uuid
from json import JSONDecodeError
from typing import Any

import openai
import pdfplumber
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from pydantic import ValidationError

from app.limiter import limiter
from app.models.disclosure import DisclosureExtraction
from app.services import database, storage
from app.services.extraction_prompt import EXTRACTION_SYSTEM_PROMPT, build_extraction_prompt
from app.services.grok_client import get_grok_client
from app.services.sanitize import sanitize_text

router = APIRouter(prefix="/disclosures", tags=["disclosures"])


@router.get("")
async def list_disclosures(agency: str | None = None) -> list[dict[str, Any]]:
    safe_agency = sanitize_text(agency) if agency else None
    if safe_agency:
        return await database.fetch_all(
            "SELECT * FROM ai_disclosures WHERE agency_name = $1 ORDER BY extracted_at DESC",
            safe_agency,
        )
    return await database.fetch_all("SELECT * FROM ai_disclosures ORDER BY extracted_at DESC")


@router.post("/upload")
@limiter.limit("5/minute")
async def upload_pdf(request: Request, file: UploadFile = File(...)) -> dict[str, object]:  # noqa: B008
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=422, detail="Only PDF files are accepted.")

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=422, detail="File exceeds 10MB limit.")

    raw_text = ""
    with pdfplumber.open(io.BytesIO(contents)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                raw_text += page_text + "\n"

    if len(raw_text.strip()) < 100:
        raise HTTPException(
            status_code=422,
            detail="PDF appears to be scanned. Text extraction not supported.",
        )

    primary_model = os.environ.get("GROK_MODEL", "grok-3")
    client = get_grok_client()
    messages = [
        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": build_extraction_prompt(raw_text)},
    ]

    try:
        response = await client.chat.completions.create(  # type: ignore[call-overload]
            model=primary_model,
            messages=messages,
            response_format={"type": "json_object"},
        )
    except openai.RateLimitError:
        response = await client.chat.completions.create(  # type: ignore[call-overload]
            model="grok-3-mini",
            messages=messages,
            response_format={"type": "json_object"},
        )

    try:
        raw_json = json.loads(response.choices[0].message.content or "{}")
        extraction = DisclosureExtraction(**raw_json)
    except (JSONDecodeError, ValidationError):
        raise HTTPException(
            status_code=422,
            detail="Extraction failed: response did not match expected schema.",
        ) from None

    key = f"{uuid.uuid4()}.pdf"
    storage.upload_pdf(io.BytesIO(contents), key)
    source_url = storage.get_presigned_url(key)

    await database.execute(
        """
        INSERT INTO ai_disclosures
          (agency_name, system_name, purpose, vendor, extraction_confidence, disclosure_source_url)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        sanitize_text(extraction.agency_name),
        sanitize_text(extraction.system_name),
        sanitize_text(extraction.purpose or ""),
        sanitize_text(extraction.vendor or ""),
        extraction.extraction_confidence,
        source_url,
    )

    return {
        "status": "received",
        "agency_name": extraction.agency_name,
        "system_name": extraction.system_name,
        "extraction_confidence": extraction.extraction_confidence,
    }
