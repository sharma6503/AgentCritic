"""Critic Agent — uses quality model. Fact-checks synthesis_result against raw_codebase."""

from google.adk import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
from ..config import Config
from ..prompts import CRITIC_PROMPT

_cfg = Config()
_END_SENTINEL = "---END-OF-CRITIQUE---"


def _strip_sentinel(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> LlmResponse:
    """Remove the sentinel marker that signals the critic has finished."""
    del callback_context
    if not llm_response.content or not llm_response.content.parts:
        return llm_response
    for idx, part in enumerate(llm_response.content.parts):
        if _END_SENTINEL in (part.text or ""):
            del llm_response.content.parts[idx + 1:]
            part.text = part.text.split(_END_SENTINEL, 1)[0].rstrip()
    return llm_response


critic_agent = Agent(
    name="critic_agent",
    model=_cfg.agent_settings.synthesis_model,
    instruction=CRITIC_PROMPT,
    description="Fact-checks the synthesised report against the raw codebase.",
    output_key="critic_findings",
    after_model_callback=_strip_sentinel,
    generate_content_config=_cfg.safety_config,
)
