from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from app.auth import require_admin_token
from app.limiter import limiter
from app.services import database
from app.services.extraction_pipeline import extract_pdf_text, run_extraction_pipeline
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
async def upload_pdf(  # noqa: B008
    request: Request,
    _admin: None = Depends(require_admin_token),
    file: UploadFile = File(...),  # noqa: B008
    agency_name: str = Form("Unknown agency"),  # noqa: B008
) -> dict[str, object]:
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=422, detail="Only PDF files are accepted.")

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=422, detail="File exceeds 10MB limit.")

    raw_text = extract_pdf_text(contents)
    if len(raw_text.strip()) < 100:
        raise HTTPException(
            status_code=422,
            detail="PDF appears to be scanned. Text extraction not supported.",
        )

    result = await run_extraction_pipeline(
        pdf_text=raw_text,
        agency_name=sanitize_text(agency_name),
        pdf_contents=contents,
    )
    return {
        "status": "skipped" if result.skipped else "received",
        "agency_name": result.agency_name,
        "systems": result.systems,
        "gaps": result.gaps,
        "validation": result.validation.model_dump() if result.validation else None,
        "extraction_confidence": result.extraction_confidence,
        "reason": result.reason,
    }
