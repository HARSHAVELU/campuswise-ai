import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.section_repository import SectionRepository
from app.schemas.section import SectionRead

router = APIRouter(prefix="/sections", tags=["sections"])


@router.get("", response_model=list[SectionRead])
def list_sections(
    course_id: uuid.UUID | None = None,
    term_id: uuid.UUID | None = None,
    professor_id: uuid.UUID | None = None,
    delivery_mode: str | None = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[SectionRead]:
    repo = SectionRepository(db)
    return repo.list_sections(
        course_id=course_id,
        term_id=term_id,
        professor_id=professor_id,
        delivery_mode=delivery_mode,
        limit=limit,
        offset=offset,
    )
