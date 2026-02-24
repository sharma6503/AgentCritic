"""
ADK Code Reviewer — Main Agent Orchestration
=============================================

Architecture:
  root_agent (Agent)                        ← User-facing supervisor
    └── review_pipeline (SequentialAgent)
          ├── ingestion_agent               ← Fetches code via GitHub/Bitbucket MCP or file tool
          ├── review_fleet (ParallelAgent)  ← Runs all 4 reviewers concurrently
          │     ├── adk_expert              → state['adk_review_result']
          │     ├── quality_expert          → state['quality_review_result']
          │     ├── security_expert         → state['security_review_result']
          │     └── code_validator_agent    → state['validation_result']
          └── reporting_fleet (ParallelAgent)
                ├── synthesis_agent         ← Combines all 4 results → synthesis_result
                └── metrics_agent           ← Extracts JSON from report → review_metrics

Shared State Flow:
  user_request  ──────────────────────────────────► ingestion_agent
  raw_codebase  ──► [adk_expert, quality_expert, security_expert, code_validator] (parallel)
  review results ─────────────────────────────────► synthesis_agent → synthesis_result
  synthesis_result ───────────────────────────────► metrics_agent → review_metrics
  synthesis_result ───────────────────────────────► html_agent    → HTML output

Callbacks:
  - ingestion_agent: split_codebase_callback optimizes file context
  - metrics_agent: parses synthesis_result into JSON

MCP Servers:
  ingestion_agent: @modelcontextprotocol/server-github (npx)
  ingestion_agent: @modelcontextprotocol/server-atlassian (npx)
  adk_expert:      adk-docs-mcp (uvx mcpdoc)

Built-in Code Tools:
  code_validator_agent: BuiltInCodeExecutor (Gemini API sandbox)
  ⚠️  BuiltInCodeExecutor must be the ONLY tool on its agent (ADK limitation).
"""

import logging
from dotenv import load_dotenv

from google.adk.apps.app import App, ResumabilityConfig
from google.adk.agents.context_cache_config import ContextCacheConfig
from google.adk.plugins.logging_plugin import LoggingPlugin

from code_reviewer.utils.compat import setup_platform_compat

# ---------------------------------------------------------------------------
# Silence ADK-internal MCP connection ERRORs at the framework level.
# These originate from mcp_toolset.py BEFORE our SafeMcpToolset wrapper
# can intercept them. They are expected on Windows when MCP subprocesses
# can't connect; the SafeMcpToolset handles graceful fallback afterwards.
# ---------------------------------------------------------------------------
class _McpTimeoutFilter(logging.Filter):
    """Demotes noisy MCP-session timeout ERRORs to DEBUG."""
    _SUPPRESS = (
        "Exception during MCP session execution",
        "Failed to get tools from MCP server",
    )
    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno == logging.ERROR and any(s in record.getMessage() for s in self._SUPPRESS):
            record.levelno = logging.DEBUG
            record.levelname = "DEBUG"
        return True  # always keep (just downgrade)


_mcp_loggers = [
    logging.getLogger("google.adk.tools.mcp_tool.mcp_toolset"),
    logging.getLogger("google_adk.google.adk.tools.mcp_tool.mcp_toolset"),
]
for logger in _mcp_loggers:
    logger.addFilter(_McpTimeoutFilter())

# Best Practice: Perform platform-specific adjustments early and transparently
setup_platform_compat()

load_dotenv()  # Load .env before any agent/MCP initialisation


# Use the `Agent` shorthand (alias for LlmAgent) — same as all google/adk-samples
from google.adk import Agent  # noqa: E402
from google.adk.agents import SequentialAgent, ParallelAgent  # noqa: E402
from google.adk.agents.callback_context import CallbackContext  # noqa: E402
from google.adk.planners.plan_re_act_planner import PlanReActPlanner  # noqa: E402

from code_reviewer.config import Config  # noqa: E402
from code_reviewer.prompts import SUPERVISOR_PROMPT  # noqa: E402
from code_reviewer.sub_agents import (  # noqa: E402
    ingestion_agent,
    adk_expert,
    quality_expert,
    security_expert,
    code_validator_agent,
    synthesis_agent,
    metrics_agent,
    html_agent,
)

