"""Ingestion Agent — uses fast model for quick routing/extraction."""

import os
import logging
from google.adk import Agent
from google.adk.planners.plan_re_act_planner import PlanReActPlanner
from google.adk.agents.callback_context import CallbackContext
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



def split_codebase_callback(callback_context: CallbackContext):
    """
    Performance Optimization: Splits raw_codebase into domain-specific keys
    after ingestion is complete. This implements a Divide & Conquer pattern
    to reduce context size for expert agents.
    """
    keys = list(callback_context.state.keys()) if isinstance(callback_context.state, dict) else list(callback_context.state.to_dict().keys())
    logger.info(f"split_codebase_callback entering. State keys: {keys}")
    raw = callback_context.state.get("raw_codebase", "")
    
    # === OPTIMIZATION: Bypassing LLM Truncation ===
    # For large codebases, the LLM will hit MAX_TOKENS and fail to echo the full string.
    # To fix this, we directly extract the parsed codebase from the ToolResponse history!
    extracted_raw = None
    if hasattr(callback_context, "history") and callback_context.history:
        for msg in reversed(callback_context.history):
            if not getattr(msg, "parts", None): continue
            for part in msg.parts:
                part_name = getattr(getattr(part, "function_response", None), "name", "")
                if part_name == "parse_uploaded_files":
                    try:
                        resp = part.function_response.response
                        if isinstance(resp, dict):
                            extracted_raw = resp.get("codebase", "")
                            if extracted_raw: break
                    except Exception: pass
            if extracted_raw: break

    # If we extracted the full text directly from the tool, it overrides the LLM's (potentially truncated/empty) output
    if extracted_raw:
        logger.info(f"Successfully bypassed LLM output: extracted {len(extracted_raw)} chars directly from ToolResponse!")
        raw = extracted_raw

    if not isinstance(raw, str) or not raw:
        logger.warning("raw_codebase not found in state or tool history during callback!")
        return

    # Parse collected files into logic, config, docs
    logic_files = {}  # fname -> content_block
    config_parts = []
    docs_parts = []
    
    lines = raw.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("--- ") and line.endswith(" ---"):
            fname = line.strip("- ")
            ext = os.path.splitext(fname)[1].lower()
            content_buf = []
            i += 1
            while i < len(lines) and not (lines[i].startswith("--- ") and lines[i].endswith(" ---")):
                content_buf.append(lines[i])
                i += 1
            
            file_block = f"\n--- {fname} ---\n" + "\n".join(content_buf)
            
            if ext in {".py", ".ts", ".js", ".go", ".java"}: 
                logic_files[fname] = file_block
            elif ext in {".yaml", ".yml", ".toml", ".json", ".env.example"}: 
                config_parts.append(file_block)
            elif ext in {".md", ".txt"}: 
                docs_parts.append(file_block)
            continue
        i += 1

    # =========================================================================
    # OPTIMIZATION: Dependency-Aware Topological Sort (Kahn's Algorithm)
    # Strategy: Parse AST of Python files to find imports. Build a directed 
    # graph where A -> B means "A imports B" (A depends on B). Sort so B comes 
    # before A in the context. This gives the LLM foundational context first.
    # =========================================================================
    import ast
    from collections import defaultdict, deque

    graph = defaultdict(list)
    in_degree = defaultdict(int)
    py_files = {f: c for f, c in logic_files.items() if f.endswith('.py')}
    
    # 1. Map files to module namespaces (e.g., 'src/api.py' -> 'src.api')
    module_to_file = {}
    for fname in py_files:
        mod_name = fname.replace("\\", "/").replace(".py", "").replace("/", ".")
        module_to_file[mod_name] = fname
        if mod_name.endswith(".__init__"):
            module_to_file[mod_name[:-9]] = fname

    def _resolve_import(module: str, level: int, current_fname: str) -> str | None:
        if level == 0:
            return module_to_file.get(module)
        parts = current_fname.replace("\\", "/").split("/")
        parts.pop() # remove file name
        for _ in range(level - 1):
            if parts: parts.pop()
            else: return None
        base_mod = ".".join(parts)
        full_mod = f"{base_mod}.{module}" if base_mod and module else base_mod or module
        return module_to_file.get(full_mod)

    # 2. Extract AST imports
    for fname, block in py_files.items():
        in_degree[fname] += 0 # Ensure node exists in degree map
        source = block.split(f"--- {fname} ---")[1] if f"--- {fname} ---" in block else block
        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dep_fname = _resolve_import(alias.name.split('.')[0], 0, fname)
                        if dep_fname and dep_fname != fname and fname not in graph[dep_fname]:
                            graph[dep_fname].append(fname)
                            in_degree[fname] += 1
                elif isinstance(node, ast.ImportFrom):
                    level = node.level
                    module = node.module or ""
                    dep_fname = _resolve_import(module, level, fname)
                    
                    if not dep_fname and node.names:
                       for alias in node.names:
                           sub_mod = f"{module}.{alias.name}" if module else alias.name
                           dep_fname_sub = _resolve_import(sub_mod, level, fname)
                           if dep_fname_sub and dep_fname_sub != fname and fname not in graph[dep_fname_sub]:
                                graph[dep_fname_sub].append(fname)
                                in_degree[fname] += 1
                                
                    if dep_fname and dep_fname != fname and fname not in graph[dep_fname]:
                        graph[dep_fname].append(fname)
                        in_degree[fname] += 1
        except SyntaxError:
            pass # Ignore unparseable code snippets

    # 3. Kahn's Algorithm with Cycle Resolution
    sorted_py_files = []
    queue = deque([f for f in py_files if in_degree[f] == 0])

    while queue:
        curr = queue.popleft()
        sorted_py_files.append(curr)
        for dependent in graph[curr]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    cyclic_files = [f for f in py_files if in_degree[f] > 0]
    while cyclic_files:
        target = min(cyclic_files, key=lambda f: in_degree[f])
        in_degree[target] = 0
        queue.append(target)
        
        while queue:
            curr = queue.popleft()
            sorted_py_files.append(curr)
            for dependent in graph[curr]:
                if in_degree[dependent] > 0:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)
        cyclic_files = [f for f in py_files if in_degree[f] > 0]

    # Combine sorted Python files with other logic files (TS, JS, etc.)
    final_logic_parts = [logic_files[f] for f in sorted_py_files]
    # Add non-Python logic files
    final_logic_parts.extend([block for f, block in logic_files.items() if not f.endswith('.py')])

    callback_context.state["code_logic"] = "\n".join(final_logic_parts) if final_logic_parts else raw
    callback_context.state["code_config"] = "\n".join(config_parts) if config_parts else ""
    callback_context.state["code_docs"] = "\n".join(docs_parts) if docs_parts else ""
    logger.info(f"Optimization: Split codebase into logic ({len(final_logic_parts)} sorted), config ({len(config_parts)}), docs ({len(docs_parts)})")

ingestion_agent = Agent(
    name="ingestion_agent",
    model=_cfg.agent_settings.expert_model,
    description="Fetches code from GitHub, Bitbucket, or local sources.",
    instruction=INGESTION_PROMPT,
    tools=_tools,
    planner=PlanReActPlanner(),
    output_key="raw_codebase",
    after_agent_callback=split_codebase_callback,
    generate_content_config=_cfg.safety_config,
)
