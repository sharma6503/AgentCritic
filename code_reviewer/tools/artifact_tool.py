"""
artifact_tool.py — Reads files uploaded via ADK web UI from artifact storage.

When a user uploads a file through the ADK web interface, the file is stored as
an ADK artifact (not a regular file system path). This tool loads the artifact
bytes from the ADK artifact service and processes the content appropriately.
"""
import json
import logging
from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)


def _preprocess_ipynb(raw_json: str) -> str:
    """Extracts code and markdown cells from a Jupyter Notebook JSON string."""
    try:
        nb = json.loads(raw_json)
        cells = nb.get("cells", [])
        blocks = []
        for cell in cells:
            ctype = cell.get("cell_type")
            source = "".join(cell.get("source", []))
            if not source.strip():
                continue
            if ctype == "code":
                blocks.append(f"```python\n{source}\n```")
            elif ctype == "markdown":
                blocks.append(source)
        result = "\n\n".join(blocks)
        if not result:
            return raw_json  # Fallback: couldn't extract anything meaningful
        return result
    except Exception:
        return raw_json  # Fallback to raw on any parse error


async def read_artifact_file(filename: str, tool_context: ToolContext) -> dict:
    """
    Reads a file uploaded via the ADK web UI from artifact storage.
    
    This tool should be used when the user has uploaded a file (e.g. a .py, .zip,
    or .ipynb file) directly through the chat interface. ADK stores uploaded files
    as artifacts identified by their filename.

    Args:
        filename: The name of the uploaded file (e.g. "Text_Summarization.ipynb").

    Returns:
        A dict with:
          - "status": "success" or "error"
          - "codebase": Formatted string with file contents ready for review.
          - "file_count": Number of files successfully read.
          - "message": Human-readable status message.
    """
    if not filename:
        return {"status": "error", "codebase": "", "file_count": 0, "message": "No filename provided."}

    try:
        artifact = await tool_context.load_artifact(filename=filename)
    except Exception as e:
        logger.warning(f"read_artifact_file: Failed to load artifact '{filename}': {e}")
        return {
            "status": "error",
            "codebase": "",
            "file_count": 0,
            "message": f"Could not load artifact '{filename}': {e}",
        }

    if artifact is None:
        return {
            "status": "error",
            "codebase": "",
            "file_count": 0,
            "message": f"Artifact '{filename}' not found in session storage.",
        }

    # Decode bytes from the artifact Part
    try:
        raw_bytes = artifact.inline_data.data
        raw_text = raw_bytes.decode("utf-8", errors="replace")
    except Exception as e:
        logger.warning(f"read_artifact_file: Failed to decode artifact bytes: {e}")
        return {
            "status": "error",
            "codebase": "",
            "file_count": 0,
            "message": f"Failed to decode file content: {e}",
        }

    # Process based on file type
    lower_name = filename.lower()
    if lower_name.endswith(".ipynb"):
        content = _preprocess_ipynb(raw_text)
        label = "Jupyter Notebook"
    else:
        content = raw_text
        label = "Source File"

    if not content.strip():
        return {
            "status": "error",
            "codebase": "",
            "file_count": 0,
            "message": f"The file '{filename}' appears to be empty after processing.",
        }

    codebase = (
        f"=== DIRECTORY STRUCTURE ===\n"
        f"  [LOGIC]\n"
        f"    {filename}\n\n"
        f"=== FILE CONTENTS ===\n\n"
        f"--- {filename} ---\n"
        f"{content}\n"
    )

    logger.info(f"read_artifact_file: Successfully loaded '{filename}' ({label}, {len(content)} chars)")
    return {
        "status": "success",
        "codebase": codebase,
        "file_count": 1,
        "message": f"Successfully read '{filename}' ({label}, {len(content)} chars).",
    }
