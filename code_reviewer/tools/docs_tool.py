"""
ADK Docs search tool using the adk-docs MCP server.
This module provides a standalone function tool for searching Google ADK documentation,
which is provided directly to the adk_expert agent as a regular function tool
(wrapping the HTTP fetch of the ADK docs site).
"""

import requests


def search_adk_docs(query: str) -> dict:
    """
    Searches the Google ADK documentation for information related to the query.

    Uses the public ADK documentation site to fetch relevant content.
    This tool should be used to verify current ADK APIs, patterns, and best practices.

    Args:
        query: A natural language query about ADK APIs, patterns, or best practices.
               Example: "how to use output_key in LlmAgent"

    Returns:
        A dict with:
          - "status": "success" or "error"
          - "results": A string containing relevant documentation excerpts.
          - "source_url": The URL that was fetched.
    """
    # Map common query topics to the most relevant ADK docs pages
    topic_map = {
        "sequential": "https://google.github.io/adk-docs/agents/workflow-agents/sequential-agents/index.md",
        "parallel": "https://google.github.io/adk-docs/agents/workflow-agents/parallel-agents/index.md",
        "loop": "https://google.github.io/adk-docs/agents/workflow-agents/loop-agents/index.md",
        "llmagent": "https://google.github.io/adk-docs/agents/llm-agents/index.md",
        "agent": "https://google.github.io/adk-docs/agents/llm-agents/index.md",
        "tool": "https://google.github.io/adk-docs/tools-custom/function-tools/index.md",
        "mcp": "https://google.github.io/adk-docs/tools-custom/mcp-tools/index.md",
        "state": "https://google.github.io/adk-docs/sessions/state/index.md",
        "session": "https://google.github.io/adk-docs/sessions/session/index.md",
        "multi": "https://google.github.io/adk-docs/agents/multi-agents/index.md",
        "deploy": "https://google.github.io/adk-docs/deploy/agent-engine/deploy/index.md",
        "callback": "https://google.github.io/adk-docs/callbacks/index.md",
        "output_key": "https://google.github.io/adk-docs/agents/multi-agents/index.md",
        "agenttool": "https://google.github.io/adk-docs/agents/multi-agents/index.md",
    }

    query_lower = query.lower()
    url = "https://google.github.io/adk-docs/agents/index.md"  # default
    for keyword, doc_url in topic_map.items():
        if keyword in query_lower:
            url = doc_url
            break

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        content = response.text

        # Trim to a reasonable size (first 8000 chars) to avoid context bloat
        trimmed = content[:8000] if len(content) > 8000 else content

        return {
            "status": "success",
            "results": trimmed,
            "source_url": url,
            "query": query,
        }
    except requests.RequestException as e:
        return {
            "status": "error",
            "results": f"Failed to fetch ADK documentation: {str(e)}",
            "source_url": url,
            "query": query,
        }
