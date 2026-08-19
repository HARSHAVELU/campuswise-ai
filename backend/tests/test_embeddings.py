from unittest.mock import patch

from app.retrieval.constants import EMBEDDING_DIM
from app.retrieval.embeddings import embed_batch, embed_text


def test_hash_embedding_is_deterministic():
    with patch("app.retrieval.embeddings.get_settings") as mock_settings:
        mock_settings.return_value.voyage_api_key = None
        a = embed_text("python machine learning")
        b = embed_text("python machine learning")
    assert a == b


def test_hash_embedding_has_expected_dimension():
    with patch("app.retrieval.embeddings.get_settings") as mock_settings:
        mock_settings.return_value.voyage_api_key = None
        vector = embed_text("some syllabus text")
    assert len(vector) == EMBEDDING_DIM


def test_similar_text_more_similar_than_unrelated_text():
    import math

    with patch("app.retrieval.embeddings.get_settings") as mock_settings:
        mock_settings.return_value.voyage_api_key = None
        a = embed_text("the exam is online and open book")
        b = embed_text("the final exam is online and open book format")
        c = embed_text("marketing strategy case study group project")

    def cosine(x, y):
        dot = sum(i * j for i, j in zip(x, y))
        return dot / (math.sqrt(sum(i * i for i in x)) * math.sqrt(sum(j * j for j in y)))

    assert cosine(a, b) > cosine(a, c)


def test_embed_batch_empty_list_returns_empty():
    with patch("app.retrieval.embeddings.get_settings") as mock_settings:
        mock_settings.return_value.voyage_api_key = None
        assert embed_batch([]) == []
