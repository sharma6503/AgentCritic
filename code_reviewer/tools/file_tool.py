import os
import zipfile
import tempfile
import concurrent.futures
import shutil
from pathlib import Path
from google.adk.tools.tool_context import ToolContext

# File extensions we care about for code review
CODE_EXTENSIONS = {
    ".py", ".ts", ".js", ".go", ".java", ".cpp", ".c", ".h", ".hpp",
    ".cs", ".rs", ".rb", ".php", ".swift", ".kt", ".kts", ".m", ".scala",
    ".yaml", ".yml", ".toml", ".json", ".xml",
    ".html", ".css", ".scss", ".sass", ".less",
    ".md", ".txt", ".env.example", ".dockerfile",
    ".tf", ".sh", ".bash", ".zsh",
}

MAX_FILE_SIZE_BYTES = 500_000  # 500 KB per file
MAX_WORKERS = 8

SKIP_DIRS = {"node_modules", "__pycache__", ".git", ".venv", "venv", ".next", "dist", "build"}


def parse_uploaded_files(file_paths: list, tool_context: ToolContext = None) -> dict:
    """
    Reads and consolidates source code from a list of local file paths or a ZIP archive.
    Uses ThreadPoolExecutor for parallel I/O to optimize multi-file ingestion.
    ZIP files are processed entirely in-memory as streams, but also physically 
    extracted to a session-specific ADK artifact directory if possible.

    Returns:
        A dict with:
          - "status": "success" or "error"
          - "codebase": Formatted string with directory structure + file contents.
          - "summary": List of files found by category (logic, config, docs).
          - "file_count": Number of files successfully read.
    """
    if not file_paths:
        return {"status": "error", "codebase": "", "file_count": 0, "skipped": ["No file paths provided."]}

    collected_files: dict[str, str] = {}
    skipped: list[str] = []
    
    # Each task is a tuple: (callable, (args...), display_name)
    all_eligible_tasks: list[tuple] = []

    try:
        for path_str in file_paths:
            path = Path(path_str)
            if not path.exists():
                skipped.append(f"{path_str}: Not found")
                continue

            if path.suffix.lower() == ".zip":
                # Extract physically for expert agents to use
                if tool_context and getattr(tool_context, 'session_id', None):
                    # We create the physical directory at .adk/artifacts/{session_id}/source
                    artifact_dir = Path.cwd() / ".adk" / "artifacts" / tool_context.session_id / "source"
                    artifact_dir.mkdir(parents=True, exist_ok=True)
                    _unzip_to_target(path, artifact_dir, skipped)
                    # Pass the directory path into the state so experts know where it is
                    tool_context.state["source_artifact_path"] = str(artifact_dir.absolute())

                try:
                    with zipfile.ZipFile(path, "r") as zf:
                        for name in zf.namelist():
                            if name.endswith('/'): 
                                continue # Skip directories
                                
                            parts = Path(name).parts
                            if any(part in SKIP_DIRS for part in parts):
                                continue
                                
                            ext = Path(name).suffix.lower()
                            if ext not in CODE_EXTENSIONS and Path(name).name not in {"Dockerfile", "Makefile"}:
                                continue
                                
                            info = zf.getinfo(name)
                            if info.file_size > MAX_FILE_SIZE_BYTES:
                                skipped.append(f"{name}: too large")
                                continue
                                
                            all_eligible_tasks.append((_read_zip_member_safe, (path, name), name))
                except zipfile.BadZipFile:
                    skipped.append(f"{path_str}: Bad ZIP file")
            elif path.is_dir():
                _gather_paths(path, all_eligible_tasks, skipped)
            else:
                _gather_paths(path, all_eligible_tasks, skipped, single_file=True)

        if not all_eligible_tasks:
            return {"status": "error", "codebase": "No readable source files found.", "file_count": 0}

        # Parallel Read
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_name = {
                executor.submit(func, *args): name 
                for func, args, name in all_eligible_tasks
            }
            for future in concurrent.futures.as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    content = future.result()
                    if content:
                        collected_files[name] = content
                except Exception as e:
                    skipped.append(f"{name}: Read error - {e}")

        # Organize by category for experts
        categories = {"logic": [], "config": [], "docs": [], "other": []}
        for fname in collected_files.keys():
            ext = Path(fname).suffix.lower()
            if ext in {".py", ".ts", ".js", ".go", ".java"}: categories["logic"].append(fname)
            elif ext in {".yaml", ".yml", ".toml", ".json", ".env.example"}: categories["config"].append(fname)
            elif ext in {".md", ".txt"}: categories["docs"].append(fname)
            else: categories["other"].append(fname)

        # Format output
        lines = ["=== DIRECTORY STRUCTURE ==="]
        for cat, files in categories.items():
            if files:
                lines.append(f"  [{cat.upper()}]")
                for f in sorted(files): lines.append(f"    {f}")
        
        lines.append("\n=== FILE CONTENTS ===")
        for fname, content in sorted(collected_files.items()):
            ext = Path(fname).suffix.lstrip('.') or ""
            # Map common extensions to markdown languages
            lang_map = {"py": "python", "js": "javascript", "ts": "typescript", "yml": "yaml", "yaml": "yaml"}
            lang = lang_map.get(ext.lower(), ext.lower())
            
            lines.append(f"\n--- {fname} ---\n```{lang}\n{content}\n```")

        return {
            "status": "success",
            "codebase": "\n".join(lines),
            "summary": categories,
            "file_count": len(collected_files),
            "skipped": skipped,
        }
    except Exception as e:
        return {"status": "error", "codebase": f"Processing error: {e}", "file_count": 0}


