"""
Configuration for Agent Critic 2.0
"""
import os
from dataclasses import dataclass, field

@dataclass
class AgentSettings:
    root_model: str = field(default_factory=lambda: os.environ.get("ROOT_MODEL", "gemini-2.0-flash"))
    expert_model: str = field(default_factory=lambda: os.environ.get("EXPERT_MODEL", "gemini-2.0-flash"))
    synthesis_model: str = field(default_factory=lambda: os.environ.get("SYNTHESIS_MODEL", "gemini-2.5-flash"))

@dataclass
class Config:
    agent_settings: AgentSettings = field(default_factory=AgentSettings)
    github_token: str | None = field(default_factory=lambda: os.environ.get("GITHUB_TOKEN"))
    max_concurrency: int = field(default_factory=lambda: int(os.environ.get("MAX_CONCURRENCY", "2")))
    max_retries: int = field(default_factory=lambda: int(os.environ.get("MAX_RETRIES", "5")))
    safety_config: dict = field(default_factory=lambda: {
        "safety_settings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
    })
