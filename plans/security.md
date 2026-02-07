# Security

## API Security
- Ensure `server.py` handles exceptions to prevent leaking stack traces.
- Use environment variables for sensitive configuration (though currently none are used).
- Validate input in scraper functions.

## Deployment
- Run in a containerized environment (Docker).
- Use non-root user in Docker if possible (currently running as root by default in python images, consider updating Dockerfile).
