import asyncio
import re
import urllib.parse
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright
import traceback

from llm_auditor import generate_audit_report

# Common API Key Signatures
KEY_PATTERNS = {
    "Google_API_Key": r'AIza[0-9A-Za-z-_]{35}',
    "Stripe_Live_Key": r'sk_live_[0-9a-zA-Z]{24}',
    "Stripe_Secret_Key": r'sk_test_[0-9a-zA-Z]{24}',
    "AWS_Access_Key_ID": r'AKIA[0-9A-Z]{16}',
    "Slack_Token": r'xox[baprs]-[0-9a-zA-Z]{10,48}',
    "Generic_API_Key_Like": r'(?i)(?:api_key|apikey|secret|token)[\s:=]+[\'"]([a-zA-Z0-9_\-\.]{15,})[\'"]'
}

class ReconAuditor:
    def __init__(self, target_url):
        self.start_url = target_url
        self.base_domain = urlparse(target_url).netloc
        self.visited = set()
        self.findings = {
            "api_requests": [],
            "javascript_keys": [],
            "security_headers": {},
            "input_fields": []
        }
        self.max_depth = 2

    async def scan_response_for_keys(self, response):
        """Intercept response, specifically JS files, and scan for API keys."""
        try:
            url = response.url
            if response.status >= 300:
                return
            
            # Record primary document security headers
            if self.start_url.strip('/') == url.strip('/'):
                headers = response.headers
                sec_headers = ['content-security-policy', 'x-frame-options', 'strict-transport-security', 'x-content-type-options', 'x-xss-protection']
                for sh in sec_headers:
                    if sh in headers:
                        self.findings["security_headers"][sh] = headers[sh]
                
            content_type = response.headers.get("content-type", "")
            if "javascript" in content_type or url.endswith(".js"):
                try:
                    text = await response.text()
                    for key_type, pattern in KEY_PATTERNS.items():
                        matches = re.finditer(pattern, text)
                        for match in matches:
                            snippet = text[max(0, match.start() - 20) : min(len(text), match.end() + 20)]
                            # Don't add generic words or massive base64 blocks blindly, but trust the regexes.
                            self.findings["javascript_keys"].append({
                                "type": key_type,
                                "file": url,
                                "matched_snippet": snippet.strip()
                            })
                except Exception as e:
                    # Some responses aren't decodeable or fail
                    pass
        except Exception:
            pass
            
    async def log_request(self, request):
        """Log outgoing API calls, like XHR/Fetch, specifically to identify API surfaces."""
        try:
            if request.resource_type in ["fetch", "xhr"]:
                self.findings["api_requests"].append({
                    "method": request.method,
                    "url": request.url,
                    # Safe serialization of headers
                    "headers": {k: v for k, v in request.headers.items() if k.lower() not in ["cookie", "authorization"]}
                })
        except Exception:
            pass

    async def perform_crawl(self, page, current_url, current_depth):
        if current_depth > self.max_depth or current_url in self.visited:
            return
        
        # Prevent crawling outside the domain
        if urlparse(current_url).netloc != self.base_domain and current_url != self.start_url:
            return
            
        self.visited.add(current_url)
        print(f"[RECON] Crawling: {current_url} (Depth: {current_depth})")
        
        try:
            await page.goto(current_url, wait_until="domcontentloaded", timeout=15000)
            
            # Extract forms/inputs for XSS/Injection
            forms = await page.evaluate(r'''() => {
                let form_data = [];
                document.querySelectorAll('form').forEach(f => {
                    let inputs = [];
                    f.querySelectorAll('input, select, textarea').forEach(inp => {
                        inputs.push({name: inp.name || '', type: inp.type || 'text', id: inp.id || ''});
                    });
                    form_data.push({
                        action: f.action || '',
                        method: f.method || 'get',
                        inputs: inputs
                    });
                });
                return form_data;
            }''')
            
            if forms:
                self.findings["input_fields"].append({
                    "url": current_url,
                    "forms": forms
                })

            # Find next valid internal links if we haven't reached max depth
            if current_depth < self.max_depth:
                hrefs = await page.evaluate(r'''() => {
                    return Array.from(document.querySelectorAll('a')).map(a => a.href);
                }''')
                
                tasks = []
                for href in set(hrefs):
                    if not href.startswith(('http:', 'https:')):
                        continue
                    if urlparse(href).netloc == self.base_domain:
                        # Clean fragments to avoid double crawling #sections
                        clean_href = urllib.parse.urldefrag(href)[0]
                        if clean_href not in self.visited:
                            tasks.append(self.perform_crawl(page, clean_href, current_depth + 1))
                            
                # For safety and speed, we only follow max 5 links per page
                tasks = tasks[:5]
                # To avoid concurrent navigation issues on a single page, we iterate sequentially
                for task in tasks:
                    await task
                    
        except Exception as e:
            print(f"[RECON] Error visiting {current_url}: {e}")

async def run_recon_audit(url: str):
    """Entry point for the reconnaissance task triggered by the API."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
        
    auditor = ReconAuditor(url)
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                ignore_https_errors=True
            )
            
            page = await context.new_page()
            
            # Attach the network interception hooks BEFORE navigating
            page.on("request", auditor.log_request)
            page.on("response", auditor.scan_response_for_keys)
            
            # Begin the depth crawl
            await auditor.perform_crawl(page, auditor.start_url, current_depth=1)
            
            await context.close()
            await browser.close()
            
    except Exception as e:
        traceback.print_exc()
        return {"error": f"Failed to perform scrape context: {str(e)}"}
    
    # Process our findings with the LLM Module
    print("[RECON] Scraping Complete, initiating LLM Audit Analysis...")
    
    # Truncate overly massive findings so it fits in token limits
    context_data = {
        "target": auditor.start_url,
        "scanned_pages": len(auditor.visited),
        "security_headers": auditor.findings["security_headers"],
        "api_endpoints_discovered": auditor.findings["api_requests"][:50],  # Limit to 50 APIs
        "javascript_hardcoded_keys": auditor.findings["javascript_keys"][:10],
        "injection_vectors": auditor.findings["input_fields"][:15]
    }
    
    llm_report = await generate_audit_report(context_data)
    
    return llm_report
