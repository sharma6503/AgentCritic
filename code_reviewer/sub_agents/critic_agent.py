"""Critic Agent — fact-checks the synthesis report against expert findings."""

from google.adk import Agent
from ..config import Config
from ..prompts import CRITIC_PROMPT

_cfg = Config()

critic_agent = Agent(
    name="critic_agent",
    model=_cfg.agent_settings.synthesis_model,
    description="Analyzes the draft report for hallucinations or omissions based on expert input.",
    instruction=CRITIC_PROMPT,
    output_key="critic_feedback",
    generate_content_config=_cfg.safety_config,
)
