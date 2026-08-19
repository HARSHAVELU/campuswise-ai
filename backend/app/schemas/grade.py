from pydantic import BaseModel


class GradeDistributionResponse(BaseModel):
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
    disclaimer: str = (
        "Historical grade data does not guarantee future outcomes. "
        "Percentages are calculated from recorded past sections only."
    )
