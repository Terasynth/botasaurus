# Architecture

## Core Components
1.  **Flask Server (`server.py`)**: Acts as the API Gateway, routing requests to specific scrapers.
2.  **Scrapers (`scrapers/`)**: Individual modules containing scraping logic (e.g., `nspires.py`).
3.  **Docker Container**: Encapsulates the application and dependencies for deployment on Cloud Run.

## Data Flow
Request -> Flask Server -> Router -> Scraper Function -> External Site -> Response -> Flask Server -> JSON Response
