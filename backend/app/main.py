import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

load_dotenv()

from app.limiter import limiter  # noqa: E402
from app.routes import disclosures, signals, complaints, ingest  # noqa: E402
from app.services.database import close_pool, get_pool  # noqa: E402

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
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


app.include_router(disclosures.router)
app.include_router(complaints.router)
app.include_router(signals.router)
app.include_router(ingest.router)
