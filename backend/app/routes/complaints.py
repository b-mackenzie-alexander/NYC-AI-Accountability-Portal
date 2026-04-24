import os
import hmac
import hashlib
import secrets
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import create_client

router = APIRouter(prefix="/complaints", tags=["complaints"])

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

# Check if keys are actually usable
is_db_ready = (
    supabase_url and "://" in supabase_url and 
    supabase_key and len(supabase_key) > 10
)

if is_db_ready:
    supabase = create_client(supabase_url, supabase_key)
else:
    supabase = None 
    print(" Running in LOCAL MODE: Data will not be saved to Supabase.")

# 1. ADD A FALLBACK for the secret so it doesn't crash if .env is missing it
HMAC_SECRET = os.getenv("COMPLAINT_HMAC_SECRET", "temporary_hackathon_secret")

class ComplaintCreate(BaseModel):
    agency: str
    system_name: str | None = None
    incident_description: str
    affected_service: str | None = None

@router.post("")
async def submit_complaint(complaint: ComplaintCreate):
    try:
        # Unique code and anonymous
        nonce = secrets.token_hex(16)
        message = f"{complaint.agency}-{datetime.now().isoformat()}-{nonce}"
        
        token = hmac.new(
            HMAC_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        # 2. ADD THIS IF STATEMENT
        # Only attempt database insert if supabase was successfully initialized
        if supabase:
            data = {
                "complaint_token": token,
                "complaint_nonce": nonce,
                "agency": complaint.agency,
                "system_name": complaint.system_name,
                "incident_description": complaint.incident_description,
                "affected_service": complaint.affected_service
            }
            supabase.table("complaints").insert(data).execute()
        else:
            # This logs to your VS Code terminal so you can verify it's working
            print(f" MOCK SAVE: Generated token {token} for {complaint.agency}")

        # Return the token to the user
        return {
            "status": "success",
            "complaint_token": token,
            "message": "Guarda este código para revisar el estado de tu denuncia."
        }

    except Exception as e:
        # Improved error logging for debugging
        print(f" COMPLAINT ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al procesar denuncia: {str(e)}")