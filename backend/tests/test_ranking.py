import datetime
import uuid

from app.models import (
    Course,
    Department,
    GradeHistory,
    Professor,
    ProfessorRating,
    Section,
    SectionMeeting,
    Term,
    University,
)
from app.ingestion.syllabus_ingestion import ingest_syllabus
from app.models.course import CourseLevel
from app.models.section import DayOfWeek, DeliveryMode
from app.models.term import Season
from app.ranking.engine import rank_sections
from app.ranking.hard_filter import apply_hard_constraints
from app.schemas.ai_search import HardConstraints, ParsedRequirement, SoftPreferences


def _build_scenario(db_session, delivery_mode=DeliveryMode.ONLINE, rating=4.5, difficulty=2.0, mean_gpa_bucket="a"):
    university = University(id=uuid.uuid4(), name="Test University", short_name=f"TU-{uuid.uuid4().hex[:6]}")
    db_session.add(university)
    db_session.flush()

    department = Department(id=uuid.uuid4(), university_id=university.id, code="CS", name="Computer Science")
    db_session.add(department)
    db_session.flush()

    course = Course(
        id=uuid.uuid4(),
        university_id=university.id,
        department_id=department.id,
        code="CS 4375",
        title="Introduction to Machine Learning",
        credit_hours=3,
        level=CourseLevel.UNDERGRADUATE,
    )
    db_session.add(course)
    db_session.flush()

    professor = Professor(id=uuid.uuid4(), university_id=university.id, department_id=department.id, name="Dr. Test")
    db_session.add(professor)
    db_session.flush()
    db_session.add(
        ProfessorRating(
            id=uuid.uuid4(),
            professor_id=professor.id,
            overall_rating=rating,
            difficulty_rating=difficulty,
            num_ratings=50,
            source_type="student_reported",
            confidence=0.8,
        )
    )

    term = Term(
        id=uuid.uuid4(), university_id=university.id, name="Fall 2026", year=2026, season=Season.FALL,
        is_active_for_planning=True,
    )
    db_session.add(term)
    db_session.flush()

    section = Section(
        id=uuid.uuid4(),
        course_id=course.id,
        term_id=term.id,
        professor_id=professor.id,
        section_number="001",
        delivery_mode=delivery_mode,
        seats_total=30,
        seats_available=10,
    )
    db_session.add(section)
    db_session.flush()

    if delivery_mode != DeliveryMode.ONLINE:
        db_session.add(
            SectionMeeting(
                id=uuid.uuid4(),
                section_id=section.id,
                day_of_week=DayOfWeek.TUESDAY,
                start_time=datetime.time(11, 0),
                end_time=datetime.time(12, 15),
            )
        )

    grade_kwargs = {b: 0 for b in [
        "a_plus", "a", "a_minus", "b_plus", "b", "b_minus",
        "c_plus", "c", "c_minus", "d_plus", "d", "d_minus", "f",
    ]}
    grade_kwargs[mean_gpa_bucket] = 30
    db_session.add(
        GradeHistory(
            id=uuid.uuid4(), course_id=course.id, professor_id=professor.id, term_id=term.id,
            withdrawals=0, source_type="historical", **grade_kwargs,
        )
    )
    db_session.commit()
    db_session.refresh(section)
    return section


def _empty_hard_constraints() -> HardConstraints:
    return HardConstraints()


def test_hard_filter_excludes_by_minimum_rating(db_session):
    section = _build_scenario(db_session, rating=3.0)
    hard = HardConstraints(minimum_professor_rating=4.0)
    result = apply_hard_constraints([section], hard)
    assert result.passed == []
    assert result.excluded_reasons == {"rating_below_threshold": 1}


def test_hard_filter_excludes_missing_rating_data_conservatively(db_session):
    section = _build_scenario(db_session, rating=4.5)
    db_session.delete(section.professor.rating)
    db_session.commit()
    db_session.refresh(section.professor)
    hard = HardConstraints(minimum_professor_rating=4.0)
    result = apply_hard_constraints([section], hard)
    assert result.passed == []
    assert result.excluded_reasons == {"missing_rating_data": 1}


def test_hard_filter_excludes_by_delivery_mode(db_session):
    section = _build_scenario(db_session, delivery_mode=DeliveryMode.IN_PERSON)
    hard = HardConstraints(delivery_modes=["online"])
    result = apply_hard_constraints([section], hard)
    assert result.passed == []
    assert result.excluded_reasons == {"delivery_mode": 1}


def test_hard_filter_excludes_excluded_day(db_session):
    section = _build_scenario(db_session, delivery_mode=DeliveryMode.IN_PERSON)
    hard = HardConstraints(exclude_days=["tuesday"])
    result = apply_hard_constraints([section], hard)
    assert result.passed == []
    assert result.excluded_reasons == {"excluded_day": 1}


