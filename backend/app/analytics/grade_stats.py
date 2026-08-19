"""Deterministic grade-distribution statistics.

Every number here is computed from stored counts in `grade_history` rows —
never estimated, guessed, or produced by an LLM.
"""

from dataclasses import dataclass

from app.models.grade_history import GRADE_BUCKETS, GradeHistory

GPA_POINTS: dict[str, float] = {
    "a_plus": 4.0,
    "a": 4.0,
    "a_minus": 3.67,
    "b_plus": 3.33,
    "b": 3.0,
    "b_minus": 2.67,
    "c_plus": 2.33,
    "c": 2.0,
    "c_minus": 1.67,
    "d_plus": 1.33,
    "d": 1.0,
    "d_minus": 0.67,
    "f": 0.0,
}

A_RANGE = {"a_plus", "a", "a_minus"}
B_RANGE = {"b_plus", "b", "b_minus"}
C_RANGE = {"c_plus", "c", "c_minus"}
D_OR_F_RANGE = {"d_plus", "d", "d_minus", "f"}


@dataclass
class GradeDistributionStats:
    total_students: int
    total_withdrawals: int
    num_terms: int
    mean_gpa: float | None
    a_range_pct: float | None
    b_range_pct: float | None
    c_range_pct: float | None
    d_or_f_range_pct: float | None
    withdrawal_pct: float | None
    bucket_counts: dict[str, int]


def compute_grade_distribution(records: list[GradeHistory]) -> GradeDistributionStats:
    bucket_counts = {bucket: 0 for bucket in GRADE_BUCKETS}
    total_withdrawals = 0
    term_ids: set = set()

    for record in records:
        term_ids.add(record.term_id)
        total_withdrawals += record.withdrawals
        for bucket in GRADE_BUCKETS:
            bucket_counts[bucket] += getattr(record, bucket)

    total_students = sum(bucket_counts.values())

    if total_students == 0:
        return GradeDistributionStats(
            total_students=0,
            total_withdrawals=total_withdrawals,
            num_terms=len(term_ids),
            mean_gpa=None,
            a_range_pct=None,
            b_range_pct=None,
            c_range_pct=None,
            d_or_f_range_pct=None,
            withdrawal_pct=None,
            bucket_counts=bucket_counts,
        )

    grade_points_sum = sum(bucket_counts[b] * GPA_POINTS[b] for b in GRADE_BUCKETS)
    mean_gpa = grade_points_sum / total_students

    def pct(bucket_set: set[str]) -> float:
        return round(100 * sum(bucket_counts[b] for b in bucket_set) / total_students, 1)

    total_enrolled_incl_withdrawals = total_students + total_withdrawals
    withdrawal_pct = (
        round(100 * total_withdrawals / total_enrolled_incl_withdrawals, 1)
        if total_enrolled_incl_withdrawals > 0
        else None
    )

    return GradeDistributionStats(
        total_students=total_students,
        total_withdrawals=total_withdrawals,
        num_terms=len(term_ids),
        mean_gpa=round(mean_gpa, 2),
        a_range_pct=pct(A_RANGE),
        b_range_pct=pct(B_RANGE),
        c_range_pct=pct(C_RANGE),
        d_or_f_range_pct=pct(D_OR_F_RANGE),
        withdrawal_pct=withdrawal_pct,
        bucket_counts=bucket_counts,
    )
