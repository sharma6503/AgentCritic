"""
Security Expert - V2 (Full implementation)
=========================================
Equipped with the 'Security-Hardening' skill for infrastructure audits.
"""

import pathlib
import logging
from google.adk import Agent
from ..config import Config
from ..prompts import SECURITY_EXPERT_PROMPT

logger = logging.getLogger(__name__)
_cfg = Config()
_tools = []

# Load Security-Hardening Skill
try:
    from google.adk.skills import load_skill_from_dir
    from google.adk.tools import skill_toolset
    _skill_dir = pathlib.Path(__file__).parent.parent / "skills" / "security_hardening"
    if _skill_dir.exists():
        security_skill = load_skill_from_dir(_skill_dir)
        _tools.append(skill_toolset.SkillToolset(skills=[security_skill]))
        logger.info("Security Expert V2: Loaded 'security-hardening' skill.")
except Exception as e:
    logger.warning(f"Security Expert V2: Could not load skill: {e}")

security_expert = Agent(
    name="security_expert",
    model=_cfg.agent_settings.expert_model,
    instruction=SECURITY_EXPERT_PROMPT,
    tools=_tools,
    output_key="security_review_result",
    generate_content_config=_cfg.safety_config,
)
