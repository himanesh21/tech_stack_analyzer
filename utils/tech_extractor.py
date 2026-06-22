import os
import json
from typing import List, Optional
from pydantic import BaseModel, Field

# ==========================================
# PYDANTIC EXTRACTION SCHEMA
# ==========================================

class Technology(BaseModel):
    name: str = Field(
        description="Name of the technology, tool, platform, or language (e.g., Dynatrace, Splunk, AWS, Python, ServiceNow)."
    )
    category: str = Field(
        description="Category of the technology (e.g., Observability, Cloud Provider, SIEM, Database, Programming Language, Framework, IT Service Management)."
    )
    evidence: str = Field(
        description="The exact text snippet or sentence from the markdown file that mentions or implies this technology."
    )
    reasoning: str = Field(
        description="Explanation of why this technology was extracted, including how the context implies its usage or relationship."
    )
    relationship: str = Field(
        description="Must be exactly one of: 'explicitly_used', 'strongly_implied', or 'speculative'."
    )

class TechStackExtraction(BaseModel):
    subject_company: str = Field(
        description="The name of the main company or client described in the case study (e.g., the insurance company or Crest Data)."
    )
    technologies: List[Technology] = Field(
        description="List of all technologies extracted from the text."
    )



def get_json_schema() -> str:
    """Returns the JSON Schema version of the Pydantic models for non-Python LLM clients."""
    return json.dumps(TechStackExtraction.model_json_schema(), indent=2)

if __name__ == "__main__":
    # Print the JSON Schema representation
    print("JSON Schema for LLM response formatting:")
    print(get_json_schema())
