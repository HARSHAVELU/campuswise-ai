import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.degree import CoursePrerequisite, DegreeProgram, StudentCompletedCourse


class DegreeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_program(self, degree_program_id: uuid.UUID) -> DegreeProgram | None:
        return self.db.get(DegreeProgram, degree_program_id)

    def list_programs(self, university_id: uuid.UUID | None = None) -> list[DegreeProgram]:
        stmt = select(DegreeProgram)
        if university_id is not None:
            stmt = stmt.where(DegreeProgram.university_id == university_id)
        return list(self.db.scalars(stmt).unique())

    def prerequisites_for(self, course_id: uuid.UUID) -> list[CoursePrerequisite]:
        stmt = select(CoursePrerequisite).where(CoursePrerequisite.course_id == course_id)
        return list(self.db.scalars(stmt).unique())

    def courses_unlocked_by(self, course_id: uuid.UUID) -> list[CoursePrerequisite]:
        """Prerequisite rows where `course_id` is itself a prerequisite for something else."""
        stmt = select(CoursePrerequisite).where(CoursePrerequisite.prerequisite_course_id == course_id)
        return list(self.db.scalars(stmt).unique())

    def completed_courses(self, user_id: uuid.UUID) -> list[StudentCompletedCourse]:
        stmt = select(StudentCompletedCourse).where(StudentCompletedCourse.user_id == user_id)
        return list(self.db.scalars(stmt).unique())

    def add_completed_course(
        self, user_id: uuid.UUID, course_id: uuid.UUID, term_completed: str | None, grade: str | None
    ) -> StudentCompletedCourse:
        record = StudentCompletedCourse(
            id=uuid.uuid4(),
            user_id=user_id,
            course_id=course_id,
            term_completed=term_completed,
            grade=grade,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record
