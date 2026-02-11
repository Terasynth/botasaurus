import trafilatura
import time
from botasaurus.browser import browser, Driver
from botasaurus.request import request, Request

def log_event(event, details=""):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [UNIVERSAL] {event}: {details}")

@request
def _scrape_request_only(request: Request, url):
    """Fast path using HTTP requests only with stealth headers."""
    log_event("REQUEST_START", url)
    
    # Stealth headers to mimic a real browser for the fast path
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }
    
    try:
        response = request.get(url, headers=headers, timeout=15)
        log_event("REQUEST_COMPLETE", f"Status: {response.status_code}")
        return response.text
    except Exception as e:
        log_event("REQUEST_FAILED", str(e))
        return ""

@browser(
    headless=True,
    block_images=True,
    # Use stealth mode if available in the installed version, 
    # otherwise defaults are handled by Botasaurus
    tiny_profile=True,
)
def _scrape_browser_only(driver: Driver, data):
    """Slow path using headless Chrome."""
    url = data.get("url")
    log_event("BROWSER_START", url)
    
    try:
        # Navigate to the URL
        # We increase timeout for heavy sites like Amazon
        driver.get(url, wait_cb=lambda d: d.wait_for_element('body', timeout=30))
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
    1. Tries fast HTTP request first (with stealth headers).
    2. If content is missing or looks like a JS-app, falls back to Browser.
    """
    url = data.get("url")
    if not url:
        return {"error": "Missing required field: 'url'", "status": 400}

    # Normalize URL
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    start_time = time.time()
    log_event("JOB_START", url)

    try:
        # STEP 1: FAST PATH (HTTP Request)
        html = _scrape_request_only(url)
        content = trafilatura.extract(html) if html else None
        
        # Check for Amazon specific block or empty content
        is_blocked = "To discuss automated access to Amazon data please contact" in (html or "")
        
        if content and len(content) > 300 and not is_blocked:
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
