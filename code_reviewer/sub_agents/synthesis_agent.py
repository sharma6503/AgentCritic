"""Synthesis Agent — uses quality model for the final report draft."""

from google.adk import Agent
from ..config import Config
from ..prompts import SYNTHESIS_PROMPT

_cfg = Config()

synthesis_agent = Agent(
    name="synthesis_agent",
    model=_cfg.agent_settings.synthesis_model,
    description="Combines expert reviews into a polished Markdown report.",
    instruction=SYNTHESIS_PROMPT,
    output_key="synthesis_result",
    generate_content_config=_cfg.safety_config,
)
