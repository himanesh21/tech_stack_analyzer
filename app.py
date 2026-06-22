import streamlit as st
import subprocess
import json
import os
from urllib.parse import urlparse
import pandas as pd

# Set page configuration
st.set_page_config(page_title="TechStack Intelligence", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    /* Gradient Header */
    .gradient-header {
        background: linear-gradient(90deg, #6C5CE7 0%, #00CEC9 100%);
        padding: 30px;
        border-radius: 12px;
        color: white;
        margin-bottom: 30px;
    }
    .gradient-header h1 {
        color: white !important;
        margin-bottom: 5px;
        font-size: 2.2rem;
    }
    .gradient-header p {
        font-size: 1.1rem;
        opacity: 0.95;
        margin-top: 0px;
    }
    
    /* Metrics */
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: white;
        margin-bottom: -5px;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #A0AEC0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
    }
    
    /* Tool Cards */
    .tool-card {
        background-color: #1E2329;
        border-radius: 8px;
        padding: 15px 20px;
        margin-bottom: -15px; /* Pull expander up closer */
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid #2D3748;
    }
    .tool-name {
        font-weight: 600;
        font-size: 1.05rem;
        color: white;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    /* Badges */
    .badge {
        font-size: 0.7rem;
        padding: 3px 8px;
        border-radius: 12px;
        font-weight: bold;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    .badge-strictly { background-color: rgba(0, 206, 201, 0.15); color: #00CEC9; border: 1px solid #00CEC9; }
    .badge-explicitly { background-color: rgba(253, 203, 110, 0.15); color: #FDCB6E; border: 1px solid #FDCB6E; }
    .badge-speculation { background-color: rgba(214, 48, 49, 0.15); color: #D63031; border: 1px solid #D63031; }
    
    .source-count {
        font-size: 0.8rem;
        color: #A0AEC0;
        background-color: #2D3748;
        padding: 4px 10px;
        border-radius: 20px;
    }
    
    /* Streamlit overrides */
    div[data-testid="stExpander"] {
        background-color: transparent !important;
        border-color: #2D3748 !important;
        margin-bottom: 15px;
    }
    .streamlit-expanderHeader {
        font-size: 0.9rem !important;
        color: #A0AEC0 !important;
    }
</style>
""", unsafe_allow_html=True)

def get_company_from_url(url: str) -> str:
    parsed = urlparse(url)
    domain = parsed.netloc if parsed.netloc else parsed.path
    if domain.startswith("www."):
        domain = domain[4:]
    return domain.split(".")[0].capitalize()

def run_scraper(domain: str):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    process = subprocess.Popen(
        ["python", "main.py", "--domain", domain],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        bufsize=1,
        env=env
    )
    
    log_container = st.empty()
    logs = ""
    
    with st.spinner(f"Scraping technology stack for {domain}..."):
        for line in iter(process.stdout.readline, ''):
            logs += line
            # Fixed-height scrollable terminal box
            log_container.markdown(
                f"""<div style="
                    background-color: #0d1117;
                    color: #c9d1d9;
                    font-family: 'Courier New', monospace;
                    font-size: 0.8rem;
                    padding: 15px;
                    border-radius: 8px;
                    border: 1px solid #30363d;
                    height: 300px;
                    overflow-y: auto;
                    white-space: pre-wrap;
                    word-break: break-all;
                ">{logs}</div>""",
                unsafe_allow_html=True
            )
            
    process.stdout.close()
    return process.wait() == 0

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🚀 Web Intelligence Scraper")
    st.markdown("<br>", unsafe_allow_html=True)
    
    domain_input = st.text_input("Company Website URL", value="https://crestdata.ai", label_visibility="collapsed")
    
    run_btn = st.button("Run Scraper Pipeline", use_container_width=True)
    
    st.markdown("<br><hr style='border-color: #2D3748;'>", unsafe_allow_html=True)
    
    st.markdown("### 🔍 Search & Filter")
    search_query = st.text_input("Search Technology or Quote", label_visibility="collapsed", placeholder="Search...")
    
    st.markdown("<p style='font-size: 0.8rem; color: #A0AEC0; margin-bottom: 5px; margin-top: 15px;'>Source Type Filter</p>", unsafe_allow_html=True)
    filter_job = st.checkbox("Job Description", value=True)
    filter_company = st.checkbox("Company Owned", value=True)
    
    st.markdown("<br><hr style='border-color: #2D3748;'>", unsafe_allow_html=True)
    st.markdown("### ⚙️ System Info")
    st.markdown("<p style='font-size: 0.85rem; color: #A0AEC0;'>• Built using Streamlit & Custom CSS</p>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.85rem; color: #A0AEC0;'>• Data dynamic parse enabled</p>", unsafe_allow_html=True)


# --- DATA PROCESSING ---
if run_btn:
    if not domain_input:
        st.sidebar.error("Please enter a domain.")
    else:
        st.subheader("Terminal Logs")
        success = run_scraper(domain_input)
        if not success:
            st.error("Pipeline encountered an error. Check logs.")

# Always try to load data based on current input if available
company_name = get_company_from_url(domain_input)
output_path = os.path.join("output", f"{company_name.lower()}_consolidated_profile.json")

if os.path.exists(output_path):
    with open(output_path, "r", encoding="utf-8") as f:
        profile_data = json.load(f)
        
    # Flatten JSON — assign clean confidence labels
    all_tools = []
    
    for tool in profile_data.get("explicitly_used", []):
        tool["confidence"] = "Strictly Mentioned"
        all_tools.append(tool)
        
    for tool in profile_data.get("strongly_implied", []):
        tool["confidence"] = "Explicitly Mentioned"
        all_tools.append(tool)
        
    for tool in profile_data.get("speculative", []):
        tool["confidence"] = "Speculation"
        all_tools.append(tool)

    # --- CATEGORY GROUPING ---
    # Maps raw LLM category strings (keywords) to clean top-level groups
    CATEGORY_GROUPS = {
        "AI & Machine Learning": ["ai", "machine learning", "ml", "llm", "nlp", "generative", "neural", "deep learning", "computer vision", "data science"],
        "Business Application": ["business", "itsm", "crm", "erp", "servicenow", "salesforce", "jira", "confluence", "collaboration", "productivity", "workflow", "automation"],
        "Database": ["database", "db", "sql", "nosql", "storage", "warehouse", "snowflake", "databricks", "redis", "postgres", "mysql", "mongodb", "elastic"],
        "DevOps & Observability": ["devops", "observability", "monitoring", "logging", "datadog", "splunk", "dynatrace", "grafana", "prometheus", "ci/cd", "pipeline", "sre", "reliability"],
        "Cloud & Infrastructure": ["cloud", "aws", "azure", "gcp", "google cloud", "infrastructure", "kubernetes", "docker", "terraform", "serverless", "network"],
        "Security": ["security", "siem", "soar", "xdr", "threat", "vulnerability", "identity", "iam", "sso", "wazuh", "crowdstrike", "firewall"],
        "Other Tools & Libraries": [],  # fallback
    }

    def get_group(raw_category: str) -> str:
        cat_lower = raw_category.lower()
        for group, keywords in CATEGORY_GROUPS.items():
            if any(kw in cat_lower for kw in keywords):
                return group
        return "Other Tools & Libraries"

    for tool in all_tools:
        tool["grouped_category"] = get_group(tool.get("category", ""))
        
    # Apply Search Filter
    if search_query:
        all_tools = [t for t in all_tools if search_query.lower() in t.get("name", "").lower() or any(search_query.lower() in ev.lower() for ev in t.get("evidence", []))]

    # Metrics Calculations — count by confidence level from raw data (before filters)
    strictly_count = len(profile_data.get("explicitly_used", []))
    explicitly_count = len(profile_data.get("strongly_implied", []))
    speculation_count = len(profile_data.get("speculative", []))
    total_count = strictly_count + explicitly_count + speculation_count

    job_mentions = 0
    company_mentions = 0
    
    # Calculate source types based on URL keywords
    for tool in all_tools:
        for url in tool.get("source_urls", []):
            url_lower = url.lower()
            if "naukri" in url_lower or "linkedin" in url_lower or "jobs" in url_lower or "careers" in url_lower:
                job_mentions += 1
            else:
                company_mentions += 1
                
    # Apply Filters (Keep tools if ANY of their URLs match the active filters)
    filtered_tools = []
    for tool in all_tools:
        has_job = any("naukri" in u.lower() or "linkedin" in u.lower() or "jobs" in u.lower() or "careers" in u.lower() for u in tool.get("source_urls", []))
        has_company = any(not ("naukri" in u.lower() or "linkedin" in u.lower() or "jobs" in u.lower() or "careers" in u.lower()) for u in tool.get("source_urls", []))
        
        # If tool has NO URLs, count it as company owned by default
        if not tool.get("source_urls"):
            has_company = True
            
        keep = False
        if filter_job and has_job:
            keep = True
        if filter_company and has_company:
            keep = True
            
        if keep:
            filtered_tools.append(tool)
            
    # Update categories list based on filtered grouped categories (preserve CATEGORY_GROUPS order)
    ordered_groups = list(CATEGORY_GROUPS.keys())
    categories = [g for g in ordered_groups if any(t.get("grouped_category") == g for t in filtered_tools)]

    # --- HEADER UI ---
    st.markdown(f"""
    <div class="gradient-header">
        <h1>🛠️ TechStack Intelligence</h1>
        <p>Discovered Technology profile for <b>{domain_input}</b></p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown('<div class="metric-label">Total Technologies</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{total_count}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-label" style="color:#00CEC9;">Strictly Mentioned</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value" style="color:#00CEC9;">{strictly_count}</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-label" style="color:#FDCB6E;">Explicitly Mentioned</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value" style="color:#FDCB6E;">{explicitly_count}</div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="metric-label" style="color:#D63031;">Speculation</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value" style="color:#D63031;">{speculation_count}</div>', unsafe_allow_html=True)
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # --- CONFIDENCE TABS ---
    def tools_to_df(tools_list):
        rows = []
        for t in tools_list:
            evidence_list = t.get("evidence", [])
            source_urls = t.get("source_urls", [])
            rows.append({
                "Tool Name": t.get("name", ""),
                "Category": t.get("category", ""),
                "Evidence": evidence_list[0] if evidence_list else "",
                "Source URL": source_urls[0] if source_urls else ""
            })
        return pd.DataFrame(rows)

    strictly_tools  = [t for t in filtered_tools if t.get("confidence") == "Strictly Mentioned"]
    explicitly_tools = [t for t in filtered_tools if t.get("confidence") == "Explicitly Mentioned"]
    speculation_tools = [t for t in filtered_tools if t.get("confidence") == "Speculation"]

    tab1, tab2, tab3 = st.tabs([
        "🟢 Strictly Mentioned",
        "🟡 Explicitly Mentioned",
        "🔴 Speculation"
    ])

    with tab1:
        st.markdown("Tools the company **directly and explicitly** states they use in their own documentation.")
        df = tools_to_df(strictly_tools)
        st.dataframe(
            df,
            column_config={
                "Tool Name": st.column_config.TextColumn(width="medium"),
                "Category": st.column_config.TextColumn(width="medium"),
                "Evidence": st.column_config.TextColumn(width="large"),
                "Source URLs": st.column_config.TextColumn(width="large"),
            },
            hide_index=True,
            use_container_width=True,
            height=500
        )

    with tab2:
        st.markdown("Tools **strongly implied** through deep technical context, architectural patterns, or job descriptions.")
        df = tools_to_df(explicitly_tools)
        st.dataframe(
            df,
            column_config={
                "Tool Name": st.column_config.TextColumn(width="medium"),
                "Category": st.column_config.TextColumn(width="medium"),
                "Evidence": st.column_config.TextColumn(width="large"),
                "Source URLs": st.column_config.TextColumn(width="large"),
            },
            hide_index=True,
            use_container_width=True,
            height=500
        )

    with tab3:
        st.markdown("Tools **speculated** based on indirect references or broader industry patterns.")
        df = tools_to_df(speculation_tools)
        st.dataframe(
            df,
            column_config={
                "Tool Name": st.column_config.TextColumn(width="medium"),
                "Category": st.column_config.TextColumn(width="medium"),
                "Evidence": st.column_config.TextColumn(width="large"),
                "Source URLs": st.column_config.TextColumn(width="large"),
            },
            hide_index=True,
            use_container_width=True,
            height=500
        )

else:
    if not run_btn:
        st.info("No data found for this domain yet. Click 'Run Scraper Pipeline' in the sidebar to begin.")
