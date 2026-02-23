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
          ├── synthesis_agent               ← Combines all 4 results → draft report
          ├── critic_agent                  ← Fact-checks draft against raw_codebase
          └── reviser_agent                 ← Applies critic's findings → final report

Shared State Flow:
  user_request  ──────────────────────────────────► ingestion_agent
  raw_codebase  ──► [adk_expert, quality_expert, security_expert, code_validator] (parallel)
  review results ─────────────────────────────────► synthesis_agent → synthesis_result
  synthesis_result + raw_codebase ────────────────► critic_agent   → critic_findings
  synthesis_result + critic_findings ─────────────► reviser_agent  → final report

Callbacks (adopted from google/adk-samples/customer-service, llm-auditor):
  - critic_agent:  after_model_callback strips ---END-OF-CRITIQUE--- sentinel
  - reviser_agent: after_model_callback strips ---END-OF-EDIT---    sentinel

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
from .utils.compat import setup_platform_compat

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
from google.adk.planners.plan_re_act_planner import PlanReActPlanner  # noqa: E402

from .config import Config  # noqa: E402
from .prompts import SUPERVISOR_PROMPT  # noqa: E402
from .sub_agents import (  # noqa: E402
    ingestion_agent,
    adk_expert,
    quality_expert,
    security_expert,
    code_validator_agent,
    synthesis_agent,
    metrics_agent,
    critic_agent,
    reviser_agent,
)

# Instantiate config — reads from env vars / .env
configs = Config()

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
# Step 2: The Reporting Fleet — concurrently synthesise report and extract metrics
# ---------------------------------------------------------------------------
reporting_fleet = ParallelAgent(
    name="reporting_fleet",
    description=(
        "Concurrently executes report synthesis and JSON metrics extraction, "
        "maximizing throughput in the final reporting phase."
    ),
    sub_agents=[
        synthesis_agent,   # Reads 4 expert results → synthesis_result
        metrics_agent,     # Reads 4 expert results → review_metrics
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
    global_instruction=(
        "You are the ADK Code Reviewer system. "
        "You produce professional, evidence-based code review reports. "
        "Always be concise, precise, and grounded in actual code evidence. "
        "Never hallucinate file names, function names, or API calls."
    ),
    instruction=SUPERVISOR_PROMPT,
    sub_agents=[review_pipeline],
    planner=PlanReActPlanner(),
    generate_content_config=configs.safety_config,
)
