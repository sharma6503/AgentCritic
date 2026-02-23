"""Security & Deployment Expert Agent — uses fast model for parallel expert fleet."""

from google.adk import Agent
from ..config import Config
from ..prompts import SECURITY_EXPERT_PROMPT
import pathlib
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ADK Best Practice: Skill Integration
# ---------------------------------------------------------------------------
_tools = []
try:
    from google.adk.skills import load_skill_from_dir
    from google.adk.tools import skill_toolset
    
    _skill_dir = pathlib.Path(__file__).parent.parent / "skills" / "security_hardening"
    if _skill_dir.exists():
        security_skill = load_skill_from_dir(_skill_dir)
        _tools.append(skill_toolset.SkillToolset(skills=[security_skill]))
        logger.info("Security Expert: Loaded 'security-hardening' skill.")
except ImportError:
    logger.debug("Skill system not supported in this ADK version.")
except Exception as e:
    logger.warning(f"Could not load SecurityHardening skill: {e}")

_cfg = Config()

security_expert = Agent(
    name="security_expert",
    model=_cfg.agent_settings.expert_model,
    description="Security and cloud deployment expert — secrets, deps, IAM, Cloud Run.",
    instruction=SECURITY_EXPERT_PROMPT,
    tools=_tools,
    output_key="security_review_result",
    generate_content_config=_cfg.safety_config,
)
