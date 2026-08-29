from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.agents.chat_pipeline import run_chat
from app.api.deps import get_db
from app.core.rate_limit import CHAT_LIMIT, limiter
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=ChatResponse)
@limiter.limit(CHAT_LIMIT)
def chat(request: Request, chat_request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    return run_chat(db, chat_request.message, chat_request.history)
