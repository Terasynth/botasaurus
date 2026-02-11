# Security

## API Security
- **API Keys**: Use specific environment variables to secure each scraper endpoint:
    - `NSPIRES_API_KEY`: Secures `/scrape/nspires`
    - `UNIVERSAL_API_KEY`: Secures `/scrape/universal`
- **Request Headers**: Clients must include the `X-API-KEY` header.
- **Verification**: The `server.py` checks the header against the environment variable corresponding to the target.
- Error Handling: Ensure `server.py` handles exceptions to prevent leaking stack traces.
- Input Validation: Validate all incoming JSON payloads in scraper functions.

## Cloud Run Deployment
- **PORT**: Automatically provided by Cloud Run.
- **Secrets Management**: Sensitive keys (like future API keys for Grants.gov or a shared `API_KEY`) should be stored in Secret Manager and injected as environment variables.
- Service Account: Use a dedicated service account with minimal permissions.
