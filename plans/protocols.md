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
