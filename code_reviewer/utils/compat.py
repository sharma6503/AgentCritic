"""
Compatibility and Platform Utilities

Centralises platform-specific setup and provides a SafeMcpToolset wrapper
to prevent adk web startup crashes on Windows due to event loop conflicts.
"""

import asyncio
import sys
import shutil
import logging
from typing import Any, List

logger = logging.getLogger(__name__)

# Try to import ADK types for the wrapper, but keep it optional for pure-compat use
try:
    from google.adk.tools.mcp_tool import McpToolset
    from google.adk.tools.base_toolset import BaseToolset
    _ADK_AVAILABLE = True
except ImportError:
    McpToolset = object
    BaseToolset = object
    _ADK_AVAILABLE = False

def setup_platform_compat():
    """Perform any required platform-specific setup for asyncio/subprocesses."""
    if sys.platform == "win32":
        try:
            # Uvicorn/ADK Web often use SelectorEventLoop which doesn't support 
            # subprocesses on Windows. ProactorEventLoop is required for MCP.
            policy = asyncio.get_event_loop_policy()
            if not isinstance(policy, asyncio.WindowsProactorEventLoopPolicy):
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                logger.info("Windows detected: Set ProactorEventLoopPolicy for MCP/subprocess support.")
        except Exception as e:
            logger.warning(f"Could not set Windows ProactorEventLoopPolicy: {e}")

def get_binary_path(name: str) -> str | None:
    """Check for existence of a binary (uvx, npx, node) in the system path."""
    return shutil.which(name)

if _ADK_AVAILABLE:
    class SafeMcpToolset(BaseToolset):
        """
        A wrapper for McpToolset that catches ConnectionErrors during 
        discovery (canonical_tools) and execution.
        
        Prevents 'adk web' from crashing on Windows when the MCP subprocess
        fails to connect due to event loop or environment issues.
        """
        def __init__(self, toolset: McpToolset):
            self._toolset = toolset
            # Delegate common attributes
            self.connection_params = getattr(toolset, "connection_params", None)

        async def get_tools(self, context: Any) -> List[Any]:
            try:
                return await self._toolset.get_tools(context)
            except Exception as e:
                # Log as info so the user/developer can see why tools are missing on Windows
                logger.info(f"SafeMcpToolset: Could not load tools from {self._toolset.connection_params.server_params.command}. Error: {e}")
                return []

        async def get_tools_with_prefix(self, context: Any) -> List[Any]:
            try:
                return await self._toolset.get_tools_with_prefix(context)
            except Exception as e:
                logger.debug(f"SafeMcpToolset connection skipped (prefix): {e}")
                return []
else:
    class SafeMcpToolset:
        def __init__(self, toolset: Any):
            pass
        async def get_tools(self, context: Any):
            return []
        async def get_tools_with_prefix(self, context: Any):
            return []
