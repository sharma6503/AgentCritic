"""Security & Deployment Expert Agent — uses fast model for parallel expert fleet."""

from google.adk import Agent
from ..config import Config
from ..prompts import SECURITY_EXPERT_PROMPT

_cfg = Config()

security_expert = Agent(
    name="security_expert",
    model=_cfg.agent_settings.expert_model,
    description="Security and cloud deployment expert — secrets, deps, IAM, Cloud Run.",
    instruction=SECURITY_EXPERT_PROMPT,
    output_key="security_review_result",
    generate_content_config=_cfg.safety_config,
)
