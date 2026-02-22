"""
Configuration dataclass for the ADK Code Reviewer agent.
Centralises all environment-driven settings in a single place,
following the pattern used in google/adk-samples/customer-service.
"""

import os
from dataclasses import dataclass, field


@dataclass
class AgentSettings:
    """Model & identity settings for each agent tier.

    Latency strategy:
      - Root supervisor:  gemini-2.0-flash (fast routing, no deep reasoning)
      - Expert fleet:     gemini-2.0-flash (4 run in parallel, speed > depth)
      - Synthesis/critic: gemini-2.5-flash (highest quality for final report)
    """

    # Root supervisor — FAST routing only, never generates long output
    root_model: str = field(
        default_factory=lambda: os.environ.get("ROOT_MODEL", "gemini-2.5-flash")
    )
    # Expert reviewer fleet — runs 4× in parallel, speed matters most
    expert_model: str = field(
        default_factory=lambda: os.environ.get("EXPERT_MODEL", "gemini-2.5-flash")
    )
    # Synthesis + metrics (parallel) — quality matters for final output
    synthesis_model: str = field(
        default_factory=lambda: os.environ.get(
            "SYNTHESIS_MODEL", "gemini-2.5-flash"
        )
    )


@dataclass
class Config:
    """Top-level configuration container."""

    agent_settings: AgentSettings = field(default_factory=AgentSettings)

    # GitHub / Bitbucket auth (optional — MCP falls back gracefully)
    github_token: str | None = field(
        default_factory=lambda: os.environ.get("GITHUB_TOKEN")
    )
    bitbucket_username: str | None = field(
        default_factory=lambda: os.environ.get("BITBUCKET_USERNAME")
    )
    bitbucket_app_password: str | None = field(
        default_factory=lambda: os.environ.get("BITBUCKET_APP_PASSWORD")
    )

    # Ingestion limits
    max_file_size_kb: int = field(
        default_factory=lambda: int(os.environ.get("MAX_FILE_SIZE_KB", "500"))
    )

    # Global safety settings wrapped in a config dict for generate_content_config
    safety_config: dict = field(
        default_factory=lambda: {
            "safety_settings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        }
    )
