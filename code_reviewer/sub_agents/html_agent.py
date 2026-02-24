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

    synthesis_markdown = synthesis_result
    
    import re
    # Extract dynamic title from the first H1 tag in Markdown
    dynamic_title = "Code Review Report"
    title_match = re.search(r'^#\s+(.+)$', synthesis_markdown, re.MULTILINE)
    if title_match:
        dynamic_title = title_match.group(1).strip()

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
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{dynamic_title}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"/>
<style>
    :root {{
        --bg-grad: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        --card-bg: #ffffff;
        --text: #1e293b;
        --heading: #0f172a;
        --border: #e2e8f0;
        --accent: #2563eb;
        --accent-hover: #1d4ed8;
        --code-bg: #f8fafc;
        --code-text: #0f172a;
        --danger: #ef4444;
        --warn: #f59e0b;
        --ok: #10b981;
    }}
    body {{
        font-family: 'Inter', system-ui, sans-serif;
        background: var(--bg-grad);
        color: var(--text);
        line-height: 1.8;
        font-size: 16px;
        padding: 40px 20px;
        margin: 0;
        min-height: 100vh;
    }}
    .container {{
        max-width: 1000px;
        margin: 0 auto;
        background: var(--card-bg);
        padding: 50px;
        border-radius: 16px;
        box-shadow: 0 10px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
        backdrop-filter: blur(10px);
        transform: translateY(20px);
        opacity: 0;
        animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }}
    @keyframes slideUp {{
        to {{ transform: translateY(0); opacity: 1; }}
    }}
    
    h1, h2, h3, h4 {{
        color: var(--heading);
        font-weight: 700;
        margin-top: 2.2em;
        margin-bottom: 0.8em;
        line-height: 1.3;
    }}
    h1 {{ font-size: 2.5rem; text-align: center; border-bottom: none; margin-top: 0; position: relative; padding-bottom: 0.5em; }}
    h1::after {{
        content: ''; position: absolute; bottom: 0; left: 50%; transform: translateX(-50%); width: 80px; height: 4px; background: var(--accent); border-radius: 2px;
    }}
    h2 {{ font-size: 1.75rem; border-bottom: 2px solid var(--border); padding-bottom: 0.4em; transition: color 0.3s ease; }}
    h2:hover {{ color: var(--accent); }}
    
    .meta-dash {{
        background: linear-gradient(to right, rgba(59, 130, 246, 0.05), transparent);
        padding: 20px 25px;
        border-left: 4px solid var(--accent);
        border-radius: 8px;
        margin: 30px 0;
        font-size: 0.95rem;
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
        justify-content: space-between;
        align-items: center;
        box-shadow: inset 0 2px 4px 0 rgb(0 0 0 / 0.02);
    }}
    .meta-item strong {{ color: var(--heading); display: block; font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }}
    

    
    pre {{
        background: var(--code-bg);
        color: var(--code-text);
        padding: 20px;
        border-radius: 10px;
        overflow-x: auto;
        font-size: 0.9em;
        border: 1px solid var(--border);
        box-shadow: inset 0 2px 4px 0 rgb(0 0 0 / 0.03);
    }}
    code {{
        font-family: 'JetBrains Mono', monospace;
        background: rgba(15, 23, 42, 0.04);
        color: #db2777;
        padding: 3px 6px;
        border-radius: 6px;
        font-size: 0.85em;
    }}
    pre code {{ background: transparent; color: inherit; padding: 0; }}
    
    table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin: 25px 0;
        font-size: 0.95em;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid var(--border);
    }}
    th, td {{ padding: 15px 20px; text-align: left; }}
    th {{ background-color: #f8fafc; font-weight: 600; color: var(--heading); border-bottom: 2px solid var(--border); }}
    td {{ border-bottom: 1px solid var(--border); }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background-color: rgba(59, 130, 246, 0.02); }}
    
    blockquote {{
        border-left: 4px solid var(--accent);
        background: rgba(59, 130, 246, 0.03);
        margin: 2em 0;
        padding: 1em 25px;
        border-radius: 0 10px 10px 0;
        font-style: italic;
        color: #475569;
    }}
</style>
</head>
<body>
<div class="container animate__animated animate__fadeIn">
    
    <div class="meta-dash">
        <div class="meta-item"><strong>Reviewed By</strong> im.agentic.review.ai</div>
        <div class="meta-item"><strong>Report Date</strong> {current_date}</div>
        <div class="meta-item"><strong>Focus Areas</strong> Security, Quality, Architecture</div>
    </div>
    
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

html_agent = Agent(
    name="html_agent",
    model=_cfg.agent_settings.synthesis_model,
    description="Generates a visually appealing, structured HTML document from the final code review report.",
    instruction="Refer to HTML_REPORT_PROMPT and callback logic for generation instructions.",
    output_key="html_report",
    generate_content_config=_cfg.safety_config,
    before_agent_callback=generate_and_save_html_callback,
)
