from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import require_admin_token
from app.limiter import limiter
from app.services import database
from app.services.analysis import calculate_disparity_ratios
from app.services.gap_detection import detect_and_store_disclosure_gaps
from app.services.sanitize import sanitize_text

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("")
async def list_signals(
    agency: str | None = None,
    signal_type: str | None = None,
    severity: str | None = None,
) -> list[dict[str, Any]]:
    conditions = []
    params: list[Any] = []
    idx = 1

    if agency:
        conditions.append(f"agency = ${idx}")
        params.append(sanitize_text(agency))
        idx += 1
    if signal_type:
        conditions.append(f"signal_type = ${idx}")
        params.append(sanitize_text(signal_type))
        idx += 1
    if severity:
        conditions.append(f"severity = ${idx}")
        params.append(sanitize_text(severity))
        idx += 1

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return await database.fetch_all(
        f"SELECT * FROM bias_signals {where} ORDER BY generated_at DESC",  # nosec B608
        *params,
    )


@router.post("/check-gaps/{agency}")
@limiter.limit("5/minute")
async def check_disclosure_gaps(
    request: Request,
    agency: str,
    _admin: None = Depends(require_admin_token),
) -> dict[str, object]:
    safe_agency = sanitize_text(agency)
    signals_created = await detect_and_store_disclosure_gaps(safe_agency)

    return {
        "status": "success",
        "gaps_found": signals_created,
        "message": f"Generated {len(signals_created)} transparency signal(s) for {safe_agency}.",
    }


@router.post("/generate/{agency}")
@limiter.limit("5/minute")
async def generate_agency_signals(
    request: Request,
    agency: str,
    _admin: None = Depends(require_admin_token),
) -> dict[str, object]:
    safe_agency = sanitize_text(agency)
    try:
        records = await database.fetch_all(
            "SELECT * FROM outcome_data WHERE agency = $1",
            safe_agency,
        )
        disparity_signals = calculate_disparity_ratios(records)

        for sig in disparity_signals:
            await database.execute(
                """
                INSERT INTO bias_signals
                  (agency, signal_type, severity, description, disparity_ratio, source_urls)
                VALUES ($1, 'disparity', $2, $3, $4, $5)
                """,
                safe_agency,
                sig["severity"],
                sig["description"],
                sig["metadata"]["ratio"],
                [],
            )

        return {
            "status": "success",
            "signals_analyzed": len(disparity_signals),
            "message": f"Analysis complete for {safe_agency}.",
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Signal generation failed.") from None