# Instantiate config — reads from env vars / .env
configs = Config()

# ---------------------------------------------------------------------------
# ADK Best Practice: Safety & Compliance Callback
# ---------------------------------------------------------------------------
def constitution_callback(callback_context: CallbackContext):
    """
    Enforces the 'Code Reviewer Constitution' by injecting it into the state.
    This ensures all agents stay grounded and compliant.
    """
    import os
    constitution_path = os.path.join(os.path.dirname(__file__), "knowledge_base", "constitution.md")
    try:
        if os.path.exists(constitution_path):
            with open(constitution_path, "r", encoding="utf-8") as f:
                callback_context.state["constitution"] = f.read()
                logger.debug("Constitution injected into state.")
    except Exception as e:
        logger.warning(f"Could not load constitution: {e}")

    # Mitigation for 429 RESOURCE_EXHAUSTED
    calls = callback_context.state.get("metadata_agent_calls", 0)
    callback_context.state["metadata_agent_calls"] = calls + 1
    if calls > 15:
        logger.warning(f"Session '{callback_context.session_id}' has exceeded 15 agent calls. Quota risk is high.")

    # Filter out ZIP file parts from history and current request to prevent Gemini 400 INVALID_ARGUMENT
    from google.genai import types
    
    def _filter_parts(parts):
        if not parts: return parts
        filtered = []
        for part in parts:
            mime_type = ""
            if getattr(part, "inline_data", None) and getattr(part.inline_data, "mime_type", None):
                mime_type = part.inline_data.mime_type
            elif getattr(part, "file_data", None) and getattr(part.file_data, "mime_type", None):
                mime_type = part.file_data.mime_type
            
            if "zip" in mime_type.lower() or "application/x-zip-compressed" in mime_type.lower():
                logger.info(f"Filtering unsupported ZIP part (MIME: {mime_type})")
                
                # Save the ZIP to disk so the agent can access it using the file tool
                zip_path_str = ""
                if getattr(part, "inline_data", None) and part.inline_data.data:
                    try:
                        import tempfile
                        from pathlib import Path
                        
                        data_bytes = part.inline_data.data
                        if isinstance(data_bytes, str):
                            import base64
                            data_bytes = base64.b64decode(data_bytes)
                            
                        # Save to project artifact directory
                        upload_dir = Path(".adk/artifacts/uploads")
                        upload_dir.mkdir(parents=True, exist_ok=True)
                        
                        tmp_file = tempfile.NamedTemporaryFile(dir=upload_dir, delete=False, suffix=".zip")
                        tmp_file.write(data_bytes)
                        tmp_file.close()
                        
                        zip_path_str = str(Path(tmp_file.name).absolute())
                        logger.info(f"Saved uploaded ZIP to temporary file: {zip_path_str}")
                    except Exception as e:
                        logger.error(f"Failed to save intercepted ZIP data: {e}")

                msg = "[System Note: User attached a ZIP file."
                if zip_path_str:
                    msg += f" It was temporarily preserved at `{zip_path_str}`. You must use the `parse_uploaded_files` tool with this exact path to extract and read it.]"
                else:
                    msg += " No valid data found or failed to save.]"
                
                filtered.append(types.Part.from_text(text=msg))
            else:
                filtered.append(part)
        return filtered

    # 1. Filter the invocation trigger content
    if hasattr(callback_context, "user_content") and callback_context.user_content:
        if getattr(callback_context.user_content, "parts", None):
            # Mutate the underlying invocation context directly
            callback_context._invocation_context.user_content.parts = _filter_parts(callback_context.user_content.parts)
    
    # 2. Filter session events (where the prompt history is built from)
    if hasattr(callback_context, "session") and getattr(callback_context.session, "events", None):
        for event in callback_context.session.events:
            if getattr(event, "content", None) and getattr(event.content, "parts", None):
                event.content.parts = _filter_parts(event.content.parts)
                
    # 3. Filter history just in case
    if hasattr(callback_context, "history") and callback_context.history:
        for msg in callback_context.history:
            if getattr(msg, "parts", None):
                msg.parts = _filter_parts(msg.parts)

