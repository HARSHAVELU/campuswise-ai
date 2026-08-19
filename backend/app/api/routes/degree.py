import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.term import Term
from app.models.user import User
from app.repositories.degree_repository import DegreeRepository
from app.schemas.degree import (
    CompletedCourseCreate,
    CompletedCourseRead,
    CourseRefRead,
    DegreeEnrollRequest,
    DegreeProgramRead,
    DegreeProgressResponse,
    RequirementGroupProgressRead,
    SuggestedCourseRead,
)
from app.services.degree_service import calculate_progress, suggest_next_courses

degrees_router = APIRouter(prefix="/degrees", tags=["degree"])
degree_router = APIRouter(prefix="/degree", tags=["degree"])


@degrees_router.get("", response_model=list[DegreeProgramRead])
def list_degrees(
    university_id: uuid.UUID | None = None, db: Session = Depends(get_db)
) -> list[DegreeProgramRead]:
    repo = DegreeRepository(db)
    return [DegreeProgramRead.from_model(p) for p in repo.list_programs(university_id)]


@degrees_router.get("/{degree_id}", response_model=DegreeProgramRead)
def get_degree(degree_id: uuid.UUID, db: Session = Depends(get_db)) -> DegreeProgramRead:
    repo = DegreeRepository(db)
    program = repo.get_program(degree_id)
    if program is None:
        raise HTTPException(status_code=404, detail="Degree program not found")
    return DegreeProgramRead.from_model(program)


@degree_router.post("/enroll", status_code=204)
def enroll_in_degree(
    request: DegreeEnrollRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    repo = DegreeRepository(db)
    if repo.get_program(request.degree_program_id) is None:
        raise HTTPException(status_code=404, detail="Degree program not found")
    current_user.degree_program_id = request.degree_program_id
    db.commit()


@degree_router.get("/completed-courses", response_model=list[CompletedCourseRead])
def list_completed_courses(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[CompletedCourseRead]:
    repo = DegreeRepository(db)
    return [CompletedCourseRead.from_model(c) for c in repo.completed_courses(current_user.id)]


@degree_router.post("/completed-courses", response_model=CompletedCourseRead, status_code=201)
def add_completed_course(
    request: CompletedCourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CompletedCourseRead:
    repo = DegreeRepository(db)
    if any(c.course_id == request.course_id for c in repo.completed_courses(current_user.id)):
        raise HTTPException(status_code=409, detail="This course is already marked completed")
    record = repo.add_completed_course(
        user_id=current_user.id,
        course_id=request.course_id,
        term_completed=request.term_completed,
        grade=request.grade,
    )
    return CompletedCourseRead.from_model(record)


@degree_router.get("/progress", response_model=DegreeProgressResponse)
def get_progress(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> DegreeProgressResponse:
    if current_user.degree_program_id is None:
        raise HTTPException(status_code=400, detail="You are not enrolled in a degree program yet")

    repo = DegreeRepository(db)
    program = repo.get_program(current_user.degree_program_id)
    if program is None:
        raise HTTPException(status_code=404, detail="Degree program not found")

    completed_ids = {c.course_id for c in repo.completed_courses(current_user.id)}
    result = calculate_progress(program, completed_ids)
    return DegreeProgressResponse(
        degree_program_name=result.degree_program_name,
        overall_percent=result.overall_percent,
        groups=[RequirementGroupProgressRead(**vars(g)) for g in result.groups],
    )


@degree_router.get("/next-courses", response_model=list[SuggestedCourseRead])
def get_next_courses(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[SuggestedCourseRead]:
    if current_user.degree_program_id is None:
        raise HTTPException(status_code=400, detail="You are not enrolled in a degree program yet")

    repo = DegreeRepository(db)
    program = repo.get_program(current_user.degree_program_id)
    if program is None:
        raise HTTPException(status_code=404, detail="Degree program not found")

    active_term = db.scalars(
        select(Term).where(
            Term.university_id == program.university_id, Term.is_active_for_planning.is_(True)
        )
    ).first()

    completed_ids = {c.course_id for c in repo.completed_courses(current_user.id)}
    suggestions = suggest_next_courses(
        db, program, completed_ids, active_term.id if active_term else None
    )
    return [
        SuggestedCourseRead(
            course=CourseRefRead.model_validate(s.course),
            requirement_group=s.requirement_group,
            eligible=s.eligible,
            missing_prerequisites=s.missing_prerequisites,
            offered_this_term=s.offered_this_term,
        )
        for s in suggestions
    ]
