# Architecture

## Core Components
1.  **FastAPI Server (`server.py`)**: Acts as the API Gateway, routing requests to specific scrapers asynchronously. Replaced Flask for improved async handling.
2.  **Scrapers (`scrapers/`)**: Individual modules containing scraping logic (e.g., `nspires.py`, `universal.py`, `recon.py`). 
    - Recon scraper utilizes `Playwright` for Headless Chromium network interception.
3.  **LLM Auditor (`llm_auditor.py`)**: Uses the Gemini API to formulate Pydantic-validated "Red Team" audit reports based on network findings.
4.  **Docker Container**: Encapsulates the application and dependencies for deployment on Cloud Run.

## Data Flow
Request -> FastAPI Server -> Router -> Scraper/Playwright Task -> External Site -> Response/Interception -> LLM Analysis Engine -> FastAPI Server -> JSON Response
