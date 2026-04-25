from fastapi import HTTPException
from openai.types.chat import ChatCompletionMessageParam
from pydantic import ValidationError

from app.models.pipeline import ExtractionResult
from app.services.agents.llm import create_json_completion

EXTRACTION_SYSTEM_PROMPT = """
You are an AI governance analyst specializing in public sector algorithmic accountability.

You will receive raw text from a government agency AI disclosure document. Extract structured
information about every AI or automated decision system mentioned.

Return ONLY a valid JSON object. Use null for fields you cannot confidently extract.

Rules:
- Extract ALL systems mentioned, even if details are sparse.
- Do not infer or hallucinate information not present in the text.
- extraction_confidence reflects your confidence that you captured all systems.
- If the document has no AI disclosures, return an empty systems array with extraction_confidence 1.0 and an explanatory note.
- Do not merge multiple systems into one record.
""".strip()


def build_extractor_prompt(text: str, document_type: str, agency_name: str) -> str:
    return (
        f"Document type: {document_type}\n"
        f"Agency name: {agency_name}\n\n"
        "Return JSON with keys agency_name, systems, extraction_confidence, missing_fields_note.\n\n"
        f"Document text:\n{text[:12000]}"
    )


async def run_extractor(text: str, document_type: str, agency_name: str) -> ExtractionResult:
    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": build_extractor_prompt(text, document_type, agency_name)},
    ]
    raw_json = await create_json_completion(messages)
    if "extraction_confidence" not in raw_json:
        raw_json["extraction_confidence"] = 0.5
    try:
        extraction = ExtractionResult(**raw_json)
    except ValidationError:
        raise HTTPException(
            status_code=422,
            detail="Extraction failed: response did not match expected schema.",
        ) from None

    extraction.systems = [
        system for system in extraction.systems if system.system_name and system.system_name.strip()
    ]
    return extraction
