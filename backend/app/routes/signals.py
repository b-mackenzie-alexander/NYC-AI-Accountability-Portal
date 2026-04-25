import os
import json
from fastapi import APIRouter, HTTPException, Request
from supabase import create_client
from app.services.analysis import calculate_disparity_ratios
from app.limiter import limiter

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
            "message": f"Generated {len(signals_created)} {agency}."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate/{agency}")
@limiter.limit("5/minute")

async def generate_agency_signals(request: Request, agency: str): 
    try:
        
        data_resp = supabase.table("outcome_data").select("*").eq("agency", agency).execute()
        
        disparity_signals = calculate_disparity_ratios(data_resp.data)
        
        for sig in disparity_signals:
            
            supabase.table("bias_signals").upsert({
                "agency": agency,
                "signal_type": sig["signal_type"],
                "severity": sig["severity"],
                "description": sig["description"],
                "metadata": sig["metadata"]
            }).execute()

        return {
            "status": "success",
            "signals_analyzed": len(disparity_signals),
            "message": f"Análisis completado para {agency}."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/complaints/{token}")
async def get_complaint_status(token: str):
    
    resp = supabase.table("complaints").select("status, agency").eq("complaint_token", token).single().execute()
    
    if not resp.data:
        raise HTTPException(status_code=404, detail="Token no válido")
        
    return {
        "token": token,
        "status": resp.data["status"],
        "agency": resp.data["agency"],
        "message": "Tu denuncia está siendo procesada y comparada con los hallazgos de IA."
    }
