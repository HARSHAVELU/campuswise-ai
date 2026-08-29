from pydantic import BaseModel, Field

from app.schemas.course import CourseSummary
from app.schemas.professor import ProfessorRead

DELIVERY_MODES = ("in_person", "online", "hybrid")
DAYS_OF_WEEK = (
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
)


class DeliveryModeCount(BaseModel):
    """A composition requirement: "N sections of this delivery mode."

    Distinct from `delivery_modes` (a per-item filter -- "each section must
    be one of these modes"): this is a per-*result-set* requirement -- "the
    results should include at least N of this mode." E.g. "2 online and 2
    in-person courses" parses to two of these, not just a wider filter.
    """

    mode: str
    count: int = Field(ge=1)


class HardConstraints(BaseModel):
    """Requirements that cannot be violated when filtering candidates.

    Populated by the RequirementParserAgent; actually *applying* these as a
    filter over sections happens in the Recommendation Engine (Phase 5).
    """

    delivery_modes: list[str] | None = Field(
        default=None, description="Delivery modes the student will accept, e.g. ['online', 'hybrid']."
    )
    delivery_mode_counts: list[DeliveryModeCount] | None = Field(
        default=None,
        description=(
            "How many results of each delivery mode the student wants, e.g. "
            "[{mode: online, count: 2}, {mode: in_person, count: 2}] for "
            "'2 online and 2 in-person courses'."
        ),
    )
    earliest_start_time: str | None = Field(
        default=None, description="No section may start before this time, 24h 'HH:MM'."
    )
    latest_start_time: str | None = Field(
        default=None, description="No section may start after this time, 24h 'HH:MM'."
    )
    exclude_days: list[str] | None = Field(
        default=None, description="Days of the week the student cannot attend, e.g. ['friday']."
    )
    minimum_professor_rating: float | None = Field(
        default=None, description="Minimum acceptable overall professor rating, 0-5."
    )
    level: str | None = Field(
        default=None, description="'undergraduate' or 'graduate', if the student specified one."
    )


class SoftPreferences(BaseModel):
    """Preferences used for ranking, not filtering — never disqualify a candidate."""

    prefer_delivery_modes: list[str] | None = Field(
        default=None, description="Delivery modes preferred but not required, in priority order."
    )
    prefer_higher_rated_professor: bool = False
    prefer_easier_grading: bool = False
    prefer_online_exams: bool = False
    prefer_fewer_campus_days: bool = False


class ParsedRequirement(BaseModel):
    raw_query: str
    topic: str | None = Field(default=None, description="The subject/skill/course topic being searched for.")
    hard_constraints: HardConstraints = Field(default_factory=HardConstraints)
    soft_preferences: SoftPreferences = Field(default_factory=SoftPreferences)
    unsupported_notes: list[str] = Field(
        default_factory=list,
        description="Requirements the student mentioned that the platform cannot yet verify with data.",
    )
    parser_source: str = Field(
        default="rule_based", description="'llm' or 'rule_based' — which parser produced this."
    )


class AISearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)


class AISearchResponse(BaseModel):
    parsed: ParsedRequirement
    courses: list[CourseSummary]
    professors: list[ProfessorRead]
    notes: list[str] = Field(
        default_factory=list,
        description="Guidance for the student, e.g. which requirements couldn't be applied yet.",
    )
