from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents.schedule_pipeline import generate_schedules, validate_schedule
from app.api.deps import get_db
from app.schemas.schedule import (
    ScheduleGenerateRequest,
    ScheduleGenerateResponse,
    ScheduleValidateRequest,
    ScheduleValidateResponse,
)

router = APIRouter(prefix="/schedule", tags=["schedule"])


@router.post("/generate", response_model=ScheduleGenerateResponse)
def schedule_generate(
    request: ScheduleGenerateRequest, db: Session = Depends(get_db)
) -> ScheduleGenerateResponse:
    return generate_schedules(db, request.query, request.min_credits, request.max_credits)


@router.post("/validate", response_model=ScheduleValidateResponse)
def schedule_validate(
    request: ScheduleValidateRequest, db: Session = Depends(get_db)
) -> ScheduleValidateResponse:
    return validate_schedule(db, request.section_ids)
