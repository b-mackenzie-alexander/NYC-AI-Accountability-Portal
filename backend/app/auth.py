import hmac
import os

from fastapi import Header, HTTPException


async def require_admin_token(x_admin_token: str | None = Header(default=None)) -> None:
    expected = os.environ.get("ADMIN_API_TOKEN")
    if not expected:
        raise HTTPException(
            status_code=500, detail="ADMIN_API_TOKEN environment variable is not set."
        )
    if x_admin_token is None:
        raise HTTPException(status_code=401, detail="Missing admin token.")
    if not hmac.compare_digest(x_admin_token, expected):
        raise HTTPException(status_code=403, detail="Invalid admin token.")