# ---------------------------------------------------------------------------
# Step 1: The Review Fleet — four experts run concurrently
# ---------------------------------------------------------------------------
review_fleet = ParallelAgent(
    name="review_fleet",
    description=(
        "Concurrently runs ADK Architecture, Code Quality, Security, and "
        "Dynamic Code Validation experts on the ingested codebase."
    ),
    sub_agents=[
        adk_expert,             # → state['adk_review_result']
        quality_expert,         # → state['quality_review_result']
        security_expert,        # → state['security_review_result']
        code_validator_agent,   # → state['validation_result']
    ],
)

# ---------------------------------------------------------------------------
# Step 2: The Reporting Pipeline — draft → critique → revise
# ---------------------------------------------------------------------------
synthesis_pipeline = SequentialAgent(
    name="synthesis_pipeline",
    description="Synthesizes expert findings into a unified Markdown report.",
    sub_agents=[
        synthesis_agent,   # Generates unified Markdown report
    ],
)

# ---------------------------------------------------------------------------
# Step 3: The Reporting Fleet — concurrently synthesise report and extract metrics
# ---------------------------------------------------------------------------
reporting_fleet = ParallelAgent(
    name="reporting_fleet",
    description=(
        "Concurrently executes report synthesis and JSON metrics extraction, "
        "maximizing throughput in the final reporting phase."
    ),
    sub_agents=[
        synthesis_pipeline, # Refined synthesis loop
        metrics_agent,      # Reads expert results → review_metrics
    ],
)

# ---------------------------------------------------------------------------
# Step 3: The Review Pipeline — sequential: ingest → fleet → reporting
# Optimized for minimum sequential depth (3 stages).
# ---------------------------------------------------------------------------
review_pipeline = SequentialAgent(
    name="review_pipeline",
    description=(
        "An optimized, low-latency execution pipeline. It fetches code, "
        "runs parallel experts, and concurrently generates the final report and metrics."
    ),
    sub_agents=[
        ingestion_agent,   # Writes raw_codebase to state
        review_fleet,      # Reads raw_codebase, writes 4 review results (Parallel)
        reporting_fleet,   # Synthesis & Metrics (Parallel)
        html_agent,        # Translates synthesis_result to HTML
    ],
)

# ---------------------------------------------------------------------------
# Step 3: Root Agent — the user-facing supervisor
# ADK requires root_agent to be defined at module level with this exact name.
# Using `global_instruction` to set the brand-voice context for all agents.
# ---------------------------------------------------------------------------
root_agent = Agent(
    name="root_agent",
    model=configs.agent_settings.root_model,
    description="ADK Code Reviewer — analyses GitHub, Bitbucket, or uploaded code.",
    before_agent_callback=constitution_callback,
    global_instruction=(
        "You are the ADK Code Reviewer system. "
        "You produce professional, evidence-based code review reports. "
        "Always be concise, precise, and grounded in actual code evidence. "
        "Adhere to the following core standards:\n"
        "- **Quality:** Prioritize maintainability, clear naming, and specific error handling.\n"
        "- **Security:** Flag hardcoded secrets and potential injection vulnerabilities.\n"
        "- **Structure:** Ensure all code snippets are properly fenced in markdown.\n"
        "- **Constitution:** You MUST follow the protocols in: {constitution}\n"
        "Never hallucinate file names, function names, or API calls."
    ),
    instruction=SUPERVISOR_PROMPT,
    sub_agents=[review_pipeline],
    planner=PlanReActPlanner(),
    generate_content_config=configs.safety_config,
)

# ---------------------------------------------------------------------------
# Step 4: ADK App Configuration — caching, logging, resumability
# ---------------------------------------------------------------------------
# Create the app with context caching, resumability, and logging configuration
app = App(
    name='code_reviewer',
    root_agent=root_agent,
    plugins=[LoggingPlugin()],
    context_cache_config=ContextCacheConfig(
        min_tokens=32768, # Cache larger inputs like full repositories
        ttl_seconds=3600, # Store for up to 1 hour
        cache_intervals=10, 
    ),
    resumability_config=ResumabilityConfig(
        is_resumable=True
    ),
)
