import uuid
from datetime import time

from pydantic import BaseModel, ConfigDict

from app.schemas.course import CourseSummary
from app.schemas.professor import ProfessorSummary
from app.schemas.university import TermRead


class SectionMeetingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    day_of_week: str
    start_time: time
    end_time: time
    room_id: uuid.UUID | None = None


class SectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    section_number: str
    delivery_mode: str
    seats_total: int
    seats_available: int
    course: CourseSummary
    term: TermRead
    professor: ProfessorSummary | None = None
    meetings: list[SectionMeetingRead] = []
