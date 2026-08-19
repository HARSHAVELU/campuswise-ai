"""Course discovery: turns a ParsedRequirement into candidate courses and professors.

This is deliberately thin for Phase 4: it reuses the keyword/topic course
search and professor rating filter already built in Phase 2/3. Full hard
constraint filtering over sections (delivery mode, time windows, excluded
days) and ranked/explained recommendations are the Recommendation Engine's
job (Phase 5) -- this stage only narrows the field.
"""

from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.professor import Professor
from app.schemas.ai_search import ParsedRequirement
from app.services.course_service import CourseService
from app.services.professor_service import ProfessorService

MAX_COURSES = 20
MAX_PROFESSORS = 20


def discover_courses(db: Session, parsed: ParsedRequirement) -> list[Course]:
    course_service = CourseService(db)
    if parsed.topic:
        return course_service.search(query=parsed.topic, limit=MAX_COURSES)
    return course_service.list_courses(limit=MAX_COURSES)


def discover_professors(db: Session, parsed: ParsedRequirement) -> list[Professor]:
    professor_service = ProfessorService(db)
    return professor_service.list_professors(
        min_rating=parsed.hard_constraints.minimum_professor_rating,
        limit=MAX_PROFESSORS,
    )
