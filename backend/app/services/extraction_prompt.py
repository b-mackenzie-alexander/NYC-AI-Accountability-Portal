EXTRACTION_SYSTEM_PROMPT = (
    "You are a specialized legal data extractor. "
    "Return ONLY valid JSON with keys: "
    "agency_name, system_name, purpose, vendor, extraction_confidence (0.0-1.0)."
)


def build_extraction_prompt(text: str) -> str:
    return f"Extract AI system disclosure fields from this document:\n\n{text[:8000]}"
