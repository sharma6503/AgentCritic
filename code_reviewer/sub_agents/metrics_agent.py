"""
Metrics Extractor Agent

Parses the synthesis_result markdown report and extracts structured JSON
with issue counts by severity and category. Used to power the Analysis Card
in the Next.js frontend.

Uses gemini-2.0-flash (fastest model) — this is a simple extraction task.
"""

from google.adk import Agent
from ..config import Config
from ..prompts import METRICS_PROMPT

_cfg = Config()

metrics_agent = Agent(
    name="metrics_agent",
    model=_cfg.agent_settings.expert_model,  # gemini-2.0-flash — fast
    description=(
        "Extracts structured metrics JSON from the synthesis_result markdown report. "
        "Outputs issue counts by severity and category for frontend visualisation."
    ),
    instruction=METRICS_PROMPT,
    output_key="review_metrics",
    generate_content_config=_cfg.safety_config,
)
