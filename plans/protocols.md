# Protocols

## Scraping Protocol
- Each scraper is a function decorated with `@request`.
- Scrapers must accept `data` as an argument.
- Scrapers return a JSON-serializable dictionary.

## API Protocol
- **Endpoint**: `/scrape/<target>`
- **Method**: POST
- **Payload**: JSON body passed to scraper as `data`.
- **Authentication**: Include the `X-API-KEY` header with your valid API key.
    - Example: `curl -H "X-API-KEY: your_api_key_here" http://<SERVICE-URL>/scrape/nspires`

## Universal Scraper Protocol
- **Endpoint**: `/scrape/universal`
- **Method**: POST
- **Payload**:
    ```json
    {
        "url": "https://example.com/article",
        "render_js": false // Optional, defaults to false (Note: True requires browser support not currently in Dockerfile)
    }
    ```
- **Response**:
    ```json
    {
        "status": 200,
        "data": {
            "title": "Page Title",
            "content": "<div>Extracted HTML content...</div>",
            "text": "Extracted plain text content...",
            "excerpt": "Short summary...",
            "url": "https://example.com/article"
        }
    }
    ```
