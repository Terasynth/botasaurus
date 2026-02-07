# Protocols

## Scraping Protocol
- Each scraper is a function decorated with `@request`.
- Scrapers must accept `data` as an argument.
- Scrapers return a JSON-serializable dictionary.

## API Protocol
- **Endpoint**: `/scrape/<target>`
- **Method**: POST (preferred) or GET
- **Payload**: JSON body passed to scraper as `data`.
