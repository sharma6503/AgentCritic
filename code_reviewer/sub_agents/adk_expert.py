"""
ADK Architecture Expert Agent — uses fast model for parallel expert fleet.
"""

import logging
from google.adk import Agent
from google.adk.planners.plan_re_act_planner import PlanReActPlanner
from ..config import Config
from ..prompts import ADK_EXPERT_PROMPT
from ..utils.compat import get_binary_path, SafeMcpToolset

from google.adk.agents.callback_context import CallbackContext
import logging
logger = logging.getLogger(__name__)

_cfg = Config()
_tools = []

def adk_expert_callback(callback_context: CallbackContext):
    """Debug callback to verify expert output."""
    res = callback_context.state.get("adk_review_result", "")
    keys = list(callback_context.state.keys()) if isinstance(callback_context.state, dict) else list(callback_context.state.to_dict().keys())
    logger.info(f"ADK EXPERT CALLBACK: Output length: {len(res)}. State keys: {keys}")

# MCP tools enabled
if get_binary_path("uv"):
    try:
        from google.adk.tools.mcp_tool import McpToolset
        from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
        from mcp import StdioServerParameters

        _adk_docs_mcp = SafeMcpToolset(McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="uvx",
                    args=[
                        "--from", "mcpdoc", "mcpdoc",
                        "--urls",
                        "AgentDevelopmentKit:https://google.github.io/adk-docs/llms.txt",
                    ],
                ),
            ),
            tool_filter=["fetch_docs", "list_doc_sources"],
        ))
        _tools.append(_adk_docs_mcp)
        logger.info("ADK Docs SafeMcpToolset loaded via uvx.")
    except Exception as e:
        logger.warning(f"Failed to load ADK Docs MCP: {e}")

adk_expert = Agent(
    name="adk_architecture_expert",
    model=_cfg.agent_settings.expert_model,
    description="Expert in Google Agent Development Kit (ADK) architecture.",
    instruction=ADK_EXPERT_PROMPT,
    tools=_tools,
    planner=PlanReActPlanner(),
    output_key="adk_review_result",
    after_agent_callback=adk_expert_callback,
    generate_content_config=_cfg.safety_config,
)
