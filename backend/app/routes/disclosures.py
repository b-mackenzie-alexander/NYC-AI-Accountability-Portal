import os
import json
import pdfplumber
from fastapi import APIRouter, UploadFile, File, HTTPException
from openai import OpenAI  
from supabase import create_client
from dotenv import load_dotenv

# 1. LOAD the environment variables
load_dotenv()

router = APIRouter(prefix="/disclosures", tags=["disclosures"])

# 2. GET credentials
api_key = os.getenv("GEMINI_API_KEY")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY") 

# 3. Validation & Client Setup
if not api_key:
    print(" WARNING: XAI_API_KEY is missing. AI extraction will fail.")

client = OpenAI(
    api_key=api_key or "missing_key",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# Robust Supabase Init (won't crash if keys are placeholders like '///')
is_supabase_valid = supabase_url and "://" in supabase_url and len(supabase_key or "") > 10
supabase = create_client(
    supabase_url if is_supabase_valid else "https://placeholder.supabase.co", 
    supabase_key if is_supabase_valid else "placeholder"
)

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        # 4. Extract text from PDF
        raw_text = ""
        with pdfplumber.open(file.file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    raw_text += page_text + "\n"

        if not raw_text.strip():
            raise ValueError("The uploaded PDF appears to be empty or unreadable.")

        # 5. Smart Model Selection
        # We try the .env model first, but keep backups in case xAI rejects the name
        models_to_try = [os.getenv("MODEL", "gemini-2.5-flash")]
        
        response = None
        last_error = ""

        for model_name in models_to_try:
            if not model_name: continue
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are a specialized legal data extractor. Return ONLY JSON."},
                        {"role": "user", "content": f"Extract: agency_name, system_name, purpose, vendor from: {raw_text[:8000]}"}
                    ],
                    response_format={"type": "json_object"}
                )
                if response: break # Success!
            except Exception as e:
                last_error = str(e)
                print(f"Skipping model {model_name}: {last_error}")

        if not response:
            raise Exception(f"All Grok models failed. Last error: {last_error}")

        # 6. Parse and Print Result
        extracted_data = json.loads(response.choices[0].message.content)
        print(" SUCCESS! Extracted Data:", json.dumps(extracted_data, indent=2))

        # 7. Save to Supabase (Only if valid keys exist)
        if is_supabase_valid:
            supabase.table("ai_disclosures").insert({
                "agency_name": extracted_data.get("agency_name"),
                "system_name": extracted_data.get("system_name"),
                "purpose": extracted_data.get("purpose"),
                "vendor": extracted_data.get("vendor"),
                "disclosure_source_url": file.filename 
            }).execute()
        else:
            print("Local Mode: Skipping database save (No Supabase keys).")

        return {"status": "success", "data": extracted_data}

    except Exception as e:
        print(f" UPLOAD ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))