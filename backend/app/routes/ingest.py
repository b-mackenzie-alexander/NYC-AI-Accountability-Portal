import json
import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import require_admin_token
from app.limiter import limiter
from app.services import database

router = APIRouter(prefix="/ingest", tags=["ingest"])

DATA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "data", "socrata_datasets.json"
)


@router.post("/socrata")
@limiter.limit("5/minute")
async def ingest_nyc_data(
    request: Request,
    _admin: None = Depends(require_admin_token),
) -> dict[str, object]:
    with open(DATA_PATH) as f:
        datasets: list[dict] = json.load(f)

    if not datasets:
        raise HTTPException(status_code=500, detail="No datasets configured.")

    app_token = os.environ.get("SOCRATA_APP_TOKEN", "")
    total_ingested = 0

    for dataset in datasets:
        url = dataset["url"]
        agency = dataset["agency"]
        dataset_id = dataset["dataset_id"]
        outcome_type = dataset.get("outcome_type", "referral")
        year = int(dataset.get("year", 2024))
        count_column = dataset.get("count_column", "count")
        report_period = dataset.get("report_period")

        params: dict[str, str] = {
            "$limit": "1000",
            "category": "Race/Ethnicity",
            "child_parent": "Children",
        }
        if report_period:
            params["report_period"] = report_period
        if app_token:
            params["$$app_token"] = app_token

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)

        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="Socrata fetch failed.")

        raw_data: list[dict] = response.json()
        records = raw_data[:100]

        for record in records:
            raw_count = record.get(count_column, "0")
            try:
                count = int(float(str(raw_count).strip()))
            except (ValueError, TypeError):
                count = 0

            await database.execute(
                """
                INSERT INTO outcome_data
                  (agency, dataset_id, year, race_ethnicity, outcome_type, count)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (agency, dataset_id, year, race_ethnicity, outcome_type)
                DO UPDATE SET count = EXCLUDED.count
                """,
                agency,
                dataset_id,
                year,
                record.get("sub_category", ""),
                outcome_type,
                count,
            )

        total_ingested += len(records)

    return {
        "status": "success",
        "records_ingested": total_ingested,
        "message": f"Ingested {total_ingested} records across {len(datasets)} dataset(s).",
    }
