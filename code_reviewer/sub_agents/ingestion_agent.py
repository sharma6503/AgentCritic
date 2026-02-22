"""Ingestion Agent — uses fast model for quick routing/extraction."""

import os
import logging
from google.adk import Agent
from ..config import Config
from ..prompts import INGESTION_PROMPT
from ..tools import (
    parse_uploaded_files,
    github_get_file_contents,
    github_list_directory_contents,
)
from ..utils.compat import get_binary_path, SafeMcpToolset

logger = logging.getLogger(__name__)
_cfg = Config()

_tools = [
    parse_uploaded_files,
    github_get_file_contents,
    github_list_directory_contents,
]

_uv_path = get_binary_path("uv")
_npx_path = get_binary_path("npx")

_bb_user = os.environ.get("BITBUCKET_USERNAME", "")
_bb_pass = os.environ.get("BITBUCKET_APP_PASSWORD", "")

if _uv_path or _npx_path:
    try:
        from google.adk.tools.mcp_tool import McpToolset
        from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
        from mcp import StdioServerParameters

        _command = "uvx" if _uv_path else "npx"
        _gh_args = ["--from", "@modelcontextprotocol/server-github", "github-mcp-server"] if _uv_path else ["-y", "@modelcontextprotocol/server-github"]
        _bb_args = ["--from", "@modelcontextprotocol/server-atlassian", "atlassian-mcp-server"] if _uv_path else ["-y", "@modelcontextprotocol/server-atlassian"]

        _github_token = os.environ.get("GITHUB_TOKEN", "")
        _github_env = {"GITHUB_PERSONAL_ACCESS_TOKEN": _github_token} if _github_token else {}

        _github_mcp = SafeMcpToolset(McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=_command,
                    args=_gh_args,
                    env=_github_env if _github_env else None,
                ),
            ),
            tool_filter=["get_file_contents", "list_directory_contents", "search_repositories"],
        ))

        if _bb_user and _bb_pass:
            _atlassian_mcp = SafeMcpToolset(McpToolset(
                connection_params=StdioConnectionParams(
                    server_params=StdioServerParameters(
                        command=_command,
                        args=_bb_args,
                        env={"BITBUCKET_USERNAME": _bb_user, "BITBUCKET_APP_PASSWORD": _bb_pass},
                    ),
                ),
            ))
            _tools.append(_atlassian_mcp)

        _tools.append(_github_mcp)
        logger.info(f"Loaded MCP tools ({_command} + REST fallback).")

    except Exception as e:
        logger.debug(f"MCP init skipped: {e}")
else:
    logger.info("MCP binaries not found. Using REST fallbacks only.")

ingestion_agent = Agent(
    name="ingestion_agent",
    model=_cfg.agent_settings.expert_model,
    description="Fetches code from GitHub, Bitbucket, or local sources.",
    instruction=INGESTION_PROMPT,
    tools=_tools,
    output_key="raw_codebase",
    generate_content_config=_cfg.safety_config,
)
