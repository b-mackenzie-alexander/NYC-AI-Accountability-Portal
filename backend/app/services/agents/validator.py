from typing import Literal

from app.models.pipeline import ExtractionResult, ValidatedSystem, ValidationResult

VAGUE_NAMES = {"system", "tool", "model", "algorithm"}


def validate_extraction(extraction: ExtractionResult) -> ValidationResult:
    validated_systems: list[ValidatedSystem] = []
    has_flags = False
    quality: Literal["high", "medium", "low"]

    for system in extraction.systems:
        flags: list[str] = []
        if not system.purpose:
            flags.append("missing_purpose")
        if not system.data_sources:
            flags.append("missing_data_sources")
        if not system.audit_date and not system.audit_findings:
            flags.append("no_audit_information")
        system_name = system.system_name or ""
        if system_name.lower() in VAGUE_NAMES:
            flags.append("vague_system_name")

        has_flags = has_flags or bool(flags)
        validated_systems.append(
            ValidatedSystem(
                **system.model_dump(),
                validation_flags=flags,
            )
        )

    if extraction.extraction_confidence > 0.8:
        quality = "high"
    elif extraction.extraction_confidence > 0.5:
        quality = "medium"
    else:
        quality = "low"

    return ValidationResult(
        validated_systems=validated_systems,
        overall_quality=quality,
        review_recommended=quality == "low" or has_flags,
        validation_notes=f"{len(extraction.systems)} systems extracted. Quality: {quality}.",
    )
