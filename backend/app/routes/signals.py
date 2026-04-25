import json
import os
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.limiter import limiter
from app.services import database
from app.services.analysis import calculate_disparity_ratios
from app.services.sanitize import sanitize_text

router = APIRouter(prefix="/signals", tags=["signals"])

DATA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "data", "known_systems.json"
)


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
        f"SELECT * FROM bias_signals {where} ORDER BY generated_at DESC",
        *params,
    )


@router.post("/check-gaps/{agency}")
async def check_disclosure_gaps(agency: str) -> dict[str, object]:
    safe_agency = sanitize_text(agency)

    with open(DATA_PATH) as f:
        known_systems: list[dict] = json.load(f)

    agency_systems = [s for s in known_systems if s["agency"] == safe_agency]

    disclosed_rows = await database.fetch_all(
        "SELECT system_name FROM ai_disclosures WHERE agency_name = $1",
        safe_agency,
    )
    disclosed_names = {row["system_name"].lower() for row in disclosed_rows}

    signals_created: list[str] = []

    for system in agency_systems:
        urls = system.get("source_urls", [])
        if not urls:
            continue

        if system["system_name"].lower() in disclosed_names:
            continue

        existing = await database.fetch_one(
            """
            SELECT id FROM bias_signals
            WHERE agency = $1 AND system_name = $2 AND signal_type = 'disclosure_gap'
            """,
            safe_agency,
            system["system_name"],
        )
        if existing:
            continue

        try:
            await database.execute(
                """
                INSERT INTO bias_signals
                  (agency, system_name, signal_type, severity, description, source_urls)
                VALUES ($1, $2, 'disclosure_gap', 'high', $3, $4)
                """,
                safe_agency,
                system["system_name"],
                f"Known system '{system['system_name']}' does not appear in the official disclosure.",
                urls,
            )
            signals_created.append(system["system_name"])
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to record bias signal.") from None

    return {
        "status": "success",
        "gaps_found": signals_created,
        "message": f"Generated {len(signals_created)} transparency signal(s) for {safe_agency}.",
    }


@router.post("/generate/{agency}")
@limiter.limit("5/minute")
async def generate_agency_signals(request: Request, agency: str) -> dict[str, object]:
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
