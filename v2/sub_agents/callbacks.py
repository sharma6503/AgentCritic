"""
Callbacks for Agent Critic 2.0
"""

import logging
import asyncio
import datetime
import os
from google.adk.agents.callback_context import CallbackContext
from ..config import Config

logger = logging.getLogger(__name__)
configs = Config()

# Traffic Shaping: Concurrency Control
# Ported from v1 to prevent 429 RESOURCE_EXHAUSTED
concurrency_semaphore = asyncio.Semaphore(configs.max_concurrency)

async def traffic_shaper_callback(callback_context: CallbackContext):
    """Limits concurrent LLM requests to stay within quota."""
    logger.debug(f"Agent '{callback_context.agent_name}' waiting for concurrency permit...")
    async with concurrency_semaphore:
        logger.debug(f"Agent '{callback_context.agent_name}' acquired permit. Starting...")
        pass

def constitution_callback(callback_context: CallbackContext):
    """
    Enforces the 'Code Reviewer Constitution' by injecting it into the state.
    """
    callback_context.state.setdefault("constitution", "Be professional and concise.")
    # In 2.0, we use safe path joining
    constitution_path = os.path.join(os.path.dirname(__file__), "..", "..", "code_reviewer", "knowledge_base", "constitution.md")
    try:
        if os.path.exists(constitution_path):
            with open(constitution_path, "r", encoding="utf-8") as f:
                callback_context.state["constitution"] = f.read()
                logger.debug("Constitution injected into state.")
    except Exception as e:
        logger.warning(f"Could not load constitution: {e}")

_REVIEW_STATE_KEYS = [
    "raw_codebase", "code_logic", "code_config", "code_docs",
    "adk_review_result", "quality_review_result", "security_review_result",
    "validation_result", "synthesis_result", "review_metrics", 
    "metrics_chart_b64", "html_report_content"
]

def pre_review_reset_callback(callback_context: CallbackContext):
    """Purges stale state on a new request."""
    current_request = callback_context.state.get("user_request", "")
    previous_request = callback_context.state.get("_previous_user_request", "")

    if current_request and current_request != previous_request:
        logger.info(f"New review request detected. Purging state.")
        for key in _REVIEW_STATE_KEYS:
            if key in callback_context.state:
                del callback_context.state[key]
        callback_context.state["_previous_user_request"] = current_request
    else:
        logger.debug("Same request; skipping reset.")

async def input_guardrail(callback_context: CallbackContext):
    """Mandatory prompt injection defense."""
    user_input = callback_context.state.get("user_request", "")
    # Simple pattern-based injection defense
    injection_patterns = ["ignore previous instructions", "system prompt", "you are now"]
    if any(pattern in user_input.lower() for pattern in injection_patterns):
        logger.warning("Potential prompt injection detected.")
        callback_context.state["user_request"] = "[REDACTED POTENTIAL INJECTION]"

async def output_guardrail(callback_context: CallbackContext):
    """Mandatory identity leakage protection."""
    response = callback_context.state.get("llm_response", "")
    identity_patterns = ["I am an AI", "large language model", "as an AI"]
    for pattern in identity_patterns:
        if pattern.lower() in response.lower():
            logger.warning("Identity leakage detected in response.")
            callback_context.state["llm_response"] = response.replace(pattern, "[AI Assistant]")
