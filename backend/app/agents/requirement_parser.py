"""RequirementParserAgent: turns a natural-language query into ParsedRequirement.

Tries the LLM-backed parser first (accurate, handles open-ended phrasing).
Falls back to the deterministic rule-based parser if no LLM is configured or
the call fails, so search keeps working -- with reduced accuracy -- offline,
in CI, and in local development without an API key.
"""

import logging

from app.agents.llm_parser import LLMParserError, parse_requirement_with_llm
from app.agents.rule_based_parser import parse_requirement_rule_based
from app.core.config import get_settings
from app.schemas.ai_search import ParsedRequirement

logger = logging.getLogger(__name__)


def parse_requirement(query: str) -> ParsedRequirement:
    settings = get_settings()
    if settings.anthropic_api_key:
        try:
            return parse_requirement_with_llm(query)
        except LLMParserError as exc:
            logger.warning("LLM requirement parsing failed, falling back to rule-based: %s", exc)

    return parse_requirement_rule_based(query)
