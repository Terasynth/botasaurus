# Botasaurus Cloud Run Deployment Instructions

**Objective**: This service will act as a "scraper host" for Dealflo, supporting multiple different scraping targets (starting with NSPIRES) via a REST API.

---

## 1. Repository Setup

2.  **Create Project Structure**:
    Inside the repo, organize the code to support multiple scrapers. Suggested structure:
    ```text
    /
    ├── Dockerfile          # (See Section 3)
    ├── requirements.txt    # (See Section 3)
    ├── server.py           # The Flask API Gateway (See Section 2)
    └── scrapers/           # Folder for individual scraper modules
        ├── __init__.py
        └── nspires.py      # The NSPIRES logic
    ```

---

## 2. Code Implementation

### A. The Scraper Logic (`scrapers/nspires.py`)
Create a file to encapsulate the NSPIRES logic.
```python
from botasaurus.request import request, Request

@request
def scrape_nspires(request: Request, data):
    # 1. Init Session (Get cookies)
    init_url = "https://nspires.nasaprs.com/external/solicitations/solicitations.do?method=init"
    request.get(init_url)
    
    # 2. Fetch Data (Humane Request)
    json_url = "https://nspires.nasaprs.com/external/solicitations/solicitationsJSON.do?path=open"
    response = request.get(json_url, headers={"Referer": init_url})
    
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Failed to fetch", "status": response.status_code}
```

### B. The API Server
Create a Flask server that dynamically routes requests to the correct scraper.

```python
import os
from flask import Flask, jsonify, request
# Import your scrapers here
from scrapers.nspires import scrape_nspires

app = Flask(__name__)

# --- Registry of Scrapers ---
# Add new scrapers here as you build them
SCRAPERS = {
    "nspires": scrape_nspires,
    # "grants_gov": scrape_grants_gov, 
    # "sam_gov": scrape_sam_gov,
}

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "active", "scrapers": list(SCRAPERS.keys())})

@app.route('/scrape/<target>', methods=['GET', 'POST'])
def run_scraper(target):
    if target not in SCRAPERS:
        return jsonify({"error": f"Scraper '{target}' not found"}), 404
        
    try:
        # Get optional data from request body to pass to scraper
        input_data = request.json if request.is_json else {}
        
        # Run the specific scraper function
        result = SCRAPERS[target](data=input_data)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
```

---

## 3. Docker Configuration

### [requirements.txt]
```text
flask
gunicorn
botasaurus-driver
# Add other botasaurus deps if not included in the base image
```

### [Dockerfile]
Use a Python image that supports browser automation (if needed) or just standard Python for HTTP requests.

```dockerfile
FROM python:3.11-slim

# Install system deps for scraping (Chrome/Gecko) if Botasaurus browser mode is needed
# For 'request' mode (HTTP only), minimal deps are fine:
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libc6-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
EXPOSE 8080

# Run with Gunicorn
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 server:app
```

---

---

## 5. Integration with Dealflo

Once deployed, the Dealflo Edge Function needs the new URL.

**Endpoint Format:**
`https://<SERVICE-URL>/scrape/nspires`

**Update Dealflo Environment Variable:**
