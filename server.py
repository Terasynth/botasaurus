import os
import asyncio
from fastapi import FastAPI, Request, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
import uvicorn

# Import existing scrapers
from scrapers.nspires import scrape_nspires
from scrapers.universal import scrape_universal

# Import new async recon scraper
try:
    from scrapers.recon import run_recon_audit
except ImportError:
    run_recon_audit = None

app = FastAPI(title="Botasaurus Scraper & Recon API")

async def get_api_key(x_api_key: str = Header(None)):
    """FastAPI Dependency to verify X-API-KEY header."""
    # We check the specific key for RECON
    expected = os.environ.get("RECON_API_KEY")
    if expected and x_api_key != expected:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid RECON_API_KEY")
    return x_api_key

# --- Registry of Sync Scrapers ---
SCRAPERS = {
    "nspires": scrape_nspires,
    "universal": scrape_universal,
}

class ReconRequest(BaseModel):
    url: str

@app.get('/')
def health_check():
    return {"status": "active", "scrapers": list(SCRAPERS.keys()), "recon_enabled": run_recon_audit is not None}

# We will refactor the generic /scrape to properly handle bodies async
@app.post("/scrape/{target}")
async def run_scraper_post(target: str, request: Request, x_api_key: str = Header(None)):
    # API Verification
    expected_api_key = os.environ.get({"nspires": "NSPIRES_API_KEY", "universal": "UNIVERSAL_API_KEY"}.get(target, "API_KEY"))
    if expected_api_key and x_api_key != expected_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if target not in SCRAPERS:
        raise HTTPException(status_code=404, detail="Scraper not found")
        
    try:
        input_data = await request.json()
    except:
        input_data = {}
        
    print(f"[{target}] JOB_START for {input_data.get('url', 'no-url')}")
    try:
        # Run blocking Botasaurus scrapers in a separate thread so it doesn't block FastAPI
        result = await asyncio.to_thread(SCRAPERS[target], data=input_data)
        print(f"[{target}] JOB_FINISHED")
        return result
    except Exception as e:
        print(f"[{target}] JOB_ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scrape/{target}")
async def run_scraper_get(target: str, request: Request, x_api_key: str = Header(None)):
    # Fallback to GET where params are passed in query
    expected_api_key = os.environ.get({"nspires": "NSPIRES_API_KEY", "universal": "UNIVERSAL_API_KEY"}.get(target, "API_KEY"))
    if expected_api_key and x_api_key != expected_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    if target not in SCRAPERS:
        raise HTTPException(status_code=404, detail="Scraper not found")
        
    input_data = dict(request.query_params)
    print(f"[{target}] JOB_START for {input_data.get('url', 'no-url')}")
    try:
        result = await asyncio.to_thread(SCRAPERS[target], data=input_data)
        print(f"[{target}] JOB_FINISHED")
        return result
    except Exception as e:
        print(f"[{target}] JOB_ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recon")
async def perform_recon(request: ReconRequest, api_key: str = Depends(get_api_key)):
    """Runs a Playwright-based Reconnaissance Security Assessment."""
    if run_recon_audit is None:
        raise HTTPException(status_code=503, detail="Recon module not implemented or loaded yet")
        
    try:
        # Trigger the async scraper logic
        result = await run_recon_audit(request.url)
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("server:app", host='0.0.0.0', port=port, reload=True)
