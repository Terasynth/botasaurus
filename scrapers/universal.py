import trafilatura
import time
from botasaurus.browser import browser, Driver
from botasaurus.request import request, Request

def log_event(event, details=""):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [UNIVERSAL] {event}: {details}")

@request
def _scrape_request_only(request: Request, url):
    """Fast path using HTTP requests only."""
    log_event("REQUEST_START", url)
    response = request.get(url, timeout=10)
    log_event("REQUEST_COMPLETE", f"Status: {response.status_code}")
    return response.text

@browser(
    headless=True,
    block_images=True,
)
def _scrape_browser_only(driver: Driver, data):
    """Slow path using headless Chrome."""
    url = data.get("url")
    log_event("BROWSER_START", url)
    
    try:
        # Navigate to the URL
        driver.get(url, wait_cb=lambda d: d.wait_for_element('body', timeout=15))
        log_event("BROWSER_PAGE_LOADED")

        # Get the fully-rendered page source and title
        page_html = driver.page_html
        page_title = driver.title
        
        return {
            "html": page_html,
            "title": page_title
        }
    except Exception as e:
        log_event("BROWSER_ERROR", str(e))
        raise e

def scrape_universal(data):
    """
    Hybrid Universal content extractor.
    1. Tries fast HTTP request first.
    2. If content is missing or looks like a JS-app, falls back to Browser.
    """
    url = data.get("url")
    if not url:
        return {"error": "Missing required field: 'url'", "status": 400}

    start_time = time.time()
    log_event("JOB_START", url)

    try:
        # STEP 1: FAST PATH (HTTP Request)
        html = _scrape_request_only(url)
        content = trafilatura.extract(html)
        
        # If we got meaningful content, return immediately
        # We check for common "JS required" markers or empty content
        if content and len(content) > 200: # Threshold for "meaningful" content
            log_event("FAST_PATH_SUCCESS", f"Extracted {len(content)} chars")
            return _format_response(url, html, content, start_time)
        
        log_event("FAST_PATH_INSUFFICIENT", "Falling back to browser mode")

        # STEP 2: SLOW PATH (Browser)
        browser_res = _scrape_browser_only(data)
        html = browser_res["html"]
        content = trafilatura.extract(html)
        
        log_event("SLOW_PATH_COMPLETE", f"Extracted {len(content) if content else 0} chars")
        return _format_response(url, html, content, start_time, title=browser_res["title"])

    except Exception as e:
        log_event("JOB_FAILED", str(e))
        return {"error": str(e), "status": 500}

def _format_response(url, html, text, start_time, title=None):
    metadata = trafilatura.extract_metadata(html)
    duration = time.time() - start_time
    log_event("JOB_FINISHED", f"Duration: {duration:.2f}s")
    
    return {
        "status": 200,
        "data": {
            "title": title or (metadata.title if metadata else ""),
            "text": text or "",
            "content": trafilatura.extract(html, output_format="xml") or "",
            "excerpt": metadata.description if metadata else "",
            "url": url,
            "debug": {
                "duration_s": round(duration, 2)
            }
        }
    }
