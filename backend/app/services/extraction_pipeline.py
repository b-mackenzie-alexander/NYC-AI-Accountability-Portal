import io
import uuid

import pdfplumber
from fastapi import HTTPException

from app.models.pipeline import PipelineResult
from app.services import database, storage
from app.services.agents.classifier import run_classifier
from app.services.agents.extractor import run_extractor
from app.services.agents.validator import validate_extraction
from app.services.gap_detection import detect_and_store_disclosure_gaps
from app.services.sanitize import sanitize_text


def extract_pdf_text(contents: bytes) -> str:
    raw_text = ""
    with pdfplumber.open(io.BytesIO(contents)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                raw_text += page_text + "\n"
    return raw_text


async def run_extraction_pipeline(
    pdf_text: str,
    agency_name: str,
    pdf_contents: bytes,
) -> PipelineResult:
    classification = await run_classifier(pdf_text)
    if classification.extraction_strategy == "skip":
        return PipelineResult(
            agency_name=classification.agency_name or agency_name,
            systems=[],
            gaps=[],
            skipped=True,
            reason=classification.notes,
            extraction_confidence=1.0,
        )
    if classification.confidence < 0.5:
        raise HTTPException(status_code=422, detail=classification.notes)

    resolved_agency = classification.agency_name or agency_name
    extraction = await run_extractor(
        text=pdf_text,
        document_type=classification.document_type,
        agency_name=resolved_agency,
    )
    validation = validate_extraction(extraction)

    key = f"{uuid.uuid4()}.pdf"
    storage.upload_pdf(io.BytesIO(pdf_contents), key)
    source_url = storage.get_presigned_url(key)

    inserted_records: list[dict] = []
    for system in validation.validated_systems:
        await database.execute(
            """
            INSERT INTO ai_disclosures
              (
                agency_name, system_name, purpose, vendor, data_sources, audit_date,
                audit_findings, extraction_confidence, disclosure_source_url
              )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            sanitize_text(extraction.agency_name),
            sanitize_text(system.system_name or ""),
            sanitize_text(system.purpose or ""),
            sanitize_text(system.vendor or ""),
            [sanitize_text(source) for source in system.data_sources],
            system.audit_date,
            sanitize_text(system.audit_findings or ""),
            extraction.extraction_confidence,
            source_url,
        )
        inserted_records.append(
            {
                **system.model_dump(),
                "agency_name": extraction.agency_name,
                "extraction_confidence": extraction.extraction_confidence,
                "disclosure_source_url": source_url,
            }
        )

    gaps = await detect_and_store_disclosure_gaps(resolved_agency)
    return PipelineResult(
        agency_name=resolved_agency,
        systems=inserted_records,
        gaps=gaps,
        validation=validation,
        extraction_confidence=extraction.extraction_confidence,
    )
