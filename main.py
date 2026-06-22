import argparse
import asyncio
import json
import os
from urllib.parse import urlparse

from utils import serper_discover
from utils import web_crawler
from utils.heading_processor import process_headings
from utils.markdown_generator import generate_markdowns
from utils.filter_section import filter_sections
from utils.build_heading_inventory import build_heading_inventory
from utils.run_extraction import process_all_markdowns
from utils import serper_dorking


def get_company_from_url(url: str) -> str:
    parsed = urlparse(url)

    # Handle domains without scheme
    domain = parsed.netloc if parsed.netloc else parsed.path

    if domain.startswith("www."):
        domain = domain[4:]

    return domain.split(".")[0].capitalize()


def run_pipeline(company_domain: str):
    # Normalize domain — strip any protocol prefix the user may have typed
    company_domain = company_domain.strip().removeprefix("https://").removeprefix("http://").removeprefix("www.").rstrip("/")

    company_name = get_company_from_url(company_domain)
    print(f"\n🚀 Starting Full Data Extraction Pipeline for: {company_domain} ({company_name})\n")

    # 1. Serper Discovery
    print("🔍 [1/5] Discovering Entry Point URLs...")
    serper_data = serper_discover.search_company(company_domain)
    entry_point_urls = serper_discover.extract_company_urls(serper_data, company_domain)

    # 2. Dorking (LinkedIn/Naukri)
    print("🕵️‍♂️ [2/5] Running Google Dorking for Job Descriptions...")
    serper_dorked_data = serper_dorking.search_dork(company_domain)
    dork_urls = serper_dorking.extract_dork_urls(serper_dorked_data, company_domain)
    
    # 3. Combine and Crawl
    print("🌐 [3/5] Crawling Discovered URLs...")
    discovered_urls = asyncio.run(web_crawler.discover_all(entry_point_urls, company_name))
    
    # Extract URL strings from the dork dictionaries and update set
    dork_url_strings = [item["url"] for item in dork_urls]
    discovered_urls.update(dork_url_strings)
    
    processed_url = web_crawler.filter_company_urls(discovered_urls, company_name)
    web_crawler.write_log(processed_url, 'deduplicated_urls', company_name)

    # 4. Generate Markdowns
    print(f"📄 [4/5] Generating Markdowns for {len(processed_url)} URLs...")
    asyncio.run(generate_markdowns(urls=processed_url, company_name=company_name, max_concurrency=10))

    # 5. Extract Headings and Filter Sections
    print("⚙️ [5/5] Processing, Filtering, and Consolidating Data...")
    process_headings(company_name)
    filter_sections(company_name)
    build_heading_inventory(company_name)
    
    # Run LLM
    print("\n🧠 Starting LLM Extraction Pipeline...")
    asyncio.run(process_all_markdowns(company_name))
    
    print("\n🎉 Full Pipeline Execution Complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Tech Stack Scraper Pipeline")
    parser.add_argument("--domain", type=str, default='crestdata.ai', help="Target company domain (e.g., crestdata.ai)")
    args = parser.parse_args()

    # To ensure immediate console flush and handle Windows Unicode character mapping
    import sys
    sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
    
    run_pipeline(args.domain)
