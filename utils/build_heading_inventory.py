import json
from pathlib import Path
from collections import Counter

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent


def artifact_dir(company_name: str):
    return PROJECT_ROOT / "artifacts" / company_name


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_heading(text: str):
    return " ".join(text.strip().split())


def build_heading_inventory(company_name: str):

    artifact = artifact_dir(company_name)

    filtered_file = artifact / "filtered_sections.json"

    pages = load_json(filtered_file)

    heading_counter = Counter()

    for page in pages:

        for section in page["sections"]:

            heading = normalize_heading(
                section["heading"]
            )

            heading_counter[heading] += 1

    inventory = []

    for heading, count in heading_counter.most_common():

        inventory.append({
            "heading": heading,
            "count": count
        })

    inventory_file = (
        artifact /
        "heading_inventory.json"
    )

    with open(
        inventory_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            inventory,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"Saved: {inventory_file}"
    )

    return inventory


def build_prompt(
    company_name: str,
    inventory: list
):

    artifact = artifact_dir(company_name)

    prompt_file = (
        artifact /
        "heading_classification_prompt.txt"
    )

    headings = []

    for row in inventory:

        headings.append(
            f"- {row['heading']} "
            f"(count={row['count']})"
        )

    prompt = f"""
You are performing technology due diligence.

Goal:
Identify the technologies,
frameworks,
programming languages,
cloud services,
AI/ML stack,
data stack,
observability stack,
security stack,
and engineering capabilities
used by this company.

Classify every heading into:

TECHNICAL
POSSIBLY_TECHNICAL
NON_TECHNICAL

Definitions:

TECHNICAL:
Contains implementation details,
architecture,
tools,
platforms,
integrations,
engineering processes,
technology capabilities.

POSSIBLY_TECHNICAL:
Could contain useful technical context
such as customer challenges,
business impact,
executive summaries.

NON_TECHNICAL:
Leadership,
careers,
testimonials,
contact pages,
privacy policies,
marketing content,
social media,
team information.

Return ONLY JSON:

{{
    "TECHNICAL": [],
    "POSSIBLY_TECHNICAL": [],
    "NON_TECHNICAL": []
}}

HEADINGS:

{chr(10).join(headings)}
"""

    with open(
        prompt_file,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(prompt)

    print(
        f"Saved: {prompt_file}"
    )


def process(company_name: str):

    inventory = build_heading_inventory(
        company_name
    )

    build_prompt(
        company_name,
        inventory
    )

    print()
    print(
        f"Unique headings: {len(inventory)}"
    )


if __name__ == "__main__":

    process("crestdata")