def test_hard_filter_passes_when_no_constraints(db_session):
    section = _build_scenario(db_session)
    result = apply_hard_constraints([section], _empty_hard_constraints())
    assert result.passed == [section]


def test_rank_sections_high_rating_and_good_grades_scores_high(db_session):
    section = _build_scenario(db_session, rating=4.8, mean_gpa_bucket="a_plus")
    parsed = ParsedRequirement(raw_query="test", topic="python")
    recs, filter_result = rank_sections(db_session, parsed, [section])
    assert len(recs) == 1
    assert recs[0].fit_score >= 90
    assert any("rating" in m.lower() for m in recs[0].matched)
    assert any("gpa" in m.lower() for m in recs[0].matched)


def test_rank_sections_low_rating_scores_lower_than_high_rating(db_session):
    high = _build_scenario(db_session, rating=4.9, mean_gpa_bucket="a_plus")
    low = _build_scenario(db_session, rating=3.2, mean_gpa_bucket="c")
    parsed = ParsedRequirement(raw_query="test")
    recs, _ = rank_sections(db_session, parsed, [high, low])
    assert recs[0].section.id == high.id
    assert recs[0].fit_score >= recs[1].fit_score


def test_missing_info_always_includes_review_and_workload_gaps(db_session):
    section = _build_scenario(db_session)
    parsed = ParsedRequirement(raw_query="test")
    recs, _ = rank_sections(db_session, parsed, [section])
    missing_text = " ".join(recs[0].missing_info)
    assert "review" in missing_text.lower()
    assert "workload" in missing_text.lower()


def test_exam_preference_not_surfaced_when_not_requested(db_session):
    section = _build_scenario(db_session)
    parsed = ParsedRequirement(raw_query="test")  # no prefer_online_exams
    recs, _ = rank_sections(db_session, parsed, [section])
    all_text = " ".join(recs[0].matched + recs[0].not_matched + recs[0].missing_info)
    assert "exam format" not in all_text.lower()
    assert "exam_preference" not in recs[0].score_breakdown


def test_exam_preference_missing_when_requested_but_no_syllabus_data(db_session):
    section = _build_scenario(db_session)
    parsed = ParsedRequirement(
        raw_query="test", soft_preferences=SoftPreferences(prefer_online_exams=True)
    )
    recs, _ = rank_sections(db_session, parsed, [section])
    assert any("no exam-format information is available" in m.lower() for m in recs[0].missing_info)


def test_exam_preference_scores_online_exam_highly(db_session):
    section = _build_scenario(db_session)
    ingest_syllabus(
        db_session,
        university_id=section.course.university_id,
        course_id=section.course_id,
        professor_id=section.professor_id,
        term_id=section.term_id,
        title="Test Syllabus",
        source_document="TEST_Fall2025.pdf",
        raw_text=(
            "Exam Format: The final exam is administered online through the course portal "
            "and is open-book.\n\nLate Policy: Late work loses 10% per day."
        ),
    )
    db_session.commit()

    parsed = ParsedRequirement(
        raw_query="test", soft_preferences=SoftPreferences(prefer_online_exams=True)
    )
    recs, _ = rank_sections(db_session, parsed, [section])
    assert "exam_preference" in recs[0].score_breakdown
    assert recs[0].score_breakdown["exam_preference"] == 100.0
    assert any("final exam is online" in m.lower() for m in recs[0].matched)


def test_prefer_easier_grading_scores_low_difficulty_higher(db_session):
    easy = _build_scenario(db_session, difficulty=1.5)
    hard_course = _build_scenario(db_session, difficulty=4.5)
    parsed = ParsedRequirement(
        raw_query="test", soft_preferences=SoftPreferences(prefer_easier_grading=True)
    )
    recs, _ = rank_sections(db_session, parsed, [easy, hard_course])
    # both sections have identical rating/gpa by default scenario values, so difficulty should differentiate
    scores_by_id = {r.section.id: r.fit_score for r in recs}
    assert scores_by_id[easy.id] >= scores_by_id[hard_course.id]


def test_no_applicable_dimensions_falls_back_to_insufficient_data(db_session):
    section = _build_scenario(db_session)
    db_session.delete(section.professor.rating)
    # Remove grade history so historical_grades has no data either
    from app.models.grade_history import GradeHistory as GH

    db_session.query(GH).filter(GH.course_id == section.course_id).delete()
    db_session.commit()
    db_session.refresh(section.professor)

    parsed = ParsedRequirement(raw_query="test")
    recs, _ = rank_sections(db_session, parsed, [section])
    assert len(recs) == 1
    assert recs[0].fit_score == 50
    assert any("not enough data" in m.lower() for m in recs[0].missing_info)
