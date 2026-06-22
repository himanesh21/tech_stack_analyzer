import json
import hashlib
from pathlib import Path
from collections import Counter


CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent


def artifact_dir(company_name: str):
    return PROJECT_ROOT / "artifacts" / company_name


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_text(text: str):
    return " ".join(text.lower().split())


def content_hash(text: str):
    return hashlib.md5(
        normalize_text(text).encode("utf-8")
    ).hexdigest()


def build_duplicate_index(pages):

    hash_counter = Counter()

    for page in pages:
        for section in page["sections"]:

            content = section["content"]

            if not content.strip():
                continue

            h = content_hash(content)

            hash_counter[h] += 1

    return hash_counter


def filter_sections(
    company_name: str,
    heading_frequency_threshold: float = 0.70,
    duplicate_frequency_threshold: float = 0.30,
    min_content_length: int = 100,
):

    artifact = artifact_dir(company_name)

    pages_file = artifact / "page_sections.json"
    headings_file = artifact / "all_headings.json"

    pages = load_json(pages_file)
    headings = load_json(headings_file)

    total_pages = len(pages)

    print(f"Total Pages: {total_pages}")

    # ------------------------------------
    # Heading Frequency Index
    # ------------------------------------

    heading_frequency = {}

    for row in headings:

        heading = normalize_text(
            row["heading"]
        )

        heading_frequency[heading] = (
            row["count"] / total_pages
        )

    # ------------------------------------
    # Duplicate Content Index
    # ------------------------------------

    duplicate_counter = build_duplicate_index(
        pages
    )

    # ------------------------------------
    # Filtering
    # ------------------------------------

    filtered_pages = []

    stats = {
        "kept": 0,
        "removed_frequency": 0,
        "removed_duplicate": 0,
        "removed_short": 0,
    }

    for page in pages:

        kept_sections = []

        for section in page["sections"]:

            heading = normalize_text(
                section["heading"]
            )

            content = section["content"]

            # -------------------------
            # Rule 1
            # Very Short Content
            # -------------------------

            if len(content.strip()) < min_content_length:
                stats["removed_short"] += 1
                continue

            # -------------------------
            # Rule 2
            # High Frequency Heading
            # -------------------------

            if (
                heading_frequency.get(
                    heading,
                    0
                )
                > heading_frequency_threshold
            ):

                stats["removed_frequency"] += 1
                continue

            # -------------------------
            # Rule 3
            # Duplicate Content
            # -------------------------

            h = content_hash(content)

            duplicate_ratio = (
                duplicate_counter[h]
                / total_pages
            )

            if (
                duplicate_ratio
                > duplicate_frequency_threshold
            ):

                stats["removed_duplicate"] += 1
                continue

            kept_sections.append(
                {
                    "heading": section[
                        "heading"
                    ],
                    "content": content,
                }
            )

            stats["kept"] += 1

        if kept_sections:

            filtered_pages.append(
                {
                    "file": page["file"],
                    "source_url": page.get("source_url", ""),
                    "section_count": len(
                        kept_sections
                    ),
                    "sections": kept_sections,
                }
            )

    # ------------------------------------
    # Save Filtered Sections
    # ------------------------------------

    output_file = (
        artifact
        / "filtered_sections.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            filtered_pages,
            f,
            indent=2,
            ensure_ascii=False,
        )

    # ------------------------------------
    # Save Report
    # ------------------------------------

    report = {
        "total_pages": total_pages,
        "kept_sections": stats["kept"],
        "removed_short": stats[
            "removed_short"
        ],
        "removed_frequency": stats[
            "removed_frequency"
        ],
        "removed_duplicate": stats[
            "removed_duplicate"
        ],
    }

    report_file = (
        artifact
        / "filter_report.json"
    )

    with open(
        report_file,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            report,
            f,
            indent=2
        )

    print("\n========== REPORT ==========")
    print(
        f"Kept Sections      : {stats['kept']}"
    )
    print(
        f"Removed Short      : {stats['removed_short']}"
    )
    print(
        f"Removed Frequency  : {stats['removed_frequency']}"
    )
    print(
        f"Removed Duplicate  : {stats['removed_duplicate']}"
    )
    print("============================")

    print(
        f"\nSaved: {output_file}"
    )

    return filtered_pages


if __name__ == "__main__":

    filter_sections(
        company_name="crestdata",
        heading_frequency_threshold=0.70,
        duplicate_frequency_threshold=0.30,
        min_content_length=100,
    )