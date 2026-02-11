import trafilatura
from botasaurus.browser import browser, Driver

@browser(
    headless=True,
    block_images=True,  # Speed optimization: don't load images
)
def scrape_universal(driver: Driver, data):
    """
    Universal content extractor.
    Accepts any URL, loads it in a headless Chrome browser (executing JS),
    then extracts the main content using trafilatura.

    Expected payload:
        {
            "url": "https://example.com/some-page"
        }

    Returns:
        {
            "status": 200,
            "data": {
                "title": "...",
                "text": "...",
                "content": "...",
                "excerpt": "...",
                "url": "..."
            }
        }
    """
    url = data.get("url")
    if not url:
        return {"error": "Missing required field: 'url'", "status": 400}

    try:
        # Navigate to the URL (this executes JavaScript)
        driver.get(url)

        # Allow JS frameworks time to render
        driver.short_random_sleep()

        # Get the fully-rendered page source
        page_html = driver.page_html

        # Extract the page title from the browser
        page_title = driver.title

        # Use trafilatura to extract the main content from the rendered HTML
        extracted_text = trafilatura.extract(
            page_html,
            include_comments=False,
            include_tables=True,
            output_format="txt",
        )

        extracted_html = trafilatura.extract(
            page_html,
            include_comments=False,
            include_tables=True,
            output_format="xml",
        )

        # Extract metadata
        metadata = trafilatura.extract_metadata(page_html)

        excerpt = ""
        if metadata:
            excerpt = metadata.description or ""

        return {
            "status": 200,
            "data": {
                "title": page_title or (metadata.title if metadata else ""),
                "text": extracted_text or "",
                "content": extracted_html or "",
                "excerpt": excerpt,
                "url": url,
            },
        }

    except Exception as e:
        return {"error": str(e), "status": 500}
