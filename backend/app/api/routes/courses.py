import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.cache import cached
from app.models.user import User
from app.repositories.degree_repository import DegreeRepository
from app.schemas.course import CourseRead, CourseSummary
from app.schemas.degree import (
    CourseRefRead,
    CoursePrerequisitesResponse,
    EligibilityResponse,
    PrerequisiteGroupRead,
)
from app.services.course_service import CourseService
from app.services.prerequisite_engine import check_eligibility

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=list[CourseSummary])
def list_courses(
    university_id: uuid.UUID | None = None,
    department_code: str | None = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[CourseSummary]:
    service = CourseService(db)
    return service.list_courses(
        university_id=university_id, department_code=department_code, limit=limit, offset=offset
    )


@cached("course_search", ttl_seconds=60)
def _cached_course_search(db: Session, query: str, limit: int) -> list[dict]:
    service = CourseService(db)
    courses = service.search(query=query, limit=limit)
    return [CourseSummary.model_validate(c).model_dump(mode="json") for c in courses]


@router.get("/search", response_model=list[CourseSummary])
def search_courses(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=20, le=50),
    db: Session = Depends(get_db),
) -> list[dict]:
    return _cached_course_search(db, q, limit)


@router.get("/{course_id}", response_model=CourseRead)
def get_course(course_id: uuid.UUID, db: Session = Depends(get_db)) -> CourseRead:
    service = CourseService(db)
    course = service.get(course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.get("/{course_id}/prerequisites", response_model=CoursePrerequisitesResponse)
def get_course_prerequisites(
    course_id: uuid.UUID, db: Session = Depends(get_db)
) -> CoursePrerequisitesResponse:
    repo = DegreeRepository(db)
    rows = repo.prerequisites_for(course_id)

    groups: dict[int, list] = {}
    for row in rows:
        groups.setdefault(row.group_number, []).append(row)

    return CoursePrerequisitesResponse(
        course_id=course_id,
        groups=[
            PrerequisiteGroupRead(
                options=[CourseRefRead.model_validate(r.prerequisite_course) for r in group_rows]
            )
            for _, group_rows in sorted(groups.items())
        ],
    )


@router.get("/{course_id}/eligibility", response_model=EligibilityResponse)
def get_course_eligibility(
    course_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EligibilityResponse:
    repo = DegreeRepository(db)
    prereqs = repo.prerequisites_for(course_id)
    completed_ids = {c.course_id for c in repo.completed_courses(current_user.id)}
    result = check_eligibility(prereqs, completed_ids)
    return EligibilityResponse(
        course_id=course_id,
        eligible=result.eligible,
        missing=[m.options for m in result.missing],
    )
