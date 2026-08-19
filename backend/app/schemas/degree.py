import uuid

from pydantic import BaseModel, ConfigDict


class CourseRefRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    title: str


class DegreeRequirementGroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    required_count: int
    eligible_courses: list[CourseRefRead]

    @classmethod
    def from_model(cls, group) -> "DegreeRequirementGroupRead":
        return cls(
            id=group.id,
            name=group.name,
            required_count=group.required_count,
            eligible_courses=[CourseRefRead.model_validate(erc.course) for erc in group.eligible_courses],
        )


class DegreeProgramRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    catalog_year: int
    requirement_groups: list[DegreeRequirementGroupRead]

    @classmethod
    def from_model(cls, program) -> "DegreeProgramRead":
        return cls(
            id=program.id,
            name=program.name,
            catalog_year=program.catalog_year,
            requirement_groups=[
                DegreeRequirementGroupRead.from_model(g) for g in program.requirement_groups
            ],
        )


class RequirementGroupProgressRead(BaseModel):
    name: str
    required_count: int
    completed_count: int
    complete: bool
    completed_course_codes: list[str]
    remaining_course_codes: list[str]


class DegreeProgressResponse(BaseModel):
    degree_program_name: str
    overall_percent: float
    groups: list[RequirementGroupProgressRead]


class SuggestedCourseRead(BaseModel):
    course: CourseRefRead
    requirement_group: str
    eligible: bool
    missing_prerequisites: list[str]
    offered_this_term: bool


class CompletedCourseCreate(BaseModel):
    course_id: uuid.UUID
    term_completed: str | None = None
    grade: str | None = None


class CompletedCourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    course_id: uuid.UUID
    term_completed: str | None
    grade: str | None

    @classmethod
    def from_model(cls, record) -> "CompletedCourseRead":
        return cls(course_id=record.course_id, term_completed=record.term_completed, grade=record.grade)


class DegreeEnrollRequest(BaseModel):
    degree_program_id: uuid.UUID


class PrerequisiteGroupRead(BaseModel):
    options: list[CourseRefRead]  # any ONE of these satisfies this AND-group


class CoursePrerequisitesResponse(BaseModel):
    course_id: uuid.UUID
    groups: list[PrerequisiteGroupRead]  # ALL groups must be satisfied


class EligibilityResponse(BaseModel):
    course_id: uuid.UUID
    eligible: bool
    missing: list[list[str]]  # each inner list is an OR'd set of course codes
