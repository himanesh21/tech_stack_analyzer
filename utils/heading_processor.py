import os
import re
import json
import csv
from collections import Counter
from pathlib import Path


# ==========================================================
# PATH HELPERS
# ==========================================================

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent


def get_markdown_dir(company_name: str) -> Path:
    # Check in current project logs
    v1_path = PROJECT_ROOT / "logs" / company_name / "markdown_files"
    if v1_path.exists():
        return v1_path
        
    # Check in parallel project logs (Data_scrapper_v2)
    v2_path = PROJECT_ROOT.parent / "Data_scrapper_v2" / "logs" / company_name / "markdown_files"
    if v2_path.exists():
        return v2_path
        
    # Check in parent logs folder
    parent_path = PROJECT_ROOT.parent / "logs" / company_name / "markdown_files"
    if parent_path.exists():
        return parent_path
        
    return v1_path


def get_artifact_dir(company_name: str) -> Path:
    artifact_dir = PROJECT_ROOT / "artifacts" / company_name
    artifact_dir.mkdir(parents=True, exist_ok=True)
    return artifact_dir


# ==========================================================
# MARKDOWN PARSER
# ==========================================================

def parse_markdown_sections(markdown_text: str):
    """
    Convert markdown into sections.

    Returns:
    [
        {
            "heading": "...",
            "content": "..."
        }
    ]
    """

    sections = []

    current_heading = "ROOT"
    current_content = []

    for line in markdown_text.splitlines():

        heading_match = re.match(r"^(#{1,6})\s+(.*)", line)

        if heading_match:

            if current_content:
                sections.append({
                    "heading": current_heading.strip(),
                    "content": "\n".join(current_content).strip()
                })

            current_heading = heading_match.group(2).strip()
            current_content = []

        else:
            current_content.append(line)

    if current_content:
        sections.append({
            "heading": current_heading.strip(),
            "content": "\n".join(current_content).strip()
        })

    return sections


# ==========================================================
# EXTRACT ALL PAGE STRUCTURE
# ==========================================================

def extract_page_sections(company_name: str):

    markdown_dir = get_markdown_dir(company_name)

    if not markdown_dir.exists():
        print(f"Error: Markdown directory not found at: {markdown_dir}")
        return [], Counter()

    markdown_files = sorted(markdown_dir.glob("*.md"))

    print(f"Found {len(markdown_files)} markdown files")

    all_pages = []
    heading_counter = Counter()

    for md_file in markdown_files:

        try:

            with open(md_file, "r", encoding="utf-8") as f:
                markdown = f.read()

            sections = parse_markdown_sections(markdown)

            for section in sections:
                heading_counter[section["heading"]] += 1

            file_name = md_file.name
            source_url = "https://" + file_name.replace(".md", "").replace("_", "/")

            all_pages.append({
                "file": file_name,
                "source_url": source_url,
                "section_count": len(sections),
                "sections": sections
            })

        except Exception as e:
            print(f"Error processing {md_file.name}: {e}")

    return all_pages, heading_counter


# ==========================================================
# SAVE PAGE STRUCTURE
# ==========================================================

def save_page_sections(
    company_name: str,
    all_pages: list
):

    artifact_dir = get_artifact_dir(company_name)

    output_file = artifact_dir / "page_sections.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            all_pages,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(f"Saved: {output_file}")


# ==========================================================
# SAVE HEADINGS JSON
# ==========================================================

def save_headings_json(
    company_name: str,
    heading_counter: Counter
):

    artifact_dir = get_artifact_dir(company_name)

    output_file = artifact_dir / "all_headings.json"

    heading_data = [
        {
            "heading": heading,
            "count": count
        }
        for heading, count
        in heading_counter.most_common()
    ]

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            heading_data,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(f"Saved: {output_file}")


# ==========================================================
# SAVE CSV
# ==========================================================

def save_heading_frequency_csv(
    company_name: str,
    heading_counter: Counter
):

    artifact_dir = get_artifact_dir(company_name)

    output_file = artifact_dir / "heading_frequency.csv"

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.writer(f)

        writer.writerow(["heading", "count"])

        for heading, count in heading_counter.most_common():
            writer.writerow([heading, count])

    print(f"Saved: {output_file}")


# ==========================================================
# BUILD LLM PROMPT
# ==========================================================

def build_heading_prompt(
    company_name: str,
    heading_counter: Counter
):

    artifact_dir = get_artifact_dir(company_name)

    output_file = (
        artifact_dir /
        "heading_classification_prompt.txt"
    )

    headings = "\n".join(
        f"- {heading}"
        for heading in heading_counter.keys()
    )

    prompt = f"""
You are a technology due diligence analyst.

Goal:
Identify which headings are useful for discovering:

- Technology Stack
- Programming Languages
- Frameworks
- Cloud Platforms
- DevOps Tools
- Databases
- AI/ML Technologies
- Security Technologies
- Engineering Capabilities

Classify every heading into:

1. KEEP
   High technical value.

2. REVIEW
   Might contain technical information.

3. DISCARD
   Marketing, legal, contact,
   FAQ, footer, testimonials,
   privacy, careers, etc.

Return STRICT JSON:

{{
  "KEEP": [],
  "REVIEW": [],
  "DISCARD": []
}}

HEADINGS:

{headings}
"""

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(prompt)

    print(f"Saved: {output_file}")


# ==========================================================
# MAIN ENTRY FUNCTION
# ==========================================================

def process_headings(company_name: str):

    print("\nExtracting sections...")

    all_pages, heading_counter = (
        extract_page_sections(company_name)
    )

    save_page_sections(
        company_name,
        all_pages
    )

    save_headings_json(
        company_name,
        heading_counter
    )

    save_heading_frequency_csv(
        company_name,
        heading_counter
    )

    build_heading_prompt(
        company_name,
        heading_counter
    )

    print("\nCompleted heading processing")


# ==========================================================
# LOCAL TEST
# ==========================================================

if __name__ == "__main__":

    process_headings("crestdata")