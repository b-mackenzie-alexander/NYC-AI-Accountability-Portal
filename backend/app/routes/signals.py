import os
import json
from fastapi import APIRouter, HTTPException
from supabase import create_client

router = APIRouter(prefix="/signals", tags=["signals"])



supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
supabase = None
if supabase_url and "://" in supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(CURRENT_DIR, "..", "data", "known_systems.json")

@router.post("/check-gaps/{agency}")
async def check_disclosure_gaps(agency: str):
    try:
        
        with open(DATA_PATH, "r") as f:
            known_data = json.load(f)
        
        agency_known_systems = known_data.get(agency, [])
        
    
        if not supabase:
            return {"status": "mock", "message": "Local Mode."}
            
        response = supabase.table("ai_disclosures").select("system_name").eq("agency_name", agency).execute()
        disclosed_names = [r["system_name"].lower() for r in response.data]

        signals_created = []

        
        for system in agency_known_systems:
            if system["system_name"].lower() not in disclosed_names:
                
                signal_data = {
                    "agency": agency,
                    "system_name": system["system_name"],
                    "signal_type": "disclosure_gap",
                    "severity": "high",
                    "description": f"Sistema conocido '{system['system_name']}' no aparece en la declaración oficial.",
                    "source_urls": [system["source_url"]]
                }
                supabase.table("bias_signals").insert(signal_data).execute()
                signals_created.append(system["system_name"])

        return {
            "status": "success", 
            "gaps_found": signals_created,
            "message": f"Se generaron {len(signals_created)} señales de transparencia para {agency}."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))