# Security

## API Security
- **API Key**: It is highly recommended to use an `API_KEY` environment variable to secure the scrapers. The `server.py` should be updated to check for this key in the request headers (e.g., `X-API-KEY`).
- Error Handling: Ensure `server.py` handles exceptions to prevent leaking stack traces.
- Input Validation: Validate all incoming JSON payloads in scraper functions.

## Cloud Run Deployment
- **PORT**: Automatically provided by Cloud Run.
- **Secrets Management**: Sensitive keys (like future API keys for Grants.gov or a shared `API_KEY`) should be stored in Secret Manager and injected as environment variables.
- Service Account: Use a dedicated service account with minimal permissions.
