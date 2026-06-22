import requests
import json
import os
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

load_dotenv()

SERPER_API_KEY = os.getenv("SERPER")

SERPER_URL = "https://google.serper.dev/search"

HEADERS = {
    "X-API-KEY": SERPER_API_KEY,
    "Content-Type": "application/json"
}


# ==========================================
# SEARCH QUERIES
# ==========================================

def generate_queries(domain: str):

    return [
        {"q": f"{domain} jobs"},
        {"q": f"{domain} careers"},
        {"q": f"{domain} solutions"},
        {"q": f"{domain} case studies"},
        {"q": f"{domain} products"},
        {"q": f"{domain} resources"},
        {"q": f"{domain} infrastructure"}
    ]


# ==========================================
# SERPER SEARCH
# ==========================================

def search_company(domain: str):

    payload = generate_queries(domain)

    response = requests.post(
        SERPER_URL,
        headers=HEADERS,
        json=payload
    )

    response.raise_for_status()

    return response.json()


# ==========================================
# COMPANY URL FILTER
# ==========================================

def is_company_owned(url: str, company_domain: str):

    try:

        netloc = urlparse(url).netloc.lower()

        company_domain = company_domain.lower()

        return (
            netloc == company_domain
            or netloc.endswith("." + company_domain)
        )

    except Exception:
        return False


# ==========================================
# URL INVENTORY
# ==========================================

def extract_company_urls(
    serper_response,
    company_domain
):

    urls = {}

    for search_result in serper_response:

        for result in search_result.get(
            "organic",
            []
        ):

            url = result.get("link")

            if not url:
                continue

            if not is_company_owned(
                url,
                company_domain
            ):
                continue

            urls[url] = {
                "url": url,
                "title": result.get(
                    "title",
                    ""
                ),
                "snippet": result.get(
                    "snippet",
                    ""
                )
            }

    artifacts_dir = PROJECT_ROOT / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    out_path = artifacts_dir / f"serper_{company_domain}_entry_point_urls.json"

    with open(out_path, "w+", encoding="utf-8") as f:
        json.dump(list(urls.values()), f, indent=2)

    print(f"✅ {out_path} successfully saved")

    return list(urls.values())


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    company_domain = "crestdata.ai"

    serper_data = search_company(
        company_domain
    )

    company_urls = extract_company_urls(
        serper_data,
        company_domain
    )

    print(
        json.dumps(
            company_urls,
            indent=2
        )
    )

    main_out_path = PROJECT_ROOT / "artifacts" / "serper_entry_point_urls.json"
    with open(
        main_out_path,
        "w+",
        encoding="utf-8"
    ) as f:

        json.dump(
            company_urls,
            f,
            indent=2
        )

    print(
        f"\nSaved {len(company_urls)} company-owned URLs"
    )