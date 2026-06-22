import asyncio
import os
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
import json
from urllib.parse import urlparse
import re

def write_log(data, entry_point_counter, company_name: str):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    log_dir = os.path.join(project_root, "logs", company_name)
    os.makedirs(log_dir, exist_ok=True)
    with open(os.path.join(log_dir, f'urls_{entry_point_counter}.txt'), 'w+', encoding='utf-8') as f:
        for line in data:
            f.write(line + '\n')
    print(f"Logged file {entry_point_counter} successfully")

def filter_company_urls(urls: list[str], company_name: str) -> list[str]:
    """
    Remove:
    - Media files
    - WordPress assets
    - Blogs
    - News
    - Press releases
    - Events
    - Webinars
    - Podcasts
    - Tags / Authors / Categories
    - Pagination pages
    - Duplicate www/non-www URLs
    """

    MEDIA_EXTENSIONS = {
        '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.ico',
        '.mp4', '.avi', '.mov', '.wmv', '.webm',
        '.mp3', '.wav', '.ogg',
        '.pdf', '.zip', '.rar', '.tar', '.gz',
        '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'
    }

    EXCLUDED_SECTIONS = {
        "blog",
        "blogs",
        "news",
        "press-release",
        "press-releases",
        "event",
        "events",
        "webinar",
        "webinars",
        "podcast",
        "podcasts",
        "author",
        "tag",
        "category"
    }

    # Compile regex pattern for media extensions matching in the path/query/fragment
    sorted_media = sorted(MEDIA_EXTENSIONS, key=len, reverse=True)
    media_extensions_clean = [ext.lstrip('.') for ext in sorted_media]
    media_pattern = re.compile(
        r'\.(?:' + '|'.join(re.escape(ext) for ext in media_extensions_clean) + r')\b',
        re.IGNORECASE
    )

    # Compile regex pattern for excluded sections matching as whole words in the path/query/fragment
    sorted_sections = sorted(EXCLUDED_SECTIONS, key=len, reverse=True)
    excluded_pattern = re.compile(
        r'\b(?:' + '|'.join(re.escape(section) for section in sorted_sections) + r')\b',
        re.IGNORECASE
    )

    filtered_urls = set()

    for url in urls:
        try:
            parsed = urlparse(url)
            path = parsed.path.lower()

            # Construct the parts of the URL after the domain to check against patterns
            url_suffix = parsed.path
            if parsed.query:
                url_suffix += "?" + parsed.query
            if parsed.fragment:
                url_suffix += "#" + parsed.fragment
            url_suffix = url_suffix.lower()

            # Remove media files
            if media_pattern.search(url_suffix):
                continue

            # Remove blog/news/event/etc sections
            if excluded_pattern.search(url_suffix):
                continue

            # Remove WordPress assets
            if "/wp-content/" in path:
                continue

            # Remove pagination
            if re.search(r"/page/\d+/?$", path):
                continue

            # Normalize domain
            normalized_url = url.replace("://www.", "://")

            # Remove trailing slash
            normalized_url = normalized_url.rstrip("/")

            filtered_urls.add(normalized_url)

        except Exception as e:
            print(f"Skipping invalid URL: {url} | Error: {e}")

    write_log(sorted(filtered_urls), "filtered_urls", company_name)

    return sorted(filtered_urls)


async def crawl_single_url(data, idx, company_name, crawler, prefetch_config):
    """Worker function to crawl a single URL concurrently."""
    # This executes in parallel with the other 18 URLs
    discovery = await crawler.arun(
        data["url"],
        config=prefetch_config
    )

    all_urls = [
        link["href"]
        for link in discovery.links.get("internal", [])
    ]

    # Log each file as soon as its specific URL finishes crawling
    write_log(all_urls, idx, company_name)
    
    return all_urls


async def discover_all(urls, company_name):
    discovered_urls = set()
    prefetch_config = CrawlerRunConfig(prefetch=True)

    # Open a single shared browser instance for efficiency
    async with AsyncWebCrawler() as crawler:
        tasks = []
        for idx, data in enumerate(urls):
            # Create a task for each URL instead of awaiting it sequentially
            task = crawl_single_url(data, idx, company_name, crawler, prefetch_config)
            tasks.append(task)
        
        # Fire all 19 requests simultaneously and wait for them all to complete
        results = await asyncio.gather(*tasks)

        # Merge all returned lists into the final unique set
        for all_urls in results:
            discovered_urls.update(all_urls)

    return discovered_urls


if __name__ == "__main__":
    company_name = 'crestdata'
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    with open(os.path.join(project_root, 'artifacts', 'serper_entry_point_urls.json'), 'r') as f:
        urls = json.load(f)

    discovered_urls = asyncio.run(discover_all(urls, company_name))
    
    processed_url=filter_company_urls(discovered_urls, company_name)

    write_log(processed_url,'deduplicated_urls',company_name)

    print(f"Total unique URLs: {len(processed_url)}")
    # print(f"All Discovered URLs: {processed_url}")
