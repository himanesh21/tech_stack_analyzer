import requests
import json
import os
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv

# Setup Paths
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

# Load Env
load_dotenv()

SERPER_API_KEY = os.getenv("SERPER")
SERPER_URL = "https://google.serper.dev/search"

HEADERS = {
    "X-API-KEY": SERPER_API_KEY,
    "Content-Type": "application/json"
}

def search_dork(domain: str):
    # Dork query specified by user
    query = f'{domain} ("job description" OR "hiring") site:linkedin.com OR site:naukri.com'
    
    payload = [{"q": query}]

    print(f"Executing Dork Query: {query}")
    
    response = requests.post(
        SERPER_URL,
        headers=HEADERS,
        json=payload
    )

    response.raise_for_status()
    return response.json()


def extract_dork_urls(serper_response, company_domain):
    urls = {}

    for search_result in serper_response:
        for result in search_result.get("organic", []):
            url = result.get("link")
            
            if not url:
                continue
                
            # We DO NOT filter by company_domain here because the dork explicitly targets linkedin.com and naukri.com
            
            urls[url] = {
                "url": url,
                "title": result.get("title", ""),
                "snippet": result.get("snippet", "")
            }

    # Ensure artifacts directory exists
    artifacts_dir = PROJECT_ROOT / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    
    output_path = artifacts_dir / f"serper_{company_domain}_dorking_urls.json"
    
    with open(output_path, "w+", encoding="utf-8") as f:
        json.dump(list(urls.values()), f, indent=2)

    print(f"✅ Successfully saved {len(urls)} results to {output_path}")

    return list(urls.values())


if __name__ == "__main__":
    company_domain = "crestdata.ai"

    # 1. Search Serper using Dorking
    serper_data = search_dork(company_domain)

    # 2. Extract and Save the results
    dork_urls = extract_dork_urls(serper_data, company_domain)

    print("\nSample of discovered URLs:")
    for i, item in enumerate(dork_urls[:5]):
        print(f"{i+1}. {item['url']}")
