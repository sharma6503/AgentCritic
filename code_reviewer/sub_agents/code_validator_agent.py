"""
Code Validator Agent — uses fast model.
⚠️ BuiltInCodeExecutor must be the ONLY tool on this agent (ADK constraint).
"""

from google.adk import Agent
from google.adk.code_executors import BuiltInCodeExecutor
from ..config import Config
from ..prompts import CODE_VALIDATOR_PROMPT

_cfg = Config()

code_validator_agent = Agent(
    name="code_validator_agent",
    model=_cfg.agent_settings.expert_model,
    description="Validates code by executing snippets in a sandbox.",
    instruction=CODE_VALIDATOR_PROMPT,
    code_executor=BuiltInCodeExecutor(),
    output_key="validation_result",
    generate_content_config=_cfg.safety_config,
)
