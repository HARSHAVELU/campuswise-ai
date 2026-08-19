from app.optimization.schedule_optimizer import ScheduleStrategy, solve_schedule
from app.schemas.course import CourseSummary
from app.schemas.recommendation import SectionRecommendation
from app.schemas.section import SectionMeetingRead, SectionRead
from app.schemas.university import DepartmentRead

DEPT = DepartmentRead(id="00000000-0000-0000-0000-000000000001", code="CS", name="Computer Science")
TERM = {"id": "00000000-0000-0000-0000-000000000003", "name": "Fall 2026", "year": 2026, "season": "fall", "is_active_for_planning": True}


def _course(idx, credit_hours=3):
    return CourseSummary(
        id=f"10000000-0000-0000-0000-{idx:012d}", code=f"CS {1000 + idx}", title=f"Course {idx}",
        credit_hours=credit_hours, level="undergraduate", department=DEPT, topics=[],
    )


def _rec(idx, day, start, end, fit_score, professor_rating=None, delivery_mode="in_person", credit_hours=3):
    course = _course(idx, credit_hours)
    section = SectionRead(
        id=f"20000000-0000-0000-0000-{idx:012d}", section_number="001", delivery_mode=delivery_mode,
        seats_total=30, seats_available=10, course=course, term=TERM, professor=None,
        meetings=[SectionMeetingRead(day_of_week=day, start_time=start, end_time=end, room_id=None)] if day else [],
    )
    breakdown = {"professor_rating": professor_rating} if professor_rating is not None else {}
    return SectionRecommendation(
        section=section, fit_score=fit_score, score_breakdown=breakdown,
        matched=[], not_matched=[], missing_info=[],
    )


def test_selects_non_conflicting_sections_within_credit_range():
    recs = [
        _rec(1, "monday", "09:00", "10:15", fit_score=90),
        _rec(2, "wednesday", "09:00", "10:15", fit_score=85),
        _rec(3, "monday", "09:30", "10:45", fit_score=95),  # conflicts with rec 1
    ]
    solution = solve_schedule(recs, ScheduleStrategy.BEST_OVERALL, min_credits=3, max_credits=9)
    assert solution is not None
    selected_ids = {rec.section.id for rec in solution.selected}
    assert not ({recs[0].section.id, recs[2].section.id} <= selected_ids)  # never both 1 and 3


def test_respects_credit_range():
    recs = [_rec(i, "monday", "09:00", "10:15", fit_score=80, credit_hours=3) for i in range(1, 4)]
    for i in range(1, 4):
        recs[i - 1] = _rec(i, ["monday", "tuesday", "wednesday"][i - 1], "09:00", "10:15", fit_score=80, credit_hours=3)
    solution = solve_schedule(recs, ScheduleStrategy.BEST_OVERALL, min_credits=6, max_credits=9)
    assert solution is not None
    assert 6 <= solution.total_credits <= 9


def test_infeasible_credit_range_returns_none():
    recs = [_rec(1, "monday", "09:00", "10:15", fit_score=80, credit_hours=3)]
    solution = solve_schedule(recs, ScheduleStrategy.BEST_OVERALL, min_credits=20, max_credits=25)
    assert solution is None


def test_no_candidates_returns_none():
    assert solve_schedule([], ScheduleStrategy.BEST_OVERALL, min_credits=3, max_credits=18) is None


def test_at_most_one_section_per_course():
    course_a_section_1 = _rec(1, "monday", "09:00", "10:15", fit_score=70)
    course_a_section_2 = _rec(2, "tuesday", "09:00", "10:15", fit_score=95)
    course_a_section_2.section.course = course_a_section_1.section.course  # same course, different section
    solution = solve_schedule(
        [course_a_section_1, course_a_section_2], ScheduleStrategy.BEST_OVERALL, min_credits=1, max_credits=6
    )
    assert solution is not None
    assert len(solution.selected) == 1
    assert solution.selected[0].fit_score == 95  # picks the higher-scoring section of the only course


def test_best_professors_strategy_prefers_higher_rated_over_higher_fit_score():
    low_fit_high_rating = _rec(1, "monday", "09:00", "10:15", fit_score=50, professor_rating=95.0)
    high_fit_low_rating = _rec(2, "wednesday", "09:00", "10:15", fit_score=90, professor_rating=20.0)
    solution = solve_schedule(
        [low_fit_high_rating, high_fit_low_rating],
        ScheduleStrategy.BEST_PROFESSORS,
        min_credits=1,
        max_credits=3,
    )
    assert solution is not None
    assert solution.selected[0].section.id == low_fit_high_rating.section.id


def test_fewest_campus_days_prefers_single_day_over_spread_out_schedule():
    same_day_a = _rec(1, "monday", "09:00", "10:15", fit_score=80, credit_hours=3)
    same_day_b = _rec(2, "monday", "11:00", "12:15", fit_score=80, credit_hours=3)
    spread_c = _rec(3, "tuesday", "09:00", "10:15", fit_score=80, credit_hours=3)
    spread_d = _rec(4, "thursday", "09:00", "10:15", fit_score=80, credit_hours=3)

    solution = solve_schedule(
        [same_day_a, same_day_b, spread_c, spread_d],
        ScheduleStrategy.FEWEST_CAMPUS_DAYS,
        min_credits=6,
        max_credits=6,
    )
    assert solution is not None
    assert solution.campus_days == ["monday"]


def test_online_heavy_prefers_online_sections():
    online_low_fit = _rec(1, None, None, None, fit_score=60, delivery_mode="online")
    in_person_high_fit = _rec(2, "monday", "09:00", "10:15", fit_score=99, delivery_mode="in_person")
    solution = solve_schedule(
        [online_low_fit, in_person_high_fit], ScheduleStrategy.ONLINE_HEAVY, min_credits=1, max_credits=3
    )
    assert solution is not None
    assert solution.selected[0].section.delivery_mode == "online"
