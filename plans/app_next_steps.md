# App Next Steps

1.  **Verify Reconnaissance Endpoint**:
    -   Ensure standard Python environment is set up with `pip install -r requirements.txt`.
    -   Install Playwright browsers with `playwright install chromium`.
    -   Run server using `uvicorn server:app --reload` or `python server.py`.
    -   Test CURL:
        ```bash
        curl -X POST -H "Content-Type: application/json" -H "RECON_API_KEY: your-key" -d '{"url":"https://example.com"}' http://localhost:8080/api/recon
        ```

2.  **Deploy FastAPI & Playwright Environment**:
    -   Update the existing `Dockerfile` to include Playwright system dependencies (`playwright install-deps`).
    -   Push to registry and update Cloud Run service.

3.  **Expand Vulnerability Regex Hook List**:
    - Add logic to intercept and test common injection points automatically instead of just DOM parsing.
