"""
File upload / paste tool for local code ingestion.
Used when the user provides a local file path or pastes code directly.
"""

import os
import zipfile
import tempfile
from pathlib import Path

# File extensions we care about for code review
CODE_EXTENSIONS = {
    ".py", ".ts", ".js", ".go", ".java",
    ".yaml", ".yml", ".toml", ".json",
    ".md", ".txt", ".env.example", ".dockerfile",
    ".tf",  # Terraform
}

MAX_FILE_SIZE_BYTES = 500_000  # 500 KB per file


def parse_uploaded_files(file_paths: list) -> dict:
    """
    Reads and consolidates source code from a list of local file paths or a ZIP archive.

    Accepts individual .py/.ts/.js files or a path to a .zip archive containing
    a project. Binary files, node_modules, __pycache__, and .git directories are
    automatically skipped.

    Args:
        file_paths: A list of absolute or relative file system paths. Can include:
                    - Individual source files (e.g. ["/tmp/agent.py"])
                    - A ZIP archive path (e.g. ["/tmp/my_project.zip"])

    Returns:
        A dict with:
          - "status": "success" or "error"
          - "codebase": Formatted string with directory structure + file contents.
          - "file_count": Number of files successfully read.
          - "skipped": List of skipped files and reasons.
    """
    if not file_paths:
        return {
            "status": "error",
            "codebase": "",
            "file_count": 0,
            "skipped": ["No file paths provided."],
        }

    collected_files: dict[str, str] = {}
    skipped: list[str] = []
    temp_dirs: list[str] = []

    try:
        for path_str in file_paths:
            path = Path(path_str)

            if not path.exists():
                skipped.append(f"{path_str}: File not found")
                continue

            if path.suffix.lower() == ".zip":
                # Extract zip to temp dir
                tmp = tempfile.mkdtemp()
                temp_dirs.append(tmp)
                with zipfile.ZipFile(path, "r") as zf:
                    zf.extractall(tmp)
                _collect_from_directory(Path(tmp), collected_files, skipped)
            elif path.is_dir():
                _collect_from_directory(path, collected_files, skipped)
            else:
                _read_single_file(path, str(path), collected_files, skipped)

        if not collected_files:
            return {
                "status": "error",
                "codebase": "No readable source files found.",
                "file_count": 0,
                "skipped": skipped,
            }

        # Format output
        lines = ["=== UPLOADED FILES ===\n"]
        lines.append("=== DIRECTORY STRUCTURE ===")
        for fname in sorted(collected_files.keys()):
            lines.append(f"  {fname}")
        lines.append("\n=== FILE CONTENTS ===")
        for fname, content in sorted(collected_files.items()):
            lines.append(f"\n--- {fname} ---")
            lines.append(content)

        return {
            "status": "success",
            "codebase": "\n".join(lines),
            "file_count": len(collected_files),
            "skipped": skipped,
        }
    except Exception as e:
        return {
            "status": "error",
            "codebase": f"Error processing files: {str(e)}",
            "file_count": 0,
            "skipped": skipped,
        }


def _collect_from_directory(root: Path, collected: dict, skipped: list) -> None:
    """Recursively walks a directory and collects source files."""
    SKIP_DIRS = {
        "node_modules", "__pycache__", ".git", ".venv", "venv",
        ".mypy_cache", ".pytest_cache", "dist", "build", ".next",
    }
    for item in root.rglob("*"):
        if item.is_dir():
            continue
        # Skip directories in path
        if any(part in SKIP_DIRS for part in item.parts):
            continue
        rel_path = str(item.relative_to(root))
        _read_single_file(item, rel_path, collected, skipped)


def _read_single_file(path: Path, display_name: str, collected: dict, skipped: list) -> None:
    """Reads a single file and adds to collected dict."""
    if path.suffix.lower() not in CODE_EXTENSIONS and path.name not in {
        "Dockerfile", "Makefile", ".gitignore",
    }:
        skipped.append(f"{display_name}: non-code extension skipped")
        return

    if path.stat().st_size > MAX_FILE_SIZE_BYTES:
        skipped.append(f"{display_name}: file too large (>{MAX_FILE_SIZE_BYTES // 1024}KB)")
        return

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        collected[display_name] = content
    except Exception as e:
        skipped.append(f"{display_name}: read error — {e}")
