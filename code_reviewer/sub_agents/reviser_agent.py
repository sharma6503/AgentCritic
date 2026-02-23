"""Reviser Agent — applies critic feedback to the synthesis report."""

from google.adk import Agent
from ..config import Config
from ..prompts import REVISER_PROMPT

_cfg = Config()

reviser_agent = Agent(
    name="reviser_agent",
    model=_cfg.agent_settings.synthesis_model,
    description="Incorporates critiques into the final refined Markdown report.",
    instruction=REVISER_PROMPT,
    output_key="synthesis_result",
    generate_content_config=_cfg.safety_config,
)
