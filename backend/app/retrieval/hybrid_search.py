"""Hybrid retrieval: dense (embedding) search + lexical search, combined by
Reciprocal Rank Fusion, then reranked.

Runs in application code over an already-fetched candidate set (scoped by
course/professor via SyllabusRepository) rather than a database-native
vector index query -- appropriate at this dataset's scale (a handful of
syllabi), and it keeps one code path working identically on Postgres and
the SQLite test database. A production deployment at real scale would push
the dense step down to a pgvector `ORDER BY embedding <=> query` query
instead; see app.database.types.EmbeddingVector.

The lexical step is a simple term-overlap score, not a true BM25
implementation -- a placeholder for Postgres full-text search or a proper
search engine at scale (see docs/architecture-proposal.md, "Hybrid Retrieval").
"""

import logging
import math
import re
from dataclasses import dataclass

import voyageai

from app.core.config import get_settings
from app.models.syllabus import SyllabusChunk
from app.retrieval.embeddings import embed_text

logger = logging.getLogger(__name__)

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")

RRF_K = 60


@dataclass
class RetrievedChunk:
    chunk: SyllabusChunk
    score: float


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _dense_rank(chunks: list[SyllabusChunk], query_embedding: list[float]) -> list[SyllabusChunk]:
    scored = [(chunk, _cosine_similarity(chunk.embedding, query_embedding)) for chunk in chunks]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return [chunk for chunk, _ in scored]


def _lexical_rank(chunks: list[SyllabusChunk], query: str) -> list[SyllabusChunk]:
    query_tokens = _TOKEN_PATTERN.findall(query.lower())
    if not query_tokens:
        return list(chunks)

    def score(chunk: SyllabusChunk) -> float:
        content_tokens = _TOKEN_PATTERN.findall(chunk.content.lower())
        if not content_tokens:
            return 0.0
        matches = sum(content_tokens.count(token) for token in query_tokens)
        return matches / math.sqrt(len(content_tokens))

    scored = [(chunk, score(chunk)) for chunk in chunks]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return [chunk for chunk, _ in scored]


def _reciprocal_rank_fusion(
    ranked_lists: list[list[SyllabusChunk]], k: int = RRF_K
) -> list[RetrievedChunk]:
    scores: dict = {}
    chunk_by_id = {}
    for ranked in ranked_lists:
        for rank, chunk in enumerate(ranked):
            chunk_by_id[chunk.id] = chunk
            scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (k + rank + 1)

    fused = sorted(scores.items(), key=lambda pair: pair[1], reverse=True)
    return [RetrievedChunk(chunk=chunk_by_id[chunk_id], score=score) for chunk_id, score in fused]


def _rerank_with_voyage(query: str, candidates: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
    settings = get_settings()
    if not settings.voyage_api_key or not candidates:
        return candidates[:top_k]

    try:
        client = voyageai.Client(api_key=settings.voyage_api_key)
        documents = [c.chunk.content for c in candidates]
        result = client.rerank(query, documents, model=settings.voyage_rerank_model, top_k=top_k)
        return [
            RetrievedChunk(chunk=candidates[item.index].chunk, score=item.relevance_score)
            for item in result.results
        ]
    except Exception as exc:  # noqa: BLE001 -- reranking is an enhancement, never block retrieval
        logger.warning("Voyage rerank call failed, using RRF order: %s", exc)
        return candidates[:top_k]


def _rerank_heuristic(query: str, candidates: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
    """Fallback reranker: boosts chunks containing the query as a near-exact phrase."""
    lowered_query = query.lower().strip("?.! ")
    boosted = []
    for candidate in candidates:
        bonus = 0.05 if lowered_query and lowered_query in candidate.chunk.content.lower() else 0.0
        boosted.append(RetrievedChunk(chunk=candidate.chunk, score=candidate.score + bonus))
    boosted.sort(key=lambda c: c.score, reverse=True)
    return boosted[:top_k]


def hybrid_search(
    query: str, chunks: list[SyllabusChunk], top_k: int = 5
) -> list[RetrievedChunk]:
    if not chunks:
        return []

    query_embedding = embed_text(query, input_type="query")
    dense_ranked = _dense_rank(chunks, query_embedding)
    lexical_ranked = _lexical_rank(chunks, query)

    fused = _reciprocal_rank_fusion([dense_ranked, lexical_ranked])
    candidate_pool = fused[: max(top_k * 4, 10)]

    settings = get_settings()
    if settings.voyage_api_key:
        return _rerank_with_voyage(query, candidate_pool, top_k)
    return _rerank_heuristic(query, candidate_pool, top_k)
