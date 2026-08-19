import uuid

from pydantic import BaseModel


class Citation(BaseModel):
    course_code: str
    course_title: str
    professor_name: str | None = None
    term_name: str | None = None
    source_document: str
    excerpt: str
    relevance_score: float


class RAGQueryRequest(BaseModel):
    query: str
    course_id: uuid.UUID | None = None
    professor_id: uuid.UUID | None = None


class RAGQueryResponse(BaseModel):
    query: str
    answer: str
    citations: list[Citation]
    confidence: str  # "none" | "low" | "medium" | "high"
    chunks_considered: int
    answer_source: str  # "llm" | "excerpt_only"
