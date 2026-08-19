import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.university import DepartmentRead


class ProfessorRatingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    overall_rating: float
    teaching_rating: float | None = None
    difficulty_rating: float | None = None
    would_take_again_pct: float | None = None
    num_ratings: int
    source_type: str
    confidence: float


class ProfessorSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    title: str | None = None


class ProfessorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    title: str | None = None
    email: str | None = None
    department: DepartmentRead | None = None
    rating: ProfessorRatingRead | None = None
