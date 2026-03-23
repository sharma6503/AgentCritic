"""
ADK Architecture Expert - V2 (Full implementation)
================================================
Equipped with:
  1. ADK Docs MCP
  2. Google Developer Knowledge MCP
  3. Vertex AI Model Lifecycle Tool
"""

import logging
import os
from google.adk import Agent
from google.adk.planners.plan_re_act_planner import PlanReActPlanner
from ..config import Config
from ..prompts import ADK_EXPERT_PROMPT
from ..tools.lifecycle_tool import fetch_gemini_model_lifecycle
from ..utils.compat import get_binary_path, SafeMcpToolset

logger = logging.getLogger(__name__)
_cfg = Config()
_tools = [fetch_gemini_model_lifecycle]

# Load MCP tools if uv is available
try:
    from google.adk.tools.mcp_tool import McpToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
    from mcp import StdioServerParameters

    # ADK Docs MCP
    _tools.append(SafeMcpToolset(McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="uvx",
                args=["--from", "mcpdoc", "mcpdoc", "--urls", "AgentDevelopmentKit:https://google.github.io/adk-docs/llms.txt"],
            ),
        ),
        tool_filter=["fetch_docs", "list_doc_sources"],
    )))

    # Google Knowledge MCP
    _tools.append(SafeMcpToolset(McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="uvx",
                args=["--from", "google-developer-knowledge-mcp", "google-developer-knowledge-mcp"],
            ),
        ),
        tool_filter=["search_documents", "get_documents"],
    )))
except Exception as e:
    logger.warning(f"ADK Expert V2: MCP tools failed: {e}")

adk_expert = Agent(
    name="adk_architecture_expert",
    model=_cfg.agent_settings.expert_model,
    instruction=ADK_EXPERT_PROMPT,
    tools=_tools,
    planner=PlanReActPlanner(),
    output_key="adk_review_result",
    generate_content_config=_cfg.safety_config,
)
