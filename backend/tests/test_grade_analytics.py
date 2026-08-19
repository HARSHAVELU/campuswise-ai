import uuid

from app.analytics.grade_stats import compute_grade_distribution
from app.models.grade_history import GradeHistory


def _record(**overrides) -> GradeHistory:
    defaults = dict(
        id=uuid.uuid4(),
        course_id=uuid.uuid4(),
        professor_id=uuid.uuid4(),
        term_id=uuid.uuid4(),
        a_plus=0, a=0, a_minus=0,
        b_plus=0, b=0, b_minus=0,
        c_plus=0, c=0, c_minus=0,
        d_plus=0, d=0, d_minus=0,
        f=0, withdrawals=0,
    )
    defaults.update(overrides)
    return GradeHistory(**defaults)


def test_empty_distribution_returns_none_stats():
    stats = compute_grade_distribution([])
    assert stats.total_students == 0
    assert stats.mean_gpa is None
    assert stats.a_range_pct is None


def test_all_a_plus_yields_gpa_four():
    record = _record(term_id=uuid.uuid4(), a_plus=10)
    stats = compute_grade_distribution([record])
    assert stats.total_students == 10
    assert stats.mean_gpa == 4.0
    assert stats.a_range_pct == 100.0
    assert stats.b_range_pct == 0.0


def test_mixed_distribution_percentages_sum_correctly():
    record = _record(a=20, b=20, c=20, f=20, withdrawals=10)
    stats = compute_grade_distribution([record])
    assert stats.total_students == 80
    assert stats.a_range_pct == 25.0
    assert stats.b_range_pct == 25.0
    assert stats.c_range_pct == 25.0
    assert stats.d_or_f_range_pct == 25.0
    # withdrawal % is computed against total enrolled including withdrawals
    assert stats.withdrawal_pct == round(100 * 10 / 90, 1)


def test_num_terms_counts_distinct_terms():
    term_a = uuid.uuid4()
    term_b = uuid.uuid4()
    records = [_record(term_id=term_a, a=5), _record(term_id=term_a, a=5), _record(term_id=term_b, a=5)]
    stats = compute_grade_distribution(records)
    assert stats.num_terms == 2
    assert stats.total_students == 15
