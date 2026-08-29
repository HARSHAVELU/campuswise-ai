"""Semester schedule generation via constraint optimization (Google OR-Tools CP-SAT).

Hard constraints (never violated): at most one section per course, total
credit hours within the requested range, no two selected sections'
meetings overlap in time. Everything else -- which sections are "best" --
is an objective function, not a filter, so it can vary per named strategy
without touching the constraint model (see docs/architecture-proposal.md,
"Schedule Optimization").

Candidates arrive pre-scored (as SectionRecommendation, from the
Recommendation Engine's ranking pipeline) so the optimizer never invents a
quality signal of its own -- it only combines numbers that were already
computed from real data.
"""

from dataclasses import dataclass
from enum import Enum

from ortools.sat.python import cp_model

from app.optimization.conflict_detection import meetings_overlap
from app.schemas.ai_search import DeliveryModeCount
from app.schemas.recommendation import SectionRecommendation

SOLVER_TIME_LIMIT_SECONDS = 5.0


class ScheduleStrategy(str, Enum):
    BEST_OVERALL = "best_overall"
    BEST_PROFESSORS = "best_professors"
    FEWEST_CAMPUS_DAYS = "fewest_campus_days"
    BEST_GRADES = "best_grades"
    ONLINE_HEAVY = "online_heavy"


STRATEGY_LABELS = {
    ScheduleStrategy.BEST_OVERALL: "Best Overall",
    ScheduleStrategy.BEST_PROFESSORS: "Best Professors",
    ScheduleStrategy.FEWEST_CAMPUS_DAYS: "Fewest Campus Days",
    ScheduleStrategy.BEST_GRADES: "Best Historical Grades",
    ScheduleStrategy.ONLINE_HEAVY: "Online-Heavy",
}

ALL_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


@dataclass
class ScheduleSolution:
    selected: list[SectionRecommendation]
    total_credits: int
    campus_days: list[str]


def _sections_conflict(rec_a: SectionRecommendation, rec_b: SectionRecommendation) -> bool:
    for meeting_a in rec_a.section.meetings:
        for meeting_b in rec_b.section.meetings:
            if meetings_overlap(meeting_a, meeting_b):
                return True
    return False


def _strategy_score(rec: SectionRecommendation, strategy: ScheduleStrategy) -> int:
    if strategy == ScheduleStrategy.BEST_PROFESSORS:
        return round(rec.score_breakdown.get("professor_rating", 0.0))
    if strategy == ScheduleStrategy.BEST_GRADES:
        return round(rec.score_breakdown.get("historical_grades", 0.0))
    if strategy == ScheduleStrategy.ONLINE_HEAVY:
        mode = rec.section.delivery_mode
        return {"online": 100, "hybrid": 60}.get(mode, 0)
    return rec.fit_score  # BEST_OVERALL and the base score for FEWEST_CAMPUS_DAYS's tiebreak


def solve_schedule(
    recommendations: list[SectionRecommendation],
    strategy: ScheduleStrategy,
    min_credits: int,
    max_credits: int,
    required_course_ids: set | None = None,
    delivery_mode_counts: list[DeliveryModeCount] | None = None,
) -> ScheduleSolution | None:
    n = len(recommendations)
    if n == 0:
        return None

    model = cp_model.CpModel()
    x = [model.NewBoolVar(f"x{i}") for i in range(n)]

    credit_terms = [recommendations[i].section.course.credit_hours * x[i] for i in range(n)]
    model.Add(sum(credit_terms) >= min_credits)
    model.Add(sum(credit_terms) <= max_credits)

    courses: dict = {}
    for i, rec in enumerate(recommendations):
        courses.setdefault(rec.section.course.id, []).append(i)
    for course_id, idxs in courses.items():
        model.Add(sum(x[i] for i in idxs) <= 1)
        if required_course_ids and course_id in required_course_ids:
            model.Add(sum(x[i] for i in idxs) == 1)

    if delivery_mode_counts:
        for entry in delivery_mode_counts:
            mode_idxs = [
                i for i, rec in enumerate(recommendations) if rec.section.delivery_mode == entry.mode
            ]
            model.Add(sum(x[i] for i in mode_idxs) >= entry.count)

    for i in range(n):
        for j in range(i + 1, n):
            if _sections_conflict(recommendations[i], recommendations[j]):
                model.Add(x[i] + x[j] <= 1)

    scores = [_strategy_score(recommendations[i], strategy) for i in range(n)]

    if strategy == ScheduleStrategy.FEWEST_CAMPUS_DAYS:
        day_used = {d: model.NewBoolVar(f"day_{d}") for d in ALL_DAYS}
        for d in ALL_DAYS:
            meeting_idxs = [
                i
                for i, rec in enumerate(recommendations)
                if any(m.day_of_week == d for m in rec.section.meetings)
            ]
            for i in meeting_idxs:
                model.Add(day_used[d] >= x[i])
        # Minimizing campus days dominates; fit score only breaks ties.
        model.Maximize(
            sum(scores[i] * x[i] for i in range(n)) - 1000 * sum(day_used[d] for d in ALL_DAYS)
        )
    else:
        model.Maximize(sum(scores[i] * x[i] for i in range(n)))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = SOLVER_TIME_LIMIT_SECONDS
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None

    selected = [recommendations[i] for i in range(n) if solver.Value(x[i]) == 1]
    if not selected:
        return None

    total_credits = sum(rec.section.course.credit_hours for rec in selected)
    campus_days = sorted(
        {m.day_of_week for rec in selected for m in rec.section.meetings}, key=ALL_DAYS.index
    )
    return ScheduleSolution(selected=selected, total_credits=total_credits, campus_days=campus_days)


def diagnose_insufficient_mode_candidates(
    recommendations: list[SectionRecommendation], delivery_mode_counts: list[DeliveryModeCount]
) -> list[str]:
    """Checks whether the *candidate pool itself* (before conflicts/credits are
    even considered) has enough sections of each requested mode. If not, that's
    almost certainly why a schedule came back infeasible, so it's worth saying
    explicitly rather than leaving the student with a generic "no schedule found."
    """
    notes = []
    for entry in delivery_mode_counts:
        available = sum(1 for rec in recommendations if rec.section.delivery_mode == entry.mode)
        if available < entry.count:
            mode_label = entry.mode.replace("_", " ")
            notes.append(
                f"Only {available} {mode_label} section(s) are available among your candidates; "
                f"you requested at least {entry.count}."
            )
    return notes
