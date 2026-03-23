"""
Quality Expert - V2 (Full implementation)
========================================
Equipped with the 'Bug-Fixing' skill for professional refactoring.
"""

import pathlib
import logging
from google.adk import Agent
from ..config import Config
from ..prompts import QUALITY_EXPERT_PROMPT

logger = logging.getLogger(__name__)
_cfg = Config()
_tools = []

# Load Bug-Fixing Skill
try:
    from google.adk.skills import load_skill_from_dir
    from google.adk.tools import skill_toolset
    _skill_dir = pathlib.Path(__file__).parent.parent / "skills" / "bug_fixing"
    if _skill_dir.exists():
        bug_fixing_skill = load_skill_from_dir(_skill_dir)
        _tools.append(skill_toolset.SkillToolset(skills=[bug_fixing_skill]))
        logger.info("Quality Expert V2: Loaded 'bug-fixing' skill.")
except Exception as e:
    logger.warning(f"Quality Expert V2: Could not load skill: {e}")

quality_expert = Agent(
    name="code_quality_expert",
    model=_cfg.agent_settings.expert_model,
    instruction=QUALITY_EXPERT_PROMPT,
    tools=_tools,
    output_key="quality_review_result",
    generate_content_config=_cfg.safety_config,
)
