import hashlib
import hmac
import os
import secrets
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.limiter import limiter
from app.services import database
from app.services.sanitize import sanitize_text

router = APIRouter(prefix="/complaints", tags=["complaints"])

_secret = os.environ.get("COMPLAINT_HMAC_SECRET")
if not _secret:
    raise RuntimeError("COMPLAINT_HMAC_SECRET environment variable is not set.")
HMAC_SECRET: str = _secret


class ComplaintCreate(BaseModel):
    agency: str
    system_name: str | None = None
    incident_description: str
    affected_service: str | None = None


@router.post("")
@limiter.limit("10/minute")
async def submit_complaint(request: Request, complaint: ComplaintCreate) -> dict[str, str]:
    nonce = secrets.token_hex(16)
    message = f"{complaint.agency}-{datetime.now().isoformat()}-{nonce}"
    token = hmac.new(HMAC_SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()

    try:
        await database.execute(
            """
            INSERT INTO complaints
              (complaint_token, complaint_nonce, agency, system_name, incident_description, affected_service)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            token,
            nonce,
            sanitize_text(complaint.agency),
            sanitize_text(complaint.system_name or ""),
            sanitize_text(complaint.incident_description),
            sanitize_text(complaint.affected_service or ""),
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to record complaint.") from None

    return {
        "status": "received",
        "complaint_token": token,
        "message": "Save this token to check your complaint status.",
    }


@router.get("/{token}")
async def get_complaint_status(token: str) -> dict[str, str]:
    row = await database.fetch_one(
        "SELECT agency FROM complaints WHERE complaint_token = $1",
        token,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Token not found.")
    return {
        "token": token,
        "status": "received",
        "agency": row["agency"],
    }
