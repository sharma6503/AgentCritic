"""
GitHub REST API fallback tool.

Used when the GitHub MCP server (npx @modelcontextprotocol/server-github) is
unavailable (e.g. Node.js not installed). Provides basic read-only access to
GitHub repositories using the REST v3 API via the requests library.
"""

import os
import base64
import httpx
import logging

logger = logging.getLogger(__name__)

_GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
if _GITHUB_TOKEN:
    _HEADERS["Authorization"] = f"Bearer {_GITHUB_TOKEN}"

async def github_get_file_contents(
    owner: str,
    repo: str,
    path: str,
    ref: str = "HEAD",
) -> dict:
    """Fetch the contents of a single file from a GitHub repository (Async).

    Args:
        owner: The GitHub organisation or username (e.g. "google").
        repo: The repository name (e.g. "adk-samples").
        path: The file path inside the repository.
        ref: The branch, tag, commit. Defaults to "HEAD".

    Returns:
        A dict with keys: "content", "path", "status".
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True) as client:
        try:
            resp = await client.get(url, params={"ref": ref}, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            if data.get("encoding") == "base64":
                content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
            else:
                content = data.get("content", "")
            return {"status": "ok", "path": path, "content": content}
        except httpx.HTTPStatusError as e:
            return {"status": "error", "path": path, "content": f"HTTP {e.response.status_code}: {e}"}
        except Exception as e:
            return {"status": "error", "path": path, "content": str(e)}

async def github_list_directory_contents(
    owner: str,
    repo: str,
    path: str = "",
    ref: str = "HEAD",
) -> dict:
    """List files and directories at a path within a GitHub repository (Async).

    Args:
        owner: The GitHub organisation or username (e.g. "google").
        repo: The repository name.
        path: Directory path. Empty means root.
        ref: The branch, tag, commit. Defaults to "HEAD".

    Returns:
        A dict with keys: "entries", "status", "message".
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True) as client:
        try:
            resp = await client.get(url, params={"ref": ref}, timeout=15)
            resp.raise_for_status()
            items = resp.json()
            if not isinstance(items, list):
                return {"status": "ok", "entries": [{"name": items["name"], "type": "file", "path": items["path"]}]}
            entries = [
                {"name": i["name"], "type": "dir" if i["type"] == "dir" else "file", "path": i["path"]}
                for i in items
            ]
            return {"status": "ok", "entries": entries}
        except httpx.HTTPStatusError as e:
            return {"status": "error", "entries": [], "message": f"HTTP {e.response.status_code}: {e}"}
        except Exception as e:
            return {"status": "error", "entries": [], "message": str(e)}
