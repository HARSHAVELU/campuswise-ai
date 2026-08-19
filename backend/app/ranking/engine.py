import uuid

from sqlalchemy.orm import Session

from app.analytics.grade_stats import GradeDistributionStats, compute_grade_distribution
from app.models.assessment import AssessmentMetadata
from app.models.section import Section
from app.ranking.explain import build_explanation
from app.ranking.features import compute_features
from app.ranking.fit_score import compute_fit_score
from app.ranking.hard_filter import HardFilterResult, apply_hard_constraints
from app.repositories.assessment_repository import AssessmentRepository
from app.repositories.grade_repository import GradeRepository
from app.schemas.ai_search import ParsedRequirement
from app.schemas.recommendation import SectionRecommendation
from app.schemas.section import SectionRead

INSUFFICIENT_DATA_SCORE = 50
INSUFFICIENT_DATA_NOTE = "Not enough data was available to fully personalize this score."

_CacheKey = tuple[uuid.UUID, uuid.UUID | None]


def rank_sections(
    db: Session, parsed: ParsedRequirement, sections: list[Section]
) -> tuple[list[SectionRecommendation], HardFilterResult]:
    filter_result = apply_hard_constraints(sections, parsed.hard_constraints)

    grade_repo = GradeRepository(db)
    assessment_repo = AssessmentRepository(db)
    grade_stats_cache: dict[_CacheKey, GradeDistributionStats] = {}
    assessment_cache: dict[_CacheKey, AssessmentMetadata | None] = {}
    recommendations: list[SectionRecommendation] = []

    for section in filter_result.passed:
        cache_key = (section.course_id, section.professor_id)
        if cache_key not in grade_stats_cache:
            records = (
                grade_repo.find(course_id=section.course_id, professor_id=section.professor_id)
                if section.professor_id
                else []
            )
            grade_stats_cache[cache_key] = compute_grade_distribution(records)
        grade_stats = grade_stats_cache[cache_key]

        if cache_key not in assessment_cache:
            assessment_cache[cache_key] = assessment_repo.find_one(
                course_id=section.course_id, professor_id=section.professor_id
            )
        assessment = assessment_cache[cache_key]

        features = compute_features(section, parsed, grade_stats, assessment)
        fit_score, breakdown = compute_fit_score(features)
        matched, not_matched, missing = build_explanation(features)

        if fit_score is None:
            fit_score = INSUFFICIENT_DATA_SCORE
            missing.insert(0, INSUFFICIENT_DATA_NOTE)

        recommendations.append(
            SectionRecommendation(
                section=SectionRead.model_validate(section),
                fit_score=fit_score,
                score_breakdown=breakdown,
                matched=matched,
                not_matched=not_matched,
                missing_info=missing,
            )
        )

    recommendations.sort(key=lambda rec: rec.fit_score, reverse=True)
    return recommendations, filter_result
