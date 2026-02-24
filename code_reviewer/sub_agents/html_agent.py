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

    # Manually generate HTML using a separate client to avoid streaming to chat
    # If GOOGLE_API_KEY is missing, Client() will automatically fall back to 
    # Vertex AI if GOOGLE_CLOUD_PROJECT and GOOGLE_GENAI_USE_VERTEXAI are set.
    api_key = os.environ.get("GOOGLE_API_KEY")
    client = Client(api_key=api_key) if api_key else Client()
    
    # Pick a random dynamic theme for this report
    selected_theme_instructions = random.choice(REPORT_THEMES)
    
    prompt = HTML_REPORT_PROMPT.format(
        synthesis_result=synthesis_result,
        theme_instructions=selected_theme_instructions
    )
    
    response = client.models.generate_content(
        model=_cfg.agent_settings.synthesis_model,
        contents=prompt
    )
    html_content = response.text

    if html_content:
        # Strip markdown fences using regex to handle conversational text before the code block
        import re
        
        # Try to match everything inside ```html ... ``` or ``` ... ```
        match = re.search(r"```(?:html)?\s*(.*?)\s*```", html_content, re.DOTALL | re.IGNORECASE)
        if match:
            clean_html = match.group(1)
        else:
            # Fallback: find the start of the HTML document
            html_start = html_content.find("<!DOCTYPE")
            if html_start == -1:
                html_start = html_content.find("<html")
            
            if html_start != -1:
                clean_html = html_content[html_start:]
            else:
                clean_html = html_content
                
        html_content = clean_html.strip()
        
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
