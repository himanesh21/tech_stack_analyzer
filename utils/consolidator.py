import os
import json
from typing import Dict, Any, List

def consolidate_company_profile(company_name: str, input_dir: str, output_dir: str):
    """
    Consolidates multiple page-level tech extraction JSON files for a single company
    into a single unified company profile, deduplicating tech entries and resolving conflicts.
    """
    if not os.path.exists(input_dir):
        print(f"Error: Input directory {input_dir} does not exist.")
        return
        
    consolidated_techs: Dict[str, Dict[str, Any]] = {}
    
    # Iterate over all JSON files generated for this company
    for filename in os.listdir(input_dir):
        if filename.endswith("_stack.json") or filename.endswith("_structured.json"):
            file_path = os.path.join(input_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Check if it matches our new TechStackExtraction schema
                tech_list = data.get("technologies", [])
                for tech in tech_list:
                    name = tech.get("name", "").strip()
                    if not name:
                        continue
                        
                    # Normalize name key (case-insensitive deduplication)
                    key = name.lower()
                    
                    category = tech.get("category", "")
                    relationship = tech.get("relationship", "")
                    evidence = tech.get("evidence", "")
                    
                    if key not in consolidated_techs:
                        consolidated_techs[key] = {
                            "name": name,
                            "category": category,
                            "relationship": relationship,
                            "sources": [data.get("url", "unknown")],
                            "evidence_snippets": [evidence] if evidence else []
                        }
                    else:
                        # Add source URL if unique
                        url = data.get("url", "unknown")
                        if url not in consolidated_techs[key]["sources"]:
                            consolidated_techs[key]["sources"].append(url)
                        # Add evidence if unique and present
                        if evidence and evidence not in consolidated_techs[key]["evidence_snippets"]:
                            consolidated_techs[key]["evidence_snippets"].append(evidence)
                            
            except Exception as e:
                print(f"Error reading/parsing {filename}: {e}")
                
    # Group results by relationship type
    profile = {
        "company_name": company_name,
        "explicitly_used": [],
        "strongly_implied": [],
        "speculative": []
    }
    
    for tech in consolidated_techs.values():
        relationship = tech["relationship"]
        clean_tech = {
            "name": tech["name"],
            "category": tech["category"],
            "evidence": tech["evidence_snippets"],
            "source_urls": tech["sources"]
        }
        if relationship in profile:
            profile[relationship].append(clean_tech)
        else:
            profile["speculative"].append(clean_tech) # fallback
            
    # Write consolidated profile
    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, f"{company_name}_consolidated_profile.json")
    with open(out_file, 'w+', encoding='utf-8') as f:
        json.dump(profile, f, indent=4)
        
    print(f"Consolidated profile successfully saved to: {out_file}")
    print(f"Found {len(profile['explicitly_used'])} explicit tools, "
          f"{len(profile['strongly_implied'])} strongly implied tools, "
          f"and {len(profile['speculative'])} speculated tools.")

if __name__ == "__main__":
    # Test execution on output directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    input_directory = os.path.join(project_root, "artifacts", "crestdata", "llm")
    output_directory = os.path.join(project_root, "output")
    
    consolidate_company_profile("crestdata", input_directory, output_directory)
