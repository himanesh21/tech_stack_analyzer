import asyncio
import os
from urllib.parse import urlparse

from crawl4ai import AsyncWebCrawler


def write_log_md(data: str, file_path: str):
    """
    Save markdown content to disk.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(data)

    print(f"✅ Saved: {file_path}")


def build_markdown_content(url: str, markdown: str) -> str:
    """
    Store URL along with markdown.
    """

    return f"""# Source URL

{url}

---

{markdown}
"""


async def process_url(
    crawler: AsyncWebCrawler,
    url: str,
    idx: int,
    company_name: str,
    semaphore: asyncio.Semaphore
):
    """
    Crawl a single URL and save markdown.
    """
    
    import re
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    log_dir = os.path.join(project_root, "logs", company_name, "markdown_files")
    
    # Generate the safe file path
    clean_name = re.sub(r'^https?://', '', url).rstrip('/')
    clean_name = re.sub(r'[^a-zA-Z0-9]', '_', clean_name)
    if not clean_name:
        clean_name = f"url_{idx}"
        
    file_path = os.path.join(log_dir, f"{clean_name}.md")
    
    # CACHE CHECK: If file exists, skip crawling
    if os.path.exists(file_path):
        print(f"⏭️ Skipping [{idx}]: Already crawled {url}")
        return

    async with semaphore:
        try:
            print(f"🔄 Crawling [{idx}] {url}")

            result = await crawler.arun(url=url)

            content = build_markdown_content(
                url,
                result.markdown
            )

            write_log_md(content, file_path)

            print(f"✅ Finished [{idx}]")

        except Exception as e:
            print(f"❌ Failed [{idx}] {url}")
            print(e)


async def generate_markdowns(
    urls: list[str],
    company_name: str,
    max_concurrency: int = 10
):
    """
    Generate markdown files for all URLs.
    """

    semaphore = asyncio.Semaphore(max_concurrency)

    async with AsyncWebCrawler() as crawler:

        tasks = [
            process_url(
                crawler=crawler,
                url=url,
                idx=idx,
                company_name=company_name,
                semaphore=semaphore
            )
            for idx, url in enumerate(urls)
        ]

        await asyncio.gather(*tasks)

    print(f"\n🎉 Completed {len(urls)} URLs")


# Optional local testing
if __name__ == "__main__":

    urls = []

    with open(
        "../logs/crestdata/urls_deduplicated_urls.txt",
        "r",
        encoding="utf-8"
    ) as f:
        urls = [
            line.strip()
            for line in f.readlines()
            if line.strip()
        ]

    asyncio.run(
        generate_markdowns(
            urls=urls,
            company_name="crestdata",
            max_concurrency=10
        )
    )