import re
import logging
from google.genai import types
from google.adk.tools import ToolContext
from google.adk.tools.load_web_page import load_web_page

logger = logging.getLogger(__name__)

GEMINI_RETIREMENT_URL = "https://cloud.google.com/vertex-ai/docs/generative-ai/learn/model-versioning#gemini-retirement"

def fetch_gemini_model_lifecycle(tool_context: ToolContext = None) -> dict:
    """
    Fetches the latest Gemini model retirement dates from live Google Cloud documentation.
    
    Returns:
    - A dictionary mapping model IDs to their Release and Retirement dates.
    """
    try:
        raw_content = load_web_page(GEMINI_RETIREMENT_URL)
        if not raw_content or "Failed to fetch" in raw_content:
            logger.error(f"Failed to fetch lifecycle data from {GEMINI_RETIREMENT_URL}")
            return {}
        
        # Parse the markdown table
        # Example line: | gemini-2.0-flash-001 | February 5, 2025 | June 1, 2026 |
        lifecycle_data = {}
        
        # Regex for table rows
        table_pattern = re.compile(r'\|\s*([a-zA-Z0-9.-]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|')
        matches = table_pattern.findall(raw_content)
        
        for model_id, release_date, retirement_date in matches:
            model_id = model_id.strip()
            if "gemini" in model_id.lower():
                lifecycle_data[model_id] = {
                    "release_date": release_date.strip(),
                    "retirement_date": retirement_date.strip(),
                    "status": "deprecated" if "2025" in retirement_date or "2024" in retirement_date else "supported"
                }

        return lifecycle_data
    except Exception as e:
        logger.error(f"Error in fetch_gemini_model_lifecycle: {e}")
        return {}
