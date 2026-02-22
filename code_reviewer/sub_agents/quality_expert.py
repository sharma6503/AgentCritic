"""Code Quality Expert Agent — uses fast model for parallel expert fleet."""

from google.adk import Agent
from ..config import Config
from ..prompts import QUALITY_EXPERT_PROMPT

_cfg = Config()

quality_expert = Agent(
    name="code_quality_expert",
    model=_cfg.agent_settings.expert_model,
    description="Expert Python code quality reviewer — types, docs, errors, tests.",
    instruction=QUALITY_EXPERT_PROMPT,
    output_key="quality_review_result",
    generate_content_config=_cfg.safety_config,
)
