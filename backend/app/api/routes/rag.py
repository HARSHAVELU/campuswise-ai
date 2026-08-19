from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents.syllabus_qa import run_syllabus_qa
from app.api.deps import get_db
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/query", response_model=RAGQueryResponse)
def rag_query(request: RAGQueryRequest, db: Session = Depends(get_db)) -> RAGQueryResponse:
    return run_syllabus_qa(
        db, request.query, course_id=request.course_id, professor_id=request.professor_id
    )