def _gather_paths(root: Path, task_list: list, skipped: list, single_file=False) -> None:
    def is_eligible(p: Path):
        if p.suffix.lower() not in CODE_EXTENSIONS and p.name not in {"Dockerfile", "Makefile"}:
            return False
        if p.stat().st_size > MAX_FILE_SIZE_BYTES:
            skipped.append(f"{p.name}: too large")
            return False
        return True

    if single_file:
        if is_eligible(root): task_list.append((_read_file_safe, (root,), root.name))
        return

    for item in root.rglob("*"):
        if item.is_file() and not any(part in SKIP_DIRS for part in item.parts) and is_eligible(item):
            task_list.append((_read_file_safe, (item,), str(item.relative_to(root))))


def _read_file_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except:
        return ""


def _read_zip_member_safe(zip_path: Path, member_name: str) -> str:
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            with zf.open(member_name) as f:
                # Read at most MAX_FILE_SIZE_BYTES + 1 to prevent zip bombs
                data = f.read(MAX_FILE_SIZE_BYTES + 1)
                if len(data) > MAX_FILE_SIZE_BYTES:
                    return "" # Omit if it sneakily exceeded the size somehow
                return data.decode("utf-8", errors="replace")
    except Exception:
        return ""


def _unzip_to_target(zip_path: Path, target_dir: Path, skipped: list):
    """Physically extracts eligible code files from a ZIP archive to a given target directory in parallel."""
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            extract_tasks = []
            for name in zf.namelist():
                if name.endswith('/'): continue
                
                parts = Path(name).parts
                if any(part in SKIP_DIRS for part in parts): continue
                
                ext = Path(name).suffix.lower()
                if ext not in CODE_EXTENSIONS and Path(name).name not in {"Dockerfile", "Makefile"}:
                    continue
                    
                info = zf.getinfo(name)
                if info.file_size > MAX_FILE_SIZE_BYTES:
                    skipped.append(f"{name}: too large to extract to physical artifact")
                    continue
                    
                extract_tasks.append(name)
                
            def _extract_member(member_name):
                try:
                    target_path = target_dir / member_name
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    # Open a fresh handle for the thread to prevent ZipFile concurrency locks
                    with zipfile.ZipFile(zip_path, "r") as thread_zf:
                        with thread_zf.open(member_name) as source_file:
                            with open(target_path, "wb") as output_file:
                                shutil.copyfileobj(source_file, output_file)
                except Exception as e:
                    return f"{member_name}: error extracting - {e}"
                return None
                
            if extract_tasks:
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    futures = {executor.submit(_extract_member, name): name for name in extract_tasks}
                    for future in concurrent.futures.as_completed(futures):
                        err = future.result()
                        if err:
                            skipped.append(err)
    except Exception as e:
        skipped.append(f"Failed to unzip {zip_path.name}: {e}")

