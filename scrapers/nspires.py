from botasaurus.request import request, Request

@request
def scrape_nspires(request: Request, data):
    # 1. Init Session (Get cookies)
    init_url = "https://nspires.nasaprs.com/external/solicitations/solicitations.do?method=init"
    request.get(init_url)
    
    # 2. Fetch Data (Humane Request)
    json_url = "https://nspires.nasaprs.com/external/solicitations/solicitationsJSON.do?path=open"
    # We might want to customize the parameters based on 'data' in the future
    response = request.get(json_url, headers={"Referer": init_url})
    
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Failed to fetch", "status": response.status_code}
