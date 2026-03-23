"""
Code Validator Agent - V2 (Full implementation)
==============================================
Evaluates code snippets in a safe sandbox.
"""

import logging
from google.adk import Agent
from ..config import Config
from ..prompts import CODE_VALIDATOR_PROMPT

logger = logging.getLogger(__name__)
_cfg = Config()

# Code Validator Agent
# Note: uses the built-in sandbox executor tool in ADK
code_validator_agent = Agent(
    name="code_validator_agent",
    model=_cfg.agent_settings.expert_model,
    instruction=CODE_VALIDATOR_PROMPT,
    output_key="validation_result",
    generate_content_config=_cfg.safety_config,
)
