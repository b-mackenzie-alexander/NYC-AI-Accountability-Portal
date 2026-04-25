import os

from openai import AsyncOpenAI


def get_grok_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=os.environ["GROK_API_KEY"],
        base_url="https://api.x.ai/v1",
    )
