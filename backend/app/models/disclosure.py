from pydantic import BaseModel


class DisclosureExtraction(BaseModel):
    agency_name: str
    system_name: str
    purpose: str | None = None
    vendor: str | None = None
    extraction_confidence: float = 0.0
