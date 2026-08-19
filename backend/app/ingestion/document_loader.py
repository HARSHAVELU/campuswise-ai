"""Loads raw text out of a source document, independent of the ingestion pipeline
that chunks/embeds/stores it. Keeping parsing separate from storage means a future
source (HTML catalog page, DOCX policy doc) is a new loader function, not a
rewrite of the pipeline (see docs/architecture-proposal.md, "Data Ingestion Pipeline").
"""

from pathlib import Path

from pypdf import PdfReader


def load_text_from_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    if suffix in (".txt", ".md"):
        return path.read_text(encoding="utf-8")
    raise ValueError(f"Unsupported document type: {suffix}")
