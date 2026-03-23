"""
HTML Agent - V2 (Premium Reporter)
=================================
Generates the final high-fidelity HTML report with Neo-Brutalist styling.
Ported from code_reviewer/sub_agents/html_agent.py
"""

import os
import re
import datetime
import logging
from google.adk import Agent
from google.adk.agents.callback_context import CallbackContext
from ..prompts import HTML_REPORT_PROMPT
from ..config import Config

logger = logging.getLogger(__name__)
_cfg = Config()

def prepare_html_context_callback(callback_context: CallbackContext):
    """
    Callback: Prepares additional metadata for the HTML report.
    Ported from v1.
    """
    state = callback_context.state
    state.setdefault("review_timestamp", datetime.datetime.now().strftime("%B %d, %Y %I:%M %p"))
    
    # Logic to calculate overall performance badge
    scores = state.get("scores", {})
    avg = scores.get("overall", 0)
    if avg > 80: badge = "🏆 Elite"
    elif avg > 60: badge = "✅ Reliable"
    else: badge = "⚠️ Needs Work"
    state["performance_status"] = badge
    
    # Prepare logo path
    logo_path = os.path.join(os.path.dirname(__file__), "..", "templates", "adk_logo.png")
    state["adk_logo_url"] = f"file://{logo_path}" if os.path.exists(logo_path) else ""

def save_html_report_callback(callback_context: CallbackContext):
    """
    Callback: Collects LLM output and renders it into the target HTML file.
    """
    state = callback_context.state
    raw_html = state.get("html_report_content", "")
    if not raw_html: return
    
    # Load the template (already copied to v2/templates/report_template.html)
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "report_template.html")
    if not os.path.exists(template_path):
        logger.error(f"Template not found at: {template_path}")
        return
        
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()
        
    # Inject report content (parsing the TITLES/SUMMARY/CONTENT blocks from prompt)
    title = re.search(r"\[TITLE\]: (.*)", raw_html)
    summary = re.search(r"\[SUMMARY\]: (.*)", raw_html, re.DOTALL)
    content = re.search(r"\[CONTENT\]: (.*)", raw_html, re.DOTALL)
    
    html = html.replace("{{ TITLE }}", title.group(1).strip() if title else "CODE REVIEW")
    html = html.replace("{{ SUMMARY }}", summary.group(1).strip() if summary else "")
    html = html.replace("{{ CONTENT }}", content.group(1).strip() if content else "")
    html = html.replace("{{ TIMESTAMP }}", state.get("review_timestamp", ""))
    html = html.replace("{{ PERFORMANCE_STATUS }}", state.get("performance_status", ""))
    html = html.replace("{{ LOGO_URL }}", state.get("adk_logo_url", ""))
    
    # Save the final report
    out_path = os.path.join(os.getcwd(), "report_v2.html")
    with open(out_path, "w", encoding='utf-8') as f:
        f.write(html)
    logger.info(f"Report v2 saved to: {out_path}")
    state["final_report_path"] = out_path

html_agent = Agent(
    name="html_agent",
    model=_cfg.agent_settings.synthesis_model,
    instruction=HTML_REPORT_PROMPT,
    before_agent_callback=prepare_html_context_callback,
    after_agent_callback=save_html_report_callback,
    output_key="html_report_content"
)
