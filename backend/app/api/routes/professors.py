import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.cache import cached
from app.schemas.grade import GradeDistributionResponse
from app.schemas.professor import ProfessorRead
from app.services.professor_service import ProfessorService

router = APIRouter(prefix="/professors", tags=["professors"])


@router.get("", response_model=list[ProfessorRead])
def list_professors(
    university_id: uuid.UUID | None = None,
    min_rating: float | None = Query(default=None, ge=0, le=5),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[ProfessorRead]:
    service = ProfessorService(db)
    return service.list_professors(
        university_id=university_id, min_rating=min_rating, limit=limit, offset=offset
    )


@router.get("/search", response_model=list[ProfessorRead])
def search_professors(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=20, le=50),
    db: Session = Depends(get_db),
) -> list[ProfessorRead]:
    service = ProfessorService(db)
    return service.search_by_name(query=q, limit=limit)


@router.get("/{professor_id}", response_model=ProfessorRead)
def get_professor(professor_id: uuid.UUID, db: Session = Depends(get_db)) -> ProfessorRead:
    service = ProfessorService(db)
    professor = service.get(professor_id)
    if professor is None:
        raise HTTPException(status_code=404, detail="Professor not found")
    return professor


@cached("professor_grades", ttl_seconds=60)
def _cached_professor_grades(db: Session, professor_id: uuid.UUID, course_id: uuid.UUID | None) -> dict:
    service = ProfessorService(db)
    stats = service.grade_distribution(professor_id=professor_id, course_id=course_id)
    return GradeDistributionResponse(**stats.__dict__).model_dump(mode="json")


@router.get("/{professor_id}/grades", response_model=GradeDistributionResponse)
def get_professor_grades(
    professor_id: uuid.UUID,
    course_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
) -> dict:
    service = ProfessorService(db)
    if service.get(professor_id) is None:
        raise HTTPException(status_code=404, detail="Professor not found")
    return _cached_professor_grades(db, professor_id, course_id)
