"""
AI Agent Prompt 模块

本模块包含教学 Agent 所需的全部领域知识和行为准则。
CLAUDE.md 中不需要了解这些细节——这些是给 AI 教学系统自己用的。
"""

from .domain_knowledge import (
    MODELING_PROCESS_5_STEPS,
    MODEL_CLASSIFICATIONS,
    MODEL_DETAILS,
    MATH_TERMINOLOGY,
)
from .teaching_guidelines import (
    TEACHING_PRINCIPLES,
    RESPONSE_STYLE_GUIDE,
    SCENARIO_HANDLING,
)
from .user_profiles import (
    USER_PROFILES,
    USER_SCENARIOS,
)

__all__ = [
    "MODELING_PROCESS_5_STEPS",
    "MODEL_CLASSIFICATIONS",
    "MODEL_DETAILS",
    "MATH_TERMINOLOGY",
    "TEACHING_PRINCIPLES",
    "RESPONSE_STYLE_GUIDE",
    "SCENARIO_HANDLING",
    "USER_PROFILES",
    "USER_SCENARIOS",
]
