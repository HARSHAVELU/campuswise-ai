import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.assessment_repository import AssessmentRepository
from app.schemas.assessment import AssessmentMetadataRead

router = APIRouter(prefix="/assessment", tags=["assessment"])


@router.get("/course/{course_id}", response_model=list[AssessmentMetadataRead])
def get_course_assessment(
    course_id: uuid.UUID, db: Session = Depends(get_db)
) -> list[AssessmentMetadataRead]:
    repo = AssessmentRepository(db)
    return [AssessmentMetadataRead.from_model(m) for m in repo.find_for_course(course_id)]


@router.get("/professor/{professor_id}", response_model=list[AssessmentMetadataRead])
def get_professor_assessment(
    professor_id: uuid.UUID, db: Session = Depends(get_db)
) -> list[AssessmentMetadataRead]:
    repo = AssessmentRepository(db)
    return [AssessmentMetadataRead.from_model(m) for m in repo.find_for_professor(professor_id)]
