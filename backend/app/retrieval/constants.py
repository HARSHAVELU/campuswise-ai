"""Shared retrieval constants.

EMBEDDING_DIM must match whatever embedding provider is actually in use
(app.retrieval.embeddings). It defaults to 512 to match Voyage AI's
voyage-3-lite model. If VOYAGE_EMBEDDING_MODEL is changed to a model with a
different output dimension, the `embedding` column (app.models.syllabus)
must be migrated to match -- this is a known coupling, not auto-detected.
"""

EMBEDDING_DIM = 512
