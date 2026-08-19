import uuid
from unittest.mock import patch

from app.models.syllabus import Syllabus, SyllabusChunk
from app.retrieval.hybrid_search import hybrid_search


def _make_chunk(content: str) -> SyllabusChunk:
    syllabus = Syllabus(
        id=uuid.uuid4(),
        university_id=uuid.uuid4(),
        course_id=uuid.uuid4(),
        title="Test Syllabus",
        source_document="doc.pdf",
        raw_text=content,
    )
    chunk = SyllabusChunk(
        id=uuid.uuid4(), syllabus_id=syllabus.id, chunk_index=0, content=content, embedding=[]
    )
    chunk.syllabus = syllabus
    return chunk


def test_hybrid_search_ranks_lexically_relevant_chunk_first():
    exam_chunk = _make_chunk("The final exam is administered online through the course portal.")
    unrelated_chunk = _make_chunk("Group projects are due in the last week of the semester.")

    with patch("app.retrieval.hybrid_search.get_settings") as mock_settings:
        mock_settings.return_value.voyage_api_key = None
        results = hybrid_search("Is the exam online?", [exam_chunk, unrelated_chunk], top_k=2)

    assert results[0].chunk is exam_chunk


def test_hybrid_search_empty_chunks_returns_empty():
    with patch("app.retrieval.hybrid_search.get_settings") as mock_settings:
        mock_settings.return_value.voyage_api_key = None
        assert hybrid_search("anything", [], top_k=5) == []
