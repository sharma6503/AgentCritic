import os
import re
import random
import logging
import datetime
from google.genai import types
from google.adk import Agent
from google.adk.agents.callback_context import CallbackContext
from code_reviewer.config import Config
from code_reviewer.prompts import HTML_REPORT_PROMPT

logger = logging.getLogger(__name__)
_cfg = Config()

def prepare_html_context_callback(callback_context: CallbackContext):
    """
    Pre-run callback to prepare context for the Templated HTML report.
    """
    callback_context.state["current_date"] = datetime.datetime.now().strftime("%B %d, %Y %I:%M %p")
    metrics = callback_context.state.get("review_metrics", {})
    scores = metrics.get("scores", {})
    
    # For the hero stat strip: show overall score with a colored badge
    overall = scores.get("overall")
    if isinstance(overall, (int, float)):
        if overall >= 90:
            badge = '<span class="bg-success text-white px-2 py-0.5 text-[10px] font-black uppercase ml-2">GOOD</span>'
        elif overall >= 70:
            badge = '<span class="bg-teal text-white px-2 py-0.5 text-[10px] font-black uppercase ml-2">OK</span>'
        elif overall >= 40:
            badge = '<span class="bg-amber text-slate-900 px-2 py-0.5 text-[10px] font-black uppercase ml-2">WARN</span>'
        else:
            badge = '<span class="bg-error text-white px-2 py-0.5 text-[10px] font-black uppercase ml-2">CRITICAL</span>'
        score_display = f'<div class="flex items-baseline gap-1"><span class="stat-number text-lg sm:text-xl font-black tracking-tighter">{overall}</span><span class="text-white/50 text-xs">/100</span>{badge}</div>'
    else:
        score_display = '<span class="text-white/40 font-black">--</span>'

    callback_context.state["scorecard_html"] = score_display

    # Prepare Repository Metadata HTML
    file_count = callback_context.state.get("logic_file_count", "Unknown")
    module_map = callback_context.state.get("module_map", {})
    modules = ", ".join(list(module_map.keys())[:5]) if module_map else "Analysing..."
    
    # Models from config
    root_mod = _cfg.agent_settings.root_model
    expert_mod = _cfg.agent_settings.expert_model
    synth_mod = _cfg.agent_settings.synthesis_model

    callback_context.state["repo_metadata_html"] = f"""
        <div class="bg-white border-2 border-slate-900 hard-shadow overflow-hidden">
            <div class="bg-slate-50 px-4 sm:px-6 py-2 border-b-2 border-slate-900 flex items-center justify-between">
                <span class="text-[10px] font-black uppercase tracking-widest text-slate-900">REPOSITORY_MANIFEST</span>
                <span class="text-[10px] text-slate-400 font-mono hidden sm:block">STATIC_ANALYSIS_CONTEXT</span>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-3 divide-y sm:divide-y-0 sm:divide-x-2 divide-slate-900">
                <div class="p-4 sm:p-6">
                    <span class="text-[10px] font-bold uppercase tracking-widest text-slate-400 block mb-2">FILES_ANALYZED</span>
                    <span class="text-3xl sm:text-4xl font-black tracking-tighter text-slate-900">{file_count}</span>
                    <span class="text-xs text-slate-400 block mt-1">Source Files</span>
                </div>
                <div class="p-4 sm:p-6">
                    <span class="text-[10px] font-bold uppercase tracking-widest text-slate-400 block mb-2">MODULE_CLUSTERS</span>
                    <span class="text-sm font-bold font-mono tracking-tight text-slate-700 break-all">{modules}</span>
                </div>
                <div class="p-4 sm:p-6">
                    <span class="text-[10px] font-bold uppercase tracking-widest text-slate-400 block mb-2">ANALYSIS_MODELS</span>
                    <div class="space-y-1 text-xs font-mono">
                        <div><span class="text-slate-400">SUP:</span> <span class="text-slate-700">{root_mod}</span></div>
                        <div><span class="text-slate-400">EXP:</span> <span class="text-slate-700">{expert_mod}</span></div>
                        <div><span class="text-slate-400">SYN:</span> <span class="text-slate-700">{synth_mod}</span></div>
                    </div>
                </div>
            </div>
        </div>
    """

    # Prepare metrics chart HTML
    metrics_chart_b64 = callback_context.state.get("metrics_chart_b64", "")
    if metrics_chart_b64:
        callback_context.state["metrics_chart_html"] = f'<div class="metrics-card"><img src="data:image/png;base64,{metrics_chart_b64}" alt="Metrics Bar Chart" /></div>'
    else:
        callback_context.state["metrics_chart_html"] = ""

