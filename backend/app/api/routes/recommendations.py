from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents.recommendation_pipeline import run_course_recommendations
from app.api.deps import get_db
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/courses", response_model=RecommendationResponse)
def recommend_courses(
    request: RecommendationRequest, db: Session = Depends(get_db)
) -> RecommendationResponse:
    return run_course_recommendations(db, request.query)
