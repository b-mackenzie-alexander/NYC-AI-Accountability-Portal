import json
import os
from collections.abc import Sequence
from json import JSONDecodeError
from typing import Any, cast

import openai
from fastapi import HTTPException
from openai.types.chat import ChatCompletionMessageParam

from app.services.grok_client import get_grok_client


async def create_json_completion(
    messages: Sequence[ChatCompletionMessageParam],
    *,
    primary_model: str | None = None,
) -> dict[str, Any]:
    client = get_grok_client()
    model = primary_model or os.environ.get("GROK_MODEL", "grok-3")

    try:
        response = await client.chat.completions.create(  # type: ignore[call-overload]
            model=model,
            messages=list(messages),
            response_format={"type": "json_object"},
        )
    except openai.RateLimitError:
        try:
            response = await client.chat.completions.create(
                model="grok-3-mini",
                messages=list(messages),
                response_format={"type": "json_object"},
            )
        except openai.RateLimitError:
            raise HTTPException(
                status_code=503,
                detail="LLM rate limit exceeded. Try again later.",
            ) from None

    try:
        raw_json = json.loads(response.choices[0].message.content or "{}")
    except JSONDecodeError:
        raise HTTPException(
            status_code=422,
            detail="Extraction failed: response did not match expected schema.",
        ) from None
    if not isinstance(raw_json, dict):
        raise HTTPException(
            status_code=422,
            detail="Extraction failed: response did not match expected schema.",
        )
    return cast(dict[str, Any], raw_json)
