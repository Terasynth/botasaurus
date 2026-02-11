import os
from flask import Flask, jsonify, request
# Import your scrapers here
from scrapers.nspires import scrape_nspires
from scrapers.universal import scrape_universal

app = Flask(__name__)

# --- Registry of Scrapers ---
# Add new scrapers here as you build them
SCRAPERS = {
    "nspires": scrape_nspires,
    "universal": scrape_universal,
    # "grants_gov": scrape_grants_gov, 
    # "sam_gov": scrape_sam_gov,
}

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "active", "scrapers": list(SCRAPERS.keys())})

@app.route('/scrape/<target>', methods=['GET', 'POST'])
def run_scraper(target):
    # --- API Key Verification ---
    # Define mapping of targets to their respective environment variable keys
    KEY_MAPPING = {
        "nspires": "NSPIRES_API_KEY",
        "universal": "UNIVERSAL_API_KEY"
    }
    
    # Get the environment variable name for the current target
    env_var_name = KEY_MAPPING.get(target, "API_KEY")
    expected_api_key = os.environ.get(env_var_name)
    
    # If a key is set in environment, verify the request header
    if expected_api_key:
        provided_api_key = request.headers.get("X-API-KEY")
        if provided_api_key != expected_api_key:
            return jsonify({"error": f"Unauthorized: Invalid or missing API Key for {target}"}), 401
    # ----------------------------

    if target not in SCRAPERS:
        return jsonify({"error": f"Scraper '{target}' not found"}), 404
        
    try:
        # Get optional data from request body to pass to scraper
        input_data = request.json if request.is_json else {}
        
        # Run the specific scraper function
        # Note: Scraper functions should accept 'data' as a keyword argument
        result = SCRAPERS[target](data=input_data)
        
        # Ensure result is JSON serializable
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
