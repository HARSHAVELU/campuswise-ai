"""Text embeddings for the syllabus RAG pipeline.

Uses Voyage AI (Anthropic's recommended embeddings partner -- Claude itself
has no embeddings endpoint) when VOYAGE_API_KEY is configured. Falls back to
a deterministic feature-hashing embedding otherwise, so ingestion and
retrieval keep working offline, in CI, and in local dev without any API key
-- the same fallback pattern used by the RequirementParserAgent (Phase 4).

The fallback is NOT a trained semantic model: it is a bag-of-words hashing
trick (two texts sharing vocabulary get some cosine similarity; no real
synonym/paraphrase understanding). It exists to keep the retrieval pipeline
mechanically correct and testable, not to provide production-quality search.
"""

import hashlib
import logging
import math
import re

import voyageai

from app.core.config import get_settings
from app.core.llm_telemetry import record_fallback, track_llm_call
from app.retrieval.constants import EMBEDDING_DIM

logger = logging.getLogger(__name__)

_PURPOSE = "embedding"
_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def _hash_embedding(text: str) -> list[float]:
    vector = [0.0] * EMBEDDING_DIM
    tokens = _TOKEN_PATTERN.findall(text.lower())
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % EMBEDDING_DIM
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign

    norm = math.sqrt(sum(v * v for v in vector))
    if norm > 0:
        vector = [v / norm for v in vector]
    return vector


def _hash_embed_batch(texts: list[str]) -> list[list[float]]:
    return [_hash_embedding(text) for text in texts]


def embed_batch(texts: list[str], *, input_type: str = "document") -> list[list[float]]:
    """input_type: 'document' when embedding syllabus chunks, 'query' when embedding a search query."""
    settings = get_settings()
    if not texts:
        return []

    if settings.voyage_api_key:
        try:
            client = voyageai.Client(api_key=settings.voyage_api_key)
            with track_llm_call("voyage", _PURPOSE, settings.voyage_embedding_model) as rec:
                result = client.embed(
                    texts, model=settings.voyage_embedding_model, input_type=input_type
                )
                rec.input_tokens = getattr(result, "total_tokens", None)
            return [[float(v) for v in embedding] for embedding in result.embeddings]
        except Exception as exc:  # noqa: BLE001 -- any provider failure should degrade, not crash ingestion
            logger.warning("Voyage embedding call failed, falling back to hash embedding: %s", exc)
            record_fallback(_PURPOSE, "llm_error")
    else:
        record_fallback(_PURPOSE, "no_api_key")

    return _hash_embed_batch(texts)


def embed_text(text: str, *, input_type: str = "document") -> list[float]:
    return embed_batch([text], input_type=input_type)[0]
