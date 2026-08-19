from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents.orchestrator import run_ai_search
from app.api.deps import get_db
from app.schemas.ai_search import AISearchRequest, AISearchResponse

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/search", response_model=AISearchResponse)
def ai_search(request: AISearchRequest, db: Session = Depends(get_db)) -> AISearchResponse:
    return run_ai_search(db, request.query)
