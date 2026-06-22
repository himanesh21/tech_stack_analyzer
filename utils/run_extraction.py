import os
import json
import asyncio
import sys

# Add parent directory to sys.path so we can import from testing/utils
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.tech_extractor import TechStackExtraction, get_json_schema
from utils.consolidator import consolidate_company_profile
from groq import AsyncGroq

# Initialize the Groq Client (make sure GROQ_API_KEY is in your environment variables)
# We set max_retries=0 so the SDK doesn't hang on 429 errors and our custom fallback loop takes over instantly
client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"),max_retries=0)

AVAILABLE_MODELS = {
    "meta-llama/llama-4-scout-17b-16e-instruct": True,
    "qwen/qwen3-32b": True,
    "qwen/qwen3.6-27b": True,
    "llama-3.3-70b-versatile": True,
    "openai/gpt-oss-120b": True
}

def get_active_model() -> str:
    for model, is_active in AVAILABLE_MODELS.items():
        if is_active:
            return model
    return None

# They can choose their favorite LLM library here (e.g., google-genai, groq, litellm)
# Example Google GenAI usage:
# from google import genai
# from google.genai import types

async def extract_tech_stack_with_llm(markdown_content: str) -> dict:
    """
    Calls the Groq API and returns structured JSON matching TechStackExtraction.
    """
    schema = get_json_schema()
    
    system_prompt = f"""
    You are an expert technology due diligence AI. 
    Your goal is to extract the tech stack used by the company from the text provided.
    
    When analyzing the text, you MUST evaluate every tool, platform, or technology against these three criteria:
    1. EXPLICITLY MENTIONED: Does the text explicitly state that the company uses this tool or technology or platform?
    2. STRONGLY IMPLIED: Does the text strongly imply that this tool or platform is being used by the company?
    3. SPECULATIVE: Is the tool or technology only indirectly mentioned, meaning its usage by the company is speculative?
    
    You MUST output valid JSON that strictly adheres to the following JSON Schema:
    {schema}
    
    Do not output any markdown formatting around the JSON. Output ONLY the raw JSON object.
    """
    
    while True:
        model = get_active_model()
        if not model:
            print("❌ All models exhausted their rate limits! Script cannot continue today.")
            raise Exception("All LLM models exhausted.")
            
        kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": markdown_content[:15000]} # Truncate just in case
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1
        }
        
        try:
            response = await client.chat.completions.create(**kwargs)
            
            try:
                return json.loads(response.choices[0].message.content)
            except json.JSONDecodeError:
                print(f"Failed to decode JSON from Groq ({model}). Raw response:", response.choices[0].message.content)
                return {"subject_company": "unknown", "technologies": []}
                
        except Exception as e:
            error_msg = str(e).lower()
            if "429" in error_msg or "rate limit" in error_msg or "exhaust" in error_msg or "quota" in error_msg:
                print(f"\n⚠️ Model '{model}' hit a rate limit or exhausted quota. Disabling it and switching to next model...")
                AVAILABLE_MODELS[model] = False
                continue # Loop back and try the next available model
            else:
                raise e # Raise other errors (like network disconnections)

async def process_all_markdowns(company_name: str):
    filtered_json_path = os.path.join(project_root, "artifacts", company_name, "filtered_sections.json")
    extraction_dir = os.path.join(project_root, "artifacts", company_name, "llm")
    os.makedirs(extraction_dir, exist_ok=True)
    
    if not os.path.exists(filtered_json_path):
        print(f"Error: Filtered JSON {filtered_json_path} does not exist. Run filter_section.py first!")
        return

    with open(filtered_json_path, 'r', encoding='utf-8') as f:
        filtered_pages = json.load(f)

    print(f"Found {len(filtered_pages)} pages to process in filtered_sections.json.")

    for page in filtered_pages:
        filename = page.get("file", "unknown.md")
        source_url = page.get("source_url", "unknown")
        
        # Create a clean filename from the URL (strip https, www, and make it alphanumeric)
        stripped_url = source_url.replace("https://", "").replace("http://", "").replace("www.", "")
        safe_name = "".join(c if c.isalnum() else "_" for c in stripped_url).strip("_")
        if not safe_name:
            safe_name = "unknown_url"
            
        json_path = os.path.join(extraction_dir, f"{safe_name}_stack.json")
        
        if os.path.exists(json_path):
            print(f"Skipping already processed file: {safe_name}")
            continue
            
        print(f"Processing {safe_name}...")
        
        # Reconstruct the page content from the surviving sections
        page_content = ""
        for section in page.get("sections", []):
            page_content += f"## {section.get('heading', '')}\n\n{section.get('content', '')}\n\n"
                
        if not page_content.strip():
            print(f"Skipping {filename}: No technical content left after filtering.")
            continue
            
        try:
            # Extract structured JSON using the LLM helper
            extracted_data = await extract_tech_stack_with_llm(page_content)
            extracted_data["url"] = source_url  # Preserve source URL context
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(extracted_data, f, indent=4)
                
            print(f"✅ Saved extraction to: {json_path}")
            
            # Rate limiting for Groq Free Tier (30K TPM limit on Scout model)
            # Sleep 4 seconds between requests to guarantee we stay under 30,000 Tokens Per Minute
            await asyncio.sleep(4)
            
        except Exception as e:
            print(f"❌ Failed to process {filename}: {e}")
            await asyncio.sleep(10) # Longer backoff on error

    # After extracting all page-level details, consolidate them into a single file
    print("\n🔄 Consolidating all pages into a final unified company profile...")
    output_dir = os.path.join(project_root, "output")
    os.makedirs(output_dir, exist_ok=True)
    consolidate_company_profile(company_name, extraction_dir, output_dir)

if __name__ == "__main__":
    asyncio.run(process_all_markdowns("crestdata"))
