import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.term import Term
from app.schemas.university import TermRead

router = APIRouter(prefix="/terms", tags=["terms"])


@router.get("", response_model=list[TermRead])
def list_terms(
    university_id: uuid.UUID | None = None, db: Session = Depends(get_db)
) -> list[TermRead]:
    stmt = select(Term).order_by(Term.year, Term.season)
    if university_id is not None:
        stmt = stmt.where(Term.university_id == university_id)
    return list(db.scalars(stmt))
