import logging

from app.agents.assessment_llm_extractor import AssessmentLLMError, extract_assessment_with_llm
from app.core.config import get_settings
from app.ingestion.assessment_extraction_rules import extract_assessment_rule_based

logger = logging.getLogger(__name__)


def extract_assessment(syllabus_text: str) -> dict:
    settings = get_settings()
    if settings.anthropic_api_key:
        try:
            return extract_assessment_with_llm(syllabus_text)
        except AssessmentLLMError as exc:
            logger.warning(
                "LLM assessment extraction failed, falling back to rule-based: %s", exc
            )

    return extract_assessment_rule_based(syllabus_text)
