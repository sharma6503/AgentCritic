"""Reviser Agent — uses quality model. Applies critic findings to produce final report."""

from google.adk import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
from ..config import Config
from ..prompts import REVISER_PROMPT

_cfg = Config()
_END_SENTINEL = "---END-OF-EDIT---"


def _remove_end_of_edit_mark(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> LlmResponse:
    """Strip the sentinel marker and everything after it."""
    del callback_context
    if not llm_response.content or not llm_response.content.parts:
        return llm_response
    for idx, part in enumerate(llm_response.content.parts):
        if _END_SENTINEL in (part.text or ""):
            del llm_response.content.parts[idx + 1:]
            part.text = part.text.split(_END_SENTINEL, 1)[0].rstrip()
    return llm_response


reviser_agent = Agent(
    name="reviser_agent",
    model=_cfg.agent_settings.synthesis_model,
    instruction=REVISER_PROMPT,
    description="Applies critic findings to produce the final corrected report.",
    after_model_callback=_remove_end_of_edit_mark,
    generate_content_config=_cfg.safety_config,
)
