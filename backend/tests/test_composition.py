
from app.ranking.composition import compose_by_delivery_mode_counts
from app.schemas.ai_search import DeliveryModeCount
from app.schemas.course import CourseSummary
from app.schemas.recommendation import SectionRecommendation
from app.schemas.section import SectionRead
from app.schemas.university import DepartmentRead

DEPT = DepartmentRead(id="00000000-0000-0000-0000-000000000001", code="CS", name="Computer Science")
TERM = {"id": "00000000-0000-0000-0000-000000000003", "name": "Fall 2026", "year": 2026, "season": "fall", "is_active_for_planning": True}


def _rec(idx: int, delivery_mode: str, fit_score: int) -> SectionRecommendation:
    course = CourseSummary(
        id=f"10000000-0000-0000-0000-{idx:012d}", code=f"CS {1000 + idx}", title=f"Course {idx}",
        credit_hours=3, level="undergraduate", department=DEPT, topics=[],
    )
    section = SectionRead(
        id=f"20000000-0000-0000-0000-{idx:012d}", section_number="001", delivery_mode=delivery_mode,
        seats_total=30, seats_available=10, course=course, term=TERM, professor=None, meetings=[],
    )
    return SectionRecommendation(
        section=section, fit_score=fit_score, score_breakdown={}, matched=[], not_matched=[], missing_info=[],
    )


def test_selects_requested_count_per_mode():
    recs = [
        _rec(1, "online", 90),
        _rec(2, "online", 85),
        _rec(3, "online", 80),
        _rec(4, "in_person", 70),
        _rec(5, "in_person", 60),
    ]
    selected, notes = compose_by_delivery_mode_counts(
        recs, [DeliveryModeCount(mode="online", count=2), DeliveryModeCount(mode="in_person", count=2)]
    )
    assert len(selected) == 4
    modes = [r.section.delivery_mode for r in selected]
    assert modes.count("online") == 2
    assert modes.count("in_person") == 2
    assert notes == []


def test_prefers_highest_fit_score_within_each_mode():
    recs = [_rec(1, "online", 50), _rec(2, "online", 95), _rec(3, "online", 70)]
    selected, _ = compose_by_delivery_mode_counts(recs, [DeliveryModeCount(mode="online", count=2)])
    assert [r.fit_score for r in selected] == [95, 70]


def test_shortfall_reported_when_not_enough_candidates():
    recs = [_rec(1, "online", 90)]
    selected, notes = compose_by_delivery_mode_counts(
        recs, [DeliveryModeCount(mode="online", count=3)]
    )
    assert len(selected) == 1
    assert len(notes) == 1
    assert "3" in notes[0] and "1" in notes[0]


def test_no_double_selection_across_overlapping_mode_requests():
    recs = [_rec(1, "online", 90)]
    selected, notes = compose_by_delivery_mode_counts(
        recs, [DeliveryModeCount(mode="online", count=1), DeliveryModeCount(mode="online", count=1)]
    )
    # second "online" request finds no unused candidates left
    assert len(selected) == 1
    assert len(notes) == 1
