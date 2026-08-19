from app.ranking.features import DimensionResult

MATCH_THRESHOLD = 70.0

# Platform-wide data gaps that apply to every recommendation until a later
# phase adds the underlying data (Review Intelligence). Exam format is no
# longer always-missing as of Phase 7 -- it's now a real dimension in
# `features.py` that reports its own missing-data message when unavailable.
ALWAYS_MISSING_NOTES = [
    "Student review summaries are not yet available for this professor.",
    "Workload/assignment-count information is not yet available for this section.",
]


def build_explanation(features: dict[str, DimensionResult]) -> tuple[list[str], list[str], list[str]]:
    matched: list[str] = []
    not_matched: list[str] = []
    missing: list[str] = []

    for result in features.values():
        if not result.requested:
            continue
        if result.score is None:
            missing.append(result.detail)
        elif result.score >= MATCH_THRESHOLD:
            matched.append(result.detail)
        else:
            not_matched.append(result.detail)

    missing.extend(ALWAYS_MISSING_NOTES)
    return matched, not_matched, missing
