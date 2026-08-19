from pydantic import BaseModel

from app.schemas.ai_search import ParsedRequirement
from app.schemas.section import SectionRead


class SectionRecommendation(BaseModel):
    section: SectionRead
    fit_score: int
    score_breakdown: dict[str, float]
    matched: list[str]
    not_matched: list[str]
    missing_info: list[str]


class RecommendationRequest(BaseModel):
    query: str


class RecommendationResponse(BaseModel):
    parsed: ParsedRequirement
    recommendations: list[SectionRecommendation]
    notes: list[str] = []
