"""
ADK Architecture & Model Lifecycle Expert Agent.

Equipped with three knowledge sources:
  1. ADK Docs MCP (mcpdoc) — live ADK documentation via fetch_docs / list_doc_sources
  2. Google Developer Knowledge MCP — searches Google developer docs for model lifecycle info
  3. lifecycle_tool — scrapes the live Vertex AI model retirement page for real-time data
"""

import logging
from google.adk import Agent
from google.adk.planners.plan_re_act_planner import PlanReActPlanner
from google.adk.agents.callback_context import CallbackContext
from ..config import Config
from ..prompts import ADK_EXPERT_PROMPT
from ..tools.lifecycle_tool import fetch_gemini_model_lifecycle
from ..utils.compat import get_binary_path, SafeMcpToolset

logger = logging.getLogger(__name__)

_cfg = Config()
_tools = [fetch_gemini_model_lifecycle]  # Always available — scrapes live retirement page


def adk_expert_callback(callback_context: CallbackContext):
    """Debug callback to verify expert output."""
    res = callback_context.state.get("adk_review_result", "")
    keys = list(callback_context.state.keys()) if isinstance(callback_context.state, dict) else list(callback_context.state.to_dict().keys())
    logger.info(f"ADK EXPERT CALLBACK: Output length: {len(res)}. State keys: {keys}")


# ---------------------------------------------------------------------------
# MCP Tools — require uvx / npx binary to be available
# ---------------------------------------------------------------------------
if get_binary_path("uv"):
    try:
        from google.adk.tools.mcp_tool import McpToolset
        from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
        from mcp import StdioServerParameters

        # 1. ADK Docs MCP — for live ADK API and pattern documentation
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
        logger.info("ADK Expert: ADK Docs MCP loaded (uvx mcpdoc).")

        # 2. Google Developer Knowledge MCP — for model lifecycle, deprecations, Cloud docs
        _google_knowledge_mcp = SafeMcpToolset(McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="uvx",
                    args=[
                        "--from", "google-developer-knowledge-mcp",
                        "google-developer-knowledge-mcp",
                    ],
                ),
            ),
            tool_filter=["search_documents", "get_documents"],
        ))
        _tools.append(_google_knowledge_mcp)
        logger.info("ADK Expert: Google Developer Knowledge MCP loaded.")

    except Exception as e:
        logger.warning(f"ADK Expert: MCP tools failed to load: {e}")
else:
    logger.info("ADK Expert: uv binary not found. Using lifecycle_tool only.")


adk_expert = Agent(
    name="adk_architecture_expert",
    model=_cfg.agent_settings.expert_model,
    description="Expert in Google ADK architecture patterns and Gemini model lifecycle.",
    instruction=ADK_EXPERT_PROMPT,
    tools=_tools,
    planner=PlanReActPlanner(),
    output_key="adk_review_result",
    after_agent_callback=adk_expert_callback,
    generate_content_config=_cfg.safety_config,
)
