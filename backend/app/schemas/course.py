import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.university import DepartmentRead


class CourseTopicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    topic: str


class CourseSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    title: str
    credit_hours: int
    level: str
    department: DepartmentRead
    topics: list[CourseTopicRead] = []


class CourseRead(CourseSummary):
    description: str | None = None