async def save_html_report_callback(callback_context: CallbackContext):
    """
    Post-run callback to assemble the final HTML from fragments and save it.
    """
    llm_response = callback_context.state.get("html_report_content", "")
    if not llm_response:
        logger.warning("No content fragments found in state for HTML report.")
        return

    # Robust Block Parsing using Regex
    # CRITICAL: Clean markdown fences BEFORE parsing tags — LLMs often wrap output in ```html blocks
    llm_response = re.sub(r'^\s*```(?:html)?\s*\n?', '', llm_response, flags=re.IGNORECASE | re.MULTILINE)
    llm_response = re.sub(r'\n?\s*```\s*$', '', llm_response, flags=re.MULTILINE)
    llm_response = llm_response.strip()

    title_match = re.search(r'\[TITLE\][:\s]*(.*?)(?=\s*\[SUMMARY\]|$)', llm_response, re.DOTALL | re.IGNORECASE)
    summary_match = re.search(r'\[SUMMARY\][:\s]*(.*?)(?=\s*\[CONTENT\]|$)', llm_response, re.DOTALL | re.IGNORECASE)
    content_match = re.search(r'\[CONTENT\][:\s]*(.*)', llm_response, re.DOTALL | re.IGNORECASE)

    if not (title_match and summary_match and content_match):
        logger.warning("LLM response missing required [TITLE], [SUMMARY], or [CONTENT] tags. Using fallback parsing.")
        # Fallback: use whatever we can extract, dump the rest as content
        title = title_match.group(1).strip() if title_match else "Code Review Report"
        summary_html = summary_match.group(1).strip() if summary_match else f'<p class="text-sm leading-relaxed text-slate-600">{llm_response[:800]}</p>'
        content_html = content_match.group(1).strip() if content_match else llm_response
    else:
        title = title_match.group(1).strip()
        summary_html = summary_match.group(1).strip()
        content_html = content_match.group(1).strip()

    # Load the base template
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "report_template.html")
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
    except Exception as e:
        logger.error(f"Failed to load HTML template from {template_path}: {e}")
        return

    # Inject data into template
    final_html = template.replace("{{TITLE}}", title)
    final_html = final_html.replace("{{DATE}}", callback_context.state.get("current_date", ""))
    final_html = final_html.replace("{{HEALTH_SCORECARD}}", callback_context.state.get("scorecard_html", ""))
    final_html = final_html.replace("{{REPO_METADATA}}", callback_context.state.get("repo_metadata_html", ""))
    final_html = final_html.replace("{{METRICS_CHART}}", callback_context.state.get("metrics_chart_html", ""))
    final_html = final_html.replace("{{EXECUTIVE_SUMMARY}}", summary_html)
    final_html = final_html.replace("{{CONTENT}}", content_html)

    # Save to ADK Artifacts
    artifact = types.Part(
        inline_data=types.Blob(
            data=final_html.encode("utf-8"),
            mime_type="text/html"
        )
    )
    
    # Create a safe filename
    safe_filename = re.sub(r'[^a-zA-Z0-9_-]', '_', title).strip('_')[:40] + ".html"
    if not safe_filename or safe_filename == ".html":
        safe_filename = "code_review_report.html"
        
    await callback_context.save_artifact(filename=safe_filename, artifact=artifact)
    logger.info(f"HTML Report generated and saved to ADK Artifact Registry: {safe_filename}")

    # Overwrite the state key so the Root Agent (Supervisor) can return the FULL HTML in the Web UI
    callback_context.state["html_report_content"] = final_html

html_agent = Agent(
    name="html_agent",
    model=_cfg.agent_settings.synthesis_model,
    description="Assembles a premium, high-fidelity HTML report using content fragments and a base template.",
    instruction=HTML_REPORT_PROMPT,
    output_key="html_report_content",
    before_agent_callback=prepare_html_context_callback,
    after_agent_callback=save_html_report_callback,
    generate_content_config=_cfg.safety_config,
)
