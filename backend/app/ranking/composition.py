"""Result-set composition: "N sections of mode A, M of mode B."

Distinct from hard-constraint filtering (app.ranking.hard_filter), which
decides whether a single candidate is acceptable at all. Composition
decides how many of each acceptable delivery mode make it into the final
result set, once every candidate has already been ranked by Fit Score.
"""

from app.schemas.ai_search import DeliveryModeCount
from app.schemas.recommendation import SectionRecommendation


def compose_by_delivery_mode_counts(
    recommendations: list[SectionRecommendation],
    mode_counts: list[DeliveryModeCount],
) -> tuple[list[SectionRecommendation], list[str]]:
    """Selects up to `count` highest-fit-score recommendations per requested
    mode. A section is never selected twice even if requested modes overlap.
    Returns (selected, notes) -- notes explain any mode that couldn't be
    fully filled, so the shortfall is visible rather than silently returned.
    """
    selected: list[SectionRecommendation] = []
    used_section_ids: set = set()
    notes: list[str] = []

    for entry in mode_counts:
        candidates = sorted(
            (
                rec
                for rec in recommendations
                if rec.section.delivery_mode == entry.mode and rec.section.id not in used_section_ids
            ),
            key=lambda rec: rec.fit_score,
            reverse=True,
        )
        chosen = candidates[: entry.count]
        selected.extend(chosen)
        used_section_ids.update(rec.section.id for rec in chosen)

        if len(chosen) < entry.count:
            mode_label = entry.mode.replace("_", " ")
            notes.append(
                f"Only {len(chosen)} {mode_label} section(s) matched your other requirements "
                f"(you asked for {entry.count})."
            )

    selected.sort(key=lambda rec: rec.fit_score, reverse=True)
    return selected, notes
