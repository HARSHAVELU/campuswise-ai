"""Personalized Fit Score.

Weights are defaults, not fixed percentages: a dimension only counts toward
the score when it is both requested and backed by real data, and the
remaining weights are renormalized to sum to 1 -- so the score always
reflects only what could actually be verified (see docs/architecture-proposal.md,
"Personalized Course Fit Score").
"""

from typing import cast

from app.ranking.features import DimensionResult

DEFAULT_WEIGHTS: dict[str, float] = {
    "professor_rating": 0.30,
    "historical_grades": 0.30,
    "delivery_mode_preference": 0.15,
    "exam_preference": 0.10,
    "difficulty_preference": 0.10,
    "campus_days_preference": 0.05,
}


def compute_fit_score(
    features: dict[str, DimensionResult], weights: dict[str, float] = DEFAULT_WEIGHTS
) -> tuple[int | None, dict[str, float]]:
    applicable: dict[str, float] = {
        name: cast(float, result.score)
        for name, result in features.items()
        if result.requested and result.score is not None
    }
    if not applicable:
        return None, {}

    total_weight = sum(weights.get(name, 0) for name in applicable)
    if total_weight > 0:
        normalized_weights = {name: weights.get(name, 0) / total_weight for name in applicable}
    else:
        normalized_weights = {name: 1 / len(applicable) for name in applicable}

    weighted_sum = sum(applicable[name] * normalized_weights[name] for name in applicable)
    breakdown = {name: round(applicable[name], 1) for name in applicable}
    return round(weighted_sum), breakdown
