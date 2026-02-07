# App Next Steps

1.  **Verify Deployment**: Build the Docker image and run locally to test.
    - Command: `docker build -t botasaurus-scraper .`
    - Command: `docker run -e API_KEY=test-key -p 8080:8080 botasaurus-scraper`
2.  **Test Endpoint**: Send a request with the `X-API-KEY` header.
    - Command: `curl -H "X-API-KEY: test-key" http://localhost:8080/scrape/nspires`
3.  **Deploy to Cloud Run**: Push image to registry and deploy, configuring the `API_KEY` secret in Cloud Run.
