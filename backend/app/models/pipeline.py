from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ClassificationResult(BaseModel):
    document_type: Literal["ll35_annual_report", "ll144_bias_audit", "agency_policy", "unknown"]
    agency_name: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    extraction_strategy: Literal["full", "partial", "skip"]
    notes: str


class ExtractedSystem(BaseModel):
    system_name: str | None = None
    purpose: str | None = None
    vendor: str | None = None
    data_sources: list[str] = Field(default_factory=list)
    audit_date: str | None = None
    audit_findings: str | None = None
    population_affected: str | None = None
    decision_type: str | None = None

    @field_validator("system_name")
    @classmethod
    def blank_system_name_becomes_none(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value


class ExtractionResult(BaseModel):
    agency_name: str
    systems: list[ExtractedSystem] = Field(default_factory=list)
    extraction_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    missing_fields_note: str = ""


class ValidatedSystem(ExtractedSystem):
    validation_flags: list[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    validated_systems: list[ValidatedSystem]
    overall_quality: Literal["high", "medium", "low"]
    review_recommended: bool
    validation_notes: str


class PipelineResult(BaseModel):
    agency_name: str | None = None
    systems: list[dict]
    gaps: list[str]
    validation: ValidationResult | None = None
    extraction_confidence: float = 1.0
    skipped: bool = False
    reason: str | None = None
