import os
from google.genai import types, Client
from google.adk import Agent
from google.adk.agents.invocation_context import InvocationContext
from code_reviewer.config import Config
from code_reviewer.prompts import HTML_REPORT_PROMPT, REPORT_THEMES
import random

_cfg = Config()

async def generate_and_save_html_callback(callback_context):
    """Callback to generate HTML quietly and store it as an ADK artifact."""
    synthesis_result = callback_context.state.get("synthesis_result")
    if not synthesis_result:
        return None

    import markdown
    import datetime

    metrics_img = ""
    metrics_chart_b64 = callback_context.state.get("metrics_chart_b64", "")
    if metrics_chart_b64:
        metrics_img = f'<div class="metrics-container"><img src="data:image/png;base64,{metrics_chart_b64}" alt="Review Metrics" /></div>'
        
    synthesis_markdown = synthesis_result
    
    # 1. Convert Markdown to raw HTML body
    try:
        html_body = markdown.markdown(
            synthesis_markdown,
            extensions=['extra', 'codehilite', 'tables', 'fenced_code', 'nl2br']
        )
    except Exception as e:
        import logging
        logging.error(f"Markdown compilation failed: {e}")
        return types.Content(
            parts=[types.Part(text=f"⚠️ **HTML Compilation Failed:**\n\n`{e}`.")],
            role="model"
        )
        
    current_date = datetime.datetime.now().strftime("%B %d, %Y")

    # 2. Build the Document Skeleton
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Code Review Report</title>
<style>
    :root {{
        --bg: #f8fafc;
        --card-bg: #ffffff;
        --text: #334155;
        --heading: #0f172a;
        --border: #e2e8f0;
        --accent: #2563eb;
        --code-bg: #f1f5f9;
        --danger: #ef4444;
        --warn: #f59e0b;
        --ok: #10b981;
    }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background-color: var(--bg);
        color: var(--text);
        line-height: 1.6;
        padding: 40px 20px;
        margin: 0;
    }}
    .container {{
        max-width: 1000px;
        margin: 0 auto;
        background: var(--card-bg);
        padding: 40px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    }}
    h1, h2, h3, h4 {{
        color: var(--heading);
        margin-top: 2em;
        margin-bottom: 0.5em;
    }}
    h1 {{ font-size: 2.25rem; border-bottom: 2px solid var(--border); padding-bottom: 0.5em; margin-top: 0; }}
    h2 {{ font-size: 1.5rem; border-bottom: 1px solid var(--border); padding-bottom: 0.3em; }}
    p, li {{ font-size: 1rem; }}
    .meta-dash {{
        background: var(--code-bg);
        padding: 15px 20px;
        border-left: 4px solid var(--accent);
        border-radius: 4px;
        margin-bottom: 30px;
        font-size: 0.95rem;
    }}
    .metrics-container img {{
        max-width: 100%;
        height: auto;
        border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        margin: 20px 0;
    }}
    pre {{
        background: var(--code-bg);
        padding: 15px;
        border-radius: 8px;
        overflow-x: auto;
        font-size: 0.9em;
        border: 1px solid var(--border);
    }}
    code {{
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        background: var(--code-bg);
        padding: 2px 4px;
        border-radius: 4px;
        font-size: 0.9em;
    }}
    pre code {{ background: transparent; padding: 0; }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        font-size: 0.95em;
    }}
    th, td {{
        padding: 12px 15px;
        border-bottom: 1px solid var(--border);
        text-align: left;
    }}
    th {{ background-color: var(--bg); font-weight: 600; color: var(--heading); }}
    tr:hover {{ background-color: var(--bg); }}
    blockquote {{
        border-left: 4px solid var(--accent);
        background: var(--bg);
        margin: 1.5em 0;
        padding: 0.5em 20px;
        border-radius: 0 8px 8px 0;
        font-style: italic;
    }}
</style>
</head>
<body>
<div class="container">
    <div class="meta-dash">
        <strong>Reviewed By:</strong> AI Code Reviewer Fleet<br/>
        <strong>Date:</strong> {current_date}<br/>
        <strong>Type:</strong> Automated Security & Quality Audit<br/>
    </div>
    
    {metrics_img}
    
    <div class="content">
        {html_body}
    </div>
</div>
</body>
</html>
"""

    # Save to ADK Artifacts
    artifact = types.Part(
        inline_data=types.Blob(
            data=html_content.encode("utf-8"),
            mime_type="text/html"
        )
    )
    await callback_context.save_artifact(filename="code_review_report.html", artifact=artifact)
    
    # Store in state for other agents
    callback_context.state["html_report"] = html_content
        
        # Return confirmation to skip original agent run and show a clean message
        return types.Content(
            parts=[types.Part(text="✨ **HTML Review Report has been generated!**\n\nThe report has been saved as an ADK artifact: `code_review_report.html`.")],
            role="model"
        )
    return None

html_agent = Agent(
    name="html_agent",
    model=_cfg.agent_settings.synthesis_model,
    description="Generates a visually appealing, structured HTML document from the final code review report.",
    instruction="Refer to HTML_REPORT_PROMPT and callback logic for generation instructions.",
    output_key="html_report",
    generate_content_config=_cfg.safety_config,
    before_agent_callback=generate_and_save_html_callback,
)
