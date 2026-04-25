import json
import os

from fastapi import HTTPException

from app.services import database
from app.services.sanitize import sanitize_text

DATA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "data", "known_systems.json"
)


async def detect_and_store_disclosure_gaps(agency: str) -> list[str]:
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
        if not urls or system["system_name"].lower() in disclosed_names:
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

    return signals_created
