"""
GitHub REST API fallback tool.

Used when the GitHub MCP server (npx @modelcontextprotocol/server-github) is
unavailable (e.g. Node.js not installed). Provides basic read-only access to
GitHub repositories using the REST v3 API via the requests library.
"""

import os
import base64
from typing import Optional
import requests

_GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
if _GITHUB_TOKEN:
    _HEADERS["Authorization"] = f"Bearer {_GITHUB_TOKEN}"


def github_get_file_contents(
    owner: str,
    repo: str,
    path: str,
    ref: str = "HEAD",
) -> dict:
    """Fetch the contents of a single file from a GitHub repository.

    Args:
        owner: The GitHub organisation or username (e.g. "google").
        repo: The repository name (e.g. "adk-samples").
        path: The file path inside the repository (e.g. "agents/hello/agent.py").
        ref: The branch, tag, or commit SHA to read from. Defaults to "HEAD".

    Returns:
        A dict with keys:
          - "content": decoded file content as a string, or an error message.
          - "path": the requested path.
          - "status": "ok" or "error".
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    try:
        resp = requests.get(url, headers=_HEADERS, params={"ref": ref}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("encoding") == "base64":
            content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        else:
            content = data.get("content", "")
        return {"status": "ok", "path": path, "content": content}
    except requests.HTTPError as e:
        return {"status": "error", "path": path, "content": f"HTTP {e.response.status_code}: {e}"}
    except Exception as e:
        return {"status": "error", "path": path, "content": str(e)}


def github_list_directory_contents(
    owner: str,
    repo: str,
    path: str = "",
    ref: str = "HEAD",
) -> dict:
    """List files and directories at a path within a GitHub repository.

    Args:
        owner: The GitHub organisation or username (e.g. "google").
        repo: The repository name (e.g. "adk-samples").
        path: Directory path inside the repo. Empty string means the root.
        ref: The branch, tag, or commit SHA to read from. Defaults to "HEAD".

    Returns:
        A dict with keys:
          - "entries": list of {"name": str, "type": "file"|"dir", "path": str}
          - "status": "ok" or "error".
          - "message": error message if status is "error".
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    try:
        resp = requests.get(url, headers=_HEADERS, params={"ref": ref}, timeout=15)
        resp.raise_for_status()
        items = resp.json()
        if not isinstance(items, list):
            # Single file returned — not a directory
            return {"status": "ok", "entries": [{"name": items["name"], "type": "file", "path": items["path"]}]}
        entries = [
            {"name": i["name"], "type": "dir" if i["type"] == "dir" else "file", "path": i["path"]}
            for i in items
        ]
        return {"status": "ok", "entries": entries}
    except requests.HTTPError as e:
        return {"status": "error", "entries": [], "message": f"HTTP {e.response.status_code}: {e}"}
    except Exception as e:
        return {"status": "error", "entries": [], "message": str(e)}
