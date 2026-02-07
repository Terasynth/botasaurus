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
        # Note: Scraper functions should accept 'data' as a keyword argument
        result = SCRAPERS[target](data=input_data)
        
        # Ensure result is JSON serializable
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
