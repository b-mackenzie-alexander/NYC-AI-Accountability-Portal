import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

load_dotenv()

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    from app.services.database import close_pool, get_pool
    await get_pool()
    yield
    await close_pool()


app = FastAPI(
    title="NYC AI Accountability Portal",
    description="Public API for NYC agency AI disclosure data, bias signals, and complaint intake.",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
# slowapi's handler signature is narrower than FastAPI's expected type — known upstream issue
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

allowed_origins = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


# Routes registered here by Saul as they are built:
# from app.routes import disclosures, signals, complaints, ingest
# app.include_router(disclosures.router)
# app.include_router(signals.router)
# app.include_router(complaints.router)
# app.include_router(ingest.router)
