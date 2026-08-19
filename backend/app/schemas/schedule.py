import uuid

from pydantic import BaseModel, Field

from app.schemas.ai_search import ParsedRequirement
from app.schemas.section import SectionRead


class ScheduleResult(BaseModel):
    strategy: str
    label: str
    sections: list[SectionRead]
    total_credits: int
    campus_days: list[str]
    average_fit_score: float


class ScheduleGenerateRequest(BaseModel):
    query: str
    min_credits: int = Field(default=12, ge=1, le=30)
    max_credits: int = Field(default=18, ge=1, le=30)


class ScheduleGenerateResponse(BaseModel):
    parsed: ParsedRequirement
    schedules: dict[str, ScheduleResult | None]
    notes: list[str] = []


class ScheduleValidateRequest(BaseModel):
    section_ids: list[uuid.UUID]


class ConflictWarningRead(BaseModel):
    section_a_id: str
    section_b_id: str
    conflict_type: str
    day_of_week: str
    detail: str


class ScheduleValidateResponse(BaseModel):
    conflicts: list[ConflictWarningRead]
    is_valid: bool
