"""
Agent Critic V2 - Core Graph Workflow
Replicates 100% of V1 logic in an ADK 2.0 Parallel Execution Graph.
"""

import logging
from google.adk.apps.app import App, ResumabilityConfig
from google.adk.plugins.logging_plugin import LoggingPlugin
from google.adk.plugins import ReflectAndRetryToolPlugin
from google.adk import Workflow

from .config import Config
from .sub_agents import (
    ingestion_agent,
    adk_expert,
    quality_expert,
    security_expert,
    code_validator_agent,
    synthesis_agent,
    metrics_agent,
    html_agent
)
from .sub_agents.callbacks import (
    traffic_shaper_callback, 
    constitution_callback, 
    pre_review_reset_callback
)

logger = logging.getLogger(__name__)
_cfg = Config()

# --- Expert Fleet (Run in Parallel) ---
experts = [adk_expert, quality_expert, security_expert, code_validator_agent]

# --- Workflow Definition ---
agent_critic_v2 = Workflow(
    name="agent_critic_v2",
    before_agent_callback=[pre_review_reset_callback, constitution_callback],
    edges=[
        ("START", ingestion_agent),
        (ingestion_agent, experts), # Parallel Analysis
        (experts, synthesis_agent), # Collate findings
        (synthesis_agent, [metrics_agent, html_agent]), # Parallel reporting
        ([metrics_agent, html_agent], "END")
    ]
)

# Root Agent Wrapper
agent = agent_critic_v2

# Create the App with all plugins and caching enabled
app = App(
    name='agent_critic_v2',
    root_agent=agent,
    plugins=[
        LoggingPlugin(),
        ReflectAndRetryToolPlugin(max_retries=_cfg.max_retries)
    ],
    resumability_config=ResumabilityConfig(is_resumable=True)
)
