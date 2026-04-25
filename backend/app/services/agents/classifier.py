from fastapi import HTTPException
from openai.types.chat import ChatCompletionMessageParam
from pydantic import ValidationError

from app.models.pipeline import ClassificationResult
from app.services.agents.llm import create_json_completion

CLASSIFIER_SYSTEM_PROMPT = """
You are a government document classifier specializing in NYC agency AI disclosure filings.

Given raw text from a government PDF, identify:
1. The document type (LL35 annual AI system report, LL144 bias audit, agency policy document, or unknown)
2. The agency name if present
3. Whether the document contains extractable AI system disclosure data

Return ONLY a valid JSON object matching this schema:
{
  "document_type": "ll35_annual_report" | "ll144_bias_audit" | "agency_policy" | "unknown",
  "agency_name": "string or null",
  "confidence": 0.0,
  "extraction_strategy": "full" | "partial" | "skip",
  "notes": "string"
}

Use extraction_strategy "skip" if the document contains no AI system disclosure data.
Use "partial" if disclosure data is present but incomplete or ambiguous.
Use "full" if the document is a clear AI system disclosure filing.
""".strip()


async def run_classifier(text: str) -> ClassificationResult:
    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
        {"role": "user", "content": text[:8000]},
    ]
    raw_json = await create_json_completion(messages)
    try:
        return ClassificationResult(**raw_json)
    except ValidationError:
        raise HTTPException(
            status_code=422,
            detail="Classification failed: response did not match expected schema.",
        ) from None
