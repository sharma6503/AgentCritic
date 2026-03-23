"""Code Quality Expert Agent — uses fast model for parallel expert fleet."""

from google.adk import Agent
from code_reviewer.config import Config
from code_reviewer.prompts import QUALITY_EXPERT_PROMPT
import pathlib
import logging
from ..tools import (
    github_get_multiple_files,
    parse_uploaded_files,
    github_get_file_contents
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ADK Best Practice: Skill Integration
# ---------------------------------------------------------------------------
_tools = [
    github_get_multiple_files,
    parse_uploaded_files,
    github_get_file_contents
]
try:
    from google.adk.skills import load_skill_from_dir
    from google.adk.tools import skill_toolset
    
    _skill_dir = pathlib.Path(__file__).parent.parent / "skills" / "bug-fixing"
    if _skill_dir.exists():
        bug_fixing_skill = load_skill_from_dir(_skill_dir)
        _tools.append(skill_toolset.SkillToolset(skills=[bug_fixing_skill]))
        logger.info("Quality Expert: Loaded 'bug-fixing' skill.")
except ImportError:
    logger.debug("Skill system not supported in this ADK version.")
except Exception as e:
    logger.warning(f"Could not load BugFixing skill: {e}")

_cfg = Config()

quality_expert = Agent(
    name="code_quality_expert",
    model=_cfg.agent_settings.expert_model,
    description="Expert Python code quality reviewer — types, docs, errors, tests.",
    instruction=QUALITY_EXPERT_PROMPT,
    tools=_tools,
    output_key="quality_review_result",
    generate_content_config=_cfg.safety_config,
)
