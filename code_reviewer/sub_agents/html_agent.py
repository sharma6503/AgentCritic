import os
from google.genai import types, Client
from google.adk import Agent
from google.adk.agents.invocation_context import InvocationContext
from ..config import Config
from ..prompts import HTML_REPORT_PROMPT

_cfg = Config()

async def generate_and_save_html_callback(callback_context):
    """Callback to generate HTML quietly and store it as an ADK artifact."""
    synthesis_result = callback_context.state.get("synthesis_result")
    if not synthesis_result:
        return None

    # Manually generate HTML using a separate client to avoid streaming to chat
    client = Client(api_key=os.environ.get("GOOGLE_API_KEY"))
    prompt = HTML_REPORT_PROMPT.format(synthesis_result=synthesis_result)
    
    response = client.models.generate_content(
        model=_cfg.agent_settings.synthesis_model,
        contents=prompt
    )
    html_content = response.text

    if html_content:
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
    instruction=HTML_REPORT_PROMPT,
    output_key="html_report",
    generate_content_config=_cfg.safety_config,
    before_agent_callback=generate_and_save_html_callback,
)
