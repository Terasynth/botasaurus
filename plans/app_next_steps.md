# App Next Steps

1.  **Implement Universal Scraper**:
    -   Add `trafilatura` to `requirements.txt`.
    -   Create `scrapers/universal.py` with content extraction logic.
    -   Register scraper in `server.py`.

2.  **Verify Implementation**:
    -   Build Docker image: `docker build -t botasaurus-scraper .`
    -   Run container: `docker run -e API_KEY=test-key -p 8080:8080 botasaurus-scraper`
    -   Test CURL:
        ```bash
        curl -X POST -H "X-API-KEY: test-key" -H "Content-Type: application/json" -d '{"url":"https://example.com"}' http://localhost:8080/scrape/universal
        ```

3.  **Deploy**:
    -   Push to registry and update Cloud Run service.